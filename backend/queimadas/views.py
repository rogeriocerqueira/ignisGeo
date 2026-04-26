from datetime import date, timedelta
from django.contrib.gis.geos import Polygon
from django.db.models import Avg, Count
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from .models import FocoQueimada, AreaRisco
from .serializers import (
    FocoQueimadaGeoSerializer,
    FocoQueimadaListSerializer,
    AreaRiscoGeoSerializer,
    AreaRiscoRankingSerializer,
)
from .topsis_fuzzy import calcular_topsis_fuzzy
from .tasks import importar_csv_inpe


class FocosGeoJSONView(generics.ListAPIView):
    serializer_class = FocoQueimadaGeoSerializer
    pagination_class = None

    def get_queryset(self):
        qs = FocoQueimada.objects.all()
        bioma = self.request.query_params.get("bioma")
        if bioma:
            qs = qs.filter(bioma=bioma)
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado.upper())
        data_inicio = self.request.query_params.get("data_inicio")
        if data_inicio:
            qs = qs.filter(data_hora__date__gte=data_inicio)
        data_fim = self.request.query_params.get("data_fim")
        if data_fim:
            qs = qs.filter(data_hora__date__lte=data_fim)
        bbox = self.request.query_params.get("bbox")
        if bbox:
            try:
                coords = [float(x) for x in bbox.split(",")]
                if len(coords) == 4:
                    poligono = Polygon.from_bbox(coords)
                    qs = qs.filter(localizacao__within=poligono)
            except (ValueError, TypeError):
                pass
        return qs.order_by("-data_hora")[:5000]


class FocosListView(generics.ListAPIView):
    serializer_class = FocoQueimadaListSerializer

    def get_queryset(self):
        qs = FocoQueimada.objects.all()
        bioma = self.request.query_params.get("bioma")
        estado = self.request.query_params.get("estado")
        if bioma:
            qs = qs.filter(bioma=bioma)
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs.order_by("-frp")[:500]


class AreasRiscoGeoJSONView(generics.ListAPIView):
    serializer_class = AreaRiscoGeoSerializer
    pagination_class = None

    def get_queryset(self):
        qs = AreaRisco.objects.filter(geometria__isnull=False)
        nivel = self.request.query_params.get("nivel_risco")
        if nivel:
            qs = qs.filter(nivel_risco=nivel.upper())
        bioma = self.request.query_params.get("bioma")
        if bioma:
            qs = qs.filter(bioma=bioma)
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs.order_by("ranking")


class RankingView(generics.ListAPIView):
    serializer_class = AreaRiscoRankingSerializer

    def get_queryset(self):
        qs = AreaRisco.objects.all()
        nivel  = self.request.query_params.get("nivel_risco")
        estado = self.request.query_params.get("estado")
        bioma  = self.request.query_params.get("bioma")
        if nivel:  qs = qs.filter(nivel_risco=nivel.upper())
        if estado: qs = qs.filter(estado=estado.upper())
        if bioma:  qs = qs.filter(bioma=bioma)
        return qs.order_by("ranking")

@csrf_exempt
@api_view(["POST"])
def calcular_topsis_view(request):
    """
    POST /api/calcular-topsis/
    Recalcula o TOPSIS Fuzzy respeitando os filtros ativos.
    Body (todos opcionais): data_inicio, data_fim, estado, bioma
    """
    data_inicio_str = request.data.get("data_inicio")
    data_fim_str    = request.data.get("data_fim")
    estado_filtro   = request.data.get("estado")
    bioma_filtro    = request.data.get("bioma")

    if data_inicio_str:
        try:
            from datetime import datetime
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        data_inicio = None

    if data_fim_str:
        try:
            from datetime import datetime
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        data_fim = None

    qs = FocoQueimada.objects.all()
    if data_inicio:
        qs = qs.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data_hora__date__lte=data_fim)
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro.upper())
    if bioma_filtro:
        qs = qs.filter(bioma=bioma_filtro)

    metricas = (
        qs.values("municipio", "estado", "bioma")
        .annotate(
            total_focos=Count("id"),
            frp_media=Avg("frp"),
            risco_historico_medio=Avg("risco_historico"),
            vento_medio=Avg("vento_ms"),
            ndvi_medio=Avg("ndvi"),
        )
        .filter(total_focos__gte=1)
    )

    if not metricas:
        return Response(
            {"mensagem": "Nenhum foco encontrado com os filtros aplicados."},
            status=status.HTTP_200_OK,
        )

    alternativas = [
        {
            "nome":                  f"{m['municipio']}/{m['estado']}",
            "municipio":             m["municipio"],
            "estado":                m["estado"],
            "bioma":                 m["bioma"],
            "total_focos":           m["total_focos"] or 0,
            "frp_media":             m["frp_media"] or 0.0,
            "risco_historico_medio": m["risco_historico_medio"] or 0.0,
            "vento_medio":           m["vento_medio"] or 0.0,
            "ndvi_medio":            m["ndvi_medio"] or 0.0,
        }
        for m in metricas
    ]

    resultado = calcular_topsis_fuzzy(alternativas)

    # Usa datas reais do banco quando não informado
    if not data_inicio or not data_fim:
        primeiro = FocoQueimada.objects.order_by("data_hora").first()
        ultimo   = FocoQueimada.objects.order_by("-data_hora").first()
        data_inicio = data_inicio or (primeiro.data_hora.date() if primeiro else date.today())
        data_fim    = data_fim    or (ultimo.data_hora.date()   if ultimo   else date.today())

    # Limpa tudo e salva com bulk_create
    AreaRisco.objects.all().delete()

    novas_areas = [
        AreaRisco(
            nome=item["nome"],
            estado=item["estado"],
            bioma=item["bioma"],
            geometria=None,
            score_topsis=item["score_topsis"],
            ranking=item["ranking"],
            nivel_risco=item["nivel_risco"],
            total_focos=item["total_focos"],
            frp_media=item["frp_media"],
            risco_historico_medio=item["risco_historico_medio"],
            vento_medio=item["vento_medio"],
            ndvi_medio=item["ndvi_medio"],
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
        )
        for item in resultado
    ]

    AreaRisco.objects.bulk_create(novas_areas)
    areas_criadas = len(novas_areas)

    return Response({
        "mensagem":          f"TOPSIS Fuzzy calculado para {len(resultado)} áreas.",
        "periodo":           {"inicio": str(data_inicio), "fim": str(data_fim)},
        "filtros":           {"estado": estado_filtro or "Todos", "bioma": bioma_filtro or "Todos"},
        "areas_atualizadas": areas_criadas,
        "top_5": [
            {
                "nome":         r["nome"],
                "score_topsis": r["score_topsis"],
                "nivel_risco":  r["nivel_risco"],
                "ranking":      r["ranking"],
            }
            for r in resultado[:5]
        ],
    })


@csrf_exempt
@api_view(["POST"])
def importar_csv_view(request):
    caminho = request.data.get("caminho", "/app/data/focos_mensal.csv")
    task = importar_csv_inpe.delay(caminho)
    return Response({
        "mensagem": "Importação iniciada.",
        "task_id":  task.id,
        "caminho":  caminho,
    })


@api_view(["GET"])
def estatisticas_view(request):
    qs = FocoQueimada.objects.all()
    bioma       = request.query_params.get("bioma")
    estado      = request.query_params.get("estado")
    data_inicio = request.query_params.get("data_inicio")
    data_fim    = request.query_params.get("data_fim")
    if bioma:       qs = qs.filter(bioma=bioma)
    if estado:      qs = qs.filter(estado=estado.upper())
    if data_inicio: qs = qs.filter(data_hora__date__gte=data_inicio)
    if data_fim:    qs = qs.filter(data_hora__date__lte=data_fim)

    total_focos = qs.count()                          # ← usa qs filtrado
    por_bioma = (
        qs                                            # ← usa qs filtrado
        .values("bioma")
        .annotate(total=Count("id"), frp_media=Avg("frp"))
        .order_by("-total")
    )
    areas_criticas = AreaRisco.objects.filter(nivel_risco="CRITICO").count()
    areas_alto     = AreaRisco.objects.filter(nivel_risco="ALTO").count()

    return Response({
        "total_focos":      total_focos,
        "areas_criticas":   areas_criticas,
        "areas_alto_risco": areas_alto,
        "por_bioma":        list(por_bioma),
    })
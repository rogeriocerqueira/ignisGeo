from datetime import date
from django.contrib.gis.geos import Polygon
from django.db.models import Avg, Count, Min, Max
from django.db.models.functions import TruncMonth
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
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


class RankingPagination(PageNumberPagination):
    page_size             = 10
    page_size_query_param = "page_size"
    max_page_size         = 100


class FocosGeoJSONView(generics.ListAPIView):
    serializer_class = FocoQueimadaGeoSerializer
    pagination_class = None

    def get_queryset(self):
        qs          = FocoQueimada.objects.all()
        bioma       = self.request.query_params.get("bioma")
        estado      = self.request.query_params.get("estado")
        data_inicio = self.request.query_params.get("data_inicio")
        data_fim    = self.request.query_params.get("data_fim")
        bbox        = self.request.query_params.get("bbox")
        if bioma:       qs = qs.filter(bioma=bioma)
        if estado:      qs = qs.filter(estado=estado.upper())
        if data_inicio: qs = qs.filter(data_hora__date__gte=data_inicio)
        if data_fim:    qs = qs.filter(data_hora__date__lte=data_fim)
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
        qs     = FocoQueimada.objects.all()
        bioma  = self.request.query_params.get("bioma")
        estado = self.request.query_params.get("estado")
        if bioma:  qs = qs.filter(bioma=bioma)
        if estado: qs = qs.filter(estado=estado.upper())
        return qs.order_by("-frp")[:500]


class AreasRiscoGeoJSONView(generics.ListAPIView):
    serializer_class = AreaRiscoGeoSerializer
    pagination_class = None

    def get_queryset(self):
        qs     = AreaRisco.objects.filter(geometria__isnull=False)
        nivel  = self.request.query_params.get("nivel_risco")
        bioma  = self.request.query_params.get("bioma")
        estado = self.request.query_params.get("estado")
        if nivel:  qs = qs.filter(nivel_risco=nivel.upper())
        if bioma:  qs = qs.filter(bioma=bioma)
        if estado: qs = qs.filter(estado=estado.upper())
        return qs.order_by("ranking")


class RankingView(generics.ListAPIView):
    serializer_class = AreaRiscoRankingSerializer
    pagination_class = RankingPagination

    def get_queryset(self):
        qs     = AreaRisco.objects.all()
        nivel  = self.request.query_params.get("nivel_risco")
        estado = self.request.query_params.get("estado")
        bioma  = self.request.query_params.get("bioma")
        if nivel:  qs = qs.filter(nivel_risco=nivel.upper())
        if estado: qs = qs.filter(estado=estado.upper())
        if bioma:  qs = qs.filter(bioma=bioma)
        return qs.order_by("ranking")


# ── NOVO: Série temporal mensal ────────────────────────────────
@api_view(["GET"])
def serie_temporal_view(request):
    """
    GET /api/serie-temporal/
    Retorna focos agrupados por mês.
    Filtros opcionais: estado, bioma, data_inicio, data_fim
    """
    qs = FocoQueimada.objects.all()
    bioma       = request.query_params.get("bioma")
    estado      = request.query_params.get("estado")
    data_inicio = request.query_params.get("data_inicio")
    data_fim    = request.query_params.get("data_fim")
    if bioma:       qs = qs.filter(bioma=bioma)
    if estado:      qs = qs.filter(estado=estado.upper())
    if data_inicio: qs = qs.filter(data_hora__date__gte=data_inicio)
    if data_fim:    qs = qs.filter(data_hora__date__lte=data_fim)

    serie = (
        qs.annotate(mes=TruncMonth("data_hora"))
        .values("mes")
        .annotate(
            focos=Count("id"),
            frp_medio=Avg("frp"),
        )
        .order_by("mes")
    )

    return Response([
        {
            "mes":       item["mes"].strftime("%Y-%m"),
            "focos":     item["focos"],
            "frp_medio": round(item["frp_medio"] or 0, 2),
        }
        for item in serie
    ])


# ── NOVO: Dados agregados para os gráficos ────────────────────
@api_view(["GET"])
def graficos_dados_view(request):
    """
    GET /api/graficos-dados/
    Retorna todos os dados necessários para os 6 gráficos em uma única chamada.
    Filtros opcionais: estado, bioma, data_inicio, data_fim
    """
    qs_focos = FocoQueimada.objects.all()
    qs_areas = AreaRisco.objects.all()
    bioma       = request.query_params.get("bioma")
    estado      = request.query_params.get("estado")
    data_inicio = request.query_params.get("data_inicio")
    data_fim    = request.query_params.get("data_fim")

    if bioma:       qs_focos = qs_focos.filter(bioma=bioma)
    if estado:      qs_focos = qs_focos.filter(estado=estado.upper())
    if data_inicio: qs_focos = qs_focos.filter(data_hora__date__gte=data_inicio)
    if data_fim:    qs_focos = qs_focos.filter(data_hora__date__lte=data_fim)

    # G1 — Focos por bioma
    por_bioma = list(
        qs_focos.values("bioma")
        .annotate(
            total=Count("id"),
            frp_medio=Avg("frp"),
            dias_sc_medio=Avg("dias_sem_chuva"),
        )
        .order_by("-total")
    )

    # G2 — Série temporal
    serie = list(
        qs_focos.annotate(mes=TruncMonth("data_hora"))
        .values("mes")
        .annotate(focos=Count("id"), frp_medio=Avg("frp"))
        .order_by("mes")
    )

    # G3 — Top 10 ranking
    top10 = list(
        qs_areas.order_by("ranking")[:10].values(
            "ranking", "nome", "score_topsis", "nivel_risco",
            "total_focos", "frp_media", "risco_historico_medio",
            "dias_sem_chuva_medio", "precipitacao_media",
        )
    )

    # G4 — Top 5 para radar (normalizado)
    top5_raw = list(
        qs_areas.order_by("ranking")[:5].values(
            "nome", "total_focos", "frp_media",
            "risco_historico_medio", "dias_sem_chuva_medio", "precipitacao_media",
        )
    )

    # Normaliza os valores do top5 para [0,1]
    campos = ["total_focos", "frp_media", "risco_historico_medio",
              "dias_sem_chuva_medio", "precipitacao_media"]
    CUSTO  = {"precipitacao_media"}

    if top5_raw:
        mins = {c: min(r[c] or 0 for r in top5_raw) for c in campos}
        maxs = {c: max(r[c] or 0 for r in top5_raw) for c in campos}

        top5_norm = []
        for r in top5_raw:
            norm = {}
            for c in campos:
                dif = (maxs[c] - mins[c]) or 1
                v   = ((r[c] or 0) - mins[c]) / dif
                norm[c] = round(1 - v if c in CUSTO else v, 4)
            top5_norm.append({"nome": r["nome"], "valores": norm})
    else:
        top5_norm = []

    # G6 — Distribuição de scores por nível
    scores_por_nivel = {}
    for nivel in ["CRITICO", "ALTO", "MEDIO", "BAIXO"]:
        qs_n = qs_areas.filter(nivel_risco=nivel)
        agg  = qs_n.aggregate(
            n=Count("id"),
            minS=Min("score_topsis"),
            maxS=Max("score_topsis"),
            medS=Avg("score_topsis"),
        )
        # Amostra de scores para histograma (máx 500)
        scores_raw = list(
            qs_n.order_by("score_topsis")
            .values_list("score_topsis", flat=True)[:500]
        )
        scores_por_nivel[nivel] = {
            "n":      agg["n"] or 0,
            "min":    round(agg["minS"] or 0, 4),
            "max":    round(agg["maxS"] or 0, 4),
            "media":  round(agg["medS"] or 0, 4),
            "scores": [round(s, 4) for s in scores_raw],
        }

    # G5 — Scatter: amostra de score × focos por nível
    scatter = {}
    for nivel in ["CRITICO", "ALTO", "MEDIO", "BAIXO"]:
        pontos = list(
            qs_areas.filter(nivel_risco=nivel)
            .order_by("ranking")[:200]
            .values_list("score_topsis", "total_focos")
        )
        scatter[nivel] = [
            {"score": round(p[0], 4), "focos": p[1]}
            for p in pontos if p[1] is not None
        ]

    return Response({
        "por_bioma":       por_bioma,
        "serie_temporal":  [
            {
                "mes":       s["mes"].strftime("%Y-%m"),
                "focos":     s["focos"],
                "frp_medio": round(s["frp_medio"] or 0, 2),
            }
            for s in serie
        ],
        "top10":           top10,
        "top5_radar":      top5_norm,
        "scores_por_nivel": scores_por_nivel,
        "scatter":         scatter,
    })


@csrf_exempt
@api_view(["POST"])
def calcular_topsis_view(request):
    data_inicio_str = request.data.get("data_inicio")
    data_fim_str    = request.data.get("data_fim")
    estado_filtro   = request.data.get("estado")
    bioma_filtro    = request.data.get("bioma")

    from datetime import datetime
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        data_inicio = None

    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        data_fim = None

    qs = FocoQueimada.objects.all()
    if data_inicio:   qs = qs.filter(data_hora__date__gte=data_inicio)
    if data_fim:      qs = qs.filter(data_hora__date__lte=data_fim)
    if estado_filtro: qs = qs.filter(estado=estado_filtro.upper())
    if bioma_filtro:  qs = qs.filter(bioma=bioma_filtro)

    metricas = (
        qs.values("municipio", "estado", "bioma")
        .annotate(
            total_focos=Count("id"),
            frp_media=Avg("frp"),
            risco_historico_medio=Avg("risco_historico"),
            dias_sem_chuva_medio=Avg("dias_sem_chuva"),
            precipitacao_media=Avg("precipitacao"),
        )
        .filter(total_focos__gte=1)
    )

    if not metricas:
        return Response({"mensagem": "Nenhum foco encontrado com os filtros aplicados."},
                        status=status.HTTP_200_OK)

    alternativas = [
        {
            "nome":                  f"{m['municipio']}/{m['estado']}/{m['bioma']}",
            "municipio":             m["municipio"],
            "estado":                m["estado"],
            "bioma":                 m["bioma"],
            "total_focos":           m["total_focos"]           or 0,
            "frp_media":             m["frp_media"]             or 0.0,
            "risco_historico_medio": m["risco_historico_medio"] or 0.0,
            "dias_sem_chuva_medio":  m["dias_sem_chuva_medio"]  or 0.0,
            "precipitacao_media":    m["precipitacao_media"]    or 0.0,
        }
        for m in metricas
    ]

    resultado = calcular_topsis_fuzzy(alternativas)

    if not data_inicio or not data_fim:
        primeiro = FocoQueimada.objects.order_by("data_hora").first()
        ultimo   = FocoQueimada.objects.order_by("-data_hora").first()
        data_inicio = data_inicio or (primeiro.data_hora.date() if primeiro else date.today())
        data_fim    = data_fim    or (ultimo.data_hora.date()   if ultimo   else date.today())

    AreaRisco.objects.all().delete()
    novas_areas = [
        AreaRisco(
            nome=item["nome"], estado=item["estado"], bioma=item["bioma"],
            geometria=None,
            score_topsis=item["score_topsis"], ranking=item["ranking"],
            nivel_risco=item["nivel_risco"], total_focos=item["total_focos"],
            frp_media=item["frp_media"],
            risco_historico_medio=item["risco_historico_medio"],
            dias_sem_chuva_medio=item["dias_sem_chuva_medio"],
            precipitacao_media=item["precipitacao_media"],
            periodo_inicio=data_inicio, periodo_fim=data_fim,
        )
        for item in resultado
    ]
    AreaRisco.objects.bulk_create(novas_areas)

    return Response({
        "mensagem":          f"TOPSIS Fuzzy calculado para {len(resultado)} áreas.",
        "periodo":           {"inicio": str(data_inicio), "fim": str(data_fim)},
        "filtros":           {"estado": estado_filtro or "Todos", "bioma": bioma_filtro or "Todos"},
        "areas_atualizadas": len(novas_areas),
        "top_5": [
            {"nome": r["nome"], "score_topsis": r["score_topsis"],
             "nivel_risco": r["nivel_risco"], "ranking": r["ranking"]}
            for r in resultado[:5]
        ],
    })


@csrf_exempt
@api_view(["POST"])
def importar_csv_view(request):
    caminho = request.data.get("caminho", "/app/data/focos_mensal.csv")
    task = importar_csv_inpe.delay(caminho)
    return Response({"mensagem": "Importação iniciada.", "task_id": task.id, "caminho": caminho})


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

    total_focos = qs.count()
    por_bioma   = list(
        qs.values("bioma")
        .annotate(total=Count("id"), frp_media=Avg("frp"))
        .order_by("-total")
    )
    areas_criticas = AreaRisco.objects.filter(nivel_risco="CRITICO").count()
    areas_alto     = AreaRisco.objects.filter(nivel_risco="ALTO").count()

    return Response({
        "total_focos":      total_focos,
        "areas_criticas":   areas_criticas,
        "areas_alto_risco": areas_alto,
        "por_bioma":        por_bioma,
    })
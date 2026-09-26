from datetime import date
from django.contrib.gis.geos import Polygon
from django.db.models import Avg, Count, Min, Max
from django.db.models.functions import TruncMonth
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Min, Max, Sum   # Sum é novo


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


# ── NOVO: Matriz de correlação entre os 5 critérios TOPSIS ───────────
@api_view(["GET"])
def correlacao_view(request):
    """
    GET /api/correlacao/
    Retorna matrizes de correlação de Pearson e Spearman entre os 5 critérios
    do TOPSIS Fuzzy, calculadas sobre os dados reais das áreas ranqueadas.

    Saída:
      - rotulos:   nomes dos critérios
      - pearson:   matriz 5×5 de correlações lineares
      - spearman:  matriz 5×5 de correlações de posto
      - pvalores:  matriz 5×5 de p-valores (teste t, bilateral)
      - n:         número de áreas utilizadas

    Referência: Cohen (1988) — limites de efeito |r|: 0.1 pequeno,
                0.3 médio, 0.5 grande.
    """
    import math

    CAMPOS  = [
        "total_focos",
        "frp_media",
        "risco_historico_medio",
        "dias_sem_chuva_medio",
        "precipitacao_media",
    ]
    ROTULOS = [
        "C1 — Focos",
        "C2 — FRP",
        "C3 — Risco Hist.",
        "C4 — Dias s/ Chuva",
        "C5 — Precipitação",
    ]

    # Aplica filtros opcionais para consistência com os outros gráficos
    qs = AreaRisco.objects.all()
    nivel  = request.query_params.get("nivel_risco")
    estado = request.query_params.get("estado")
    bioma  = request.query_params.get("bioma")
    if nivel:  qs = qs.filter(nivel_risco=nivel.upper())
    if estado: qs = qs.filter(estado=estado.upper())
    if bioma:  qs = qs.filter(bioma=bioma)

    rows = list(qs.values_list(*CAMPOS))
    N    = len(rows)
    K    = len(CAMPOS)

    if N < 3:
        return Response(
            {"erro": "Amostras insuficientes para calcular correlação (mín. 3)."},
            status=400,
        )

    # ── Helpers estatísticos (Python puro, sem NumPy) ──────────────
    def media(arr):
        return sum(arr) / len(arr)

    def pearson_r(x, y):
        mx, my = media(x), media(y)
        num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        dx  = sum((xi - mx) ** 2 for xi in x)
        dy  = sum((yi - my) ** 2 for yi in y)
        den = math.sqrt(dx * dy)
        return num / den if den > 1e-12 else 0.0

    def rankear(arr):
        """Rank médio para empates (Spearman padrão)."""
        idx_ord = sorted(range(len(arr)), key=lambda i: arr[i])
        ranks   = [0.0] * len(arr)
        i = 0
        while i < len(idx_ord):
            j = i
            while j < len(idx_ord) - 1 and arr[idx_ord[j]] == arr[idx_ord[j + 1]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k_ in range(i, j + 1):
                ranks[idx_ord[k_]] = avg
            i = j + 1
        return ranks

    def pvalor(r, n):
        """
        P-valor bilateral do teste t para correlação de Pearson.
        H0: ρ = 0 | Estatística: t = r√(n-2)/√(1-r²)
        Aproximação de Abramowitz & Stegun para a CDF da t-Student.
        """
        if abs(r) >= 1.0:
            return 0.0
        df = n - 2
        t  = r * math.sqrt(df) / math.sqrt(1.0 - r * r)
        # Aproximação da CDF t via regularized incomplete beta
        # Para df grandes (>30) converge para Normal; usamos a fórmula exata
        x   = df / (df + t * t)
        # Série de Lentz para Ix(a,b): a=df/2, b=0.5
        # Simplificação: para df ≥ 2 usamos a aproximação de Hill (1970)
        a   = df / 2.0
        b   = 0.5
        # Regularized incomplete beta via continued fraction (5 iterações)
        def ibeta(xx, aa, bb):
            if xx == 0: return 0.0
            if xx == 1: return 1.0
            lbeta = (math.lgamma(aa) + math.lgamma(bb) - math.lgamma(aa + bb))
            front = math.exp(math.log(xx) * aa + math.log(1 - xx) * bb - lbeta) / aa
            # Método de Lentz
            cf = 1.0; d = 1.0 - (aa + bb) * xx / (aa + 1); d = 1.0 / d if abs(d) > 1e-30 else 1e30
            c = 1.0; f = d
            for m in range(1, 50):
                # Passo 2m-1
                num1 = m * (bb - m) * xx / ((aa + 2*m - 1) * (aa + 2*m))
                d = 1.0 + num1 * d; d = 1.0 / d if abs(d) > 1e-30 else 1e30
                c = 1.0 + num1 / c if abs(c) > 1e-30 else 1e30
                f *= c * d
                # Passo 2m
                num2 = -(aa + m) * (aa + bb + m) * xx / ((aa + 2*m) * (aa + 2*m + 1))
                d = 1.0 + num2 * d; d = 1.0 / d if abs(d) > 1e-30 else 1e30
                c = 1.0 + num2 / c if abs(c) > 1e-30 else 1e30
                delta = c * d; f *= delta
                if abs(delta - 1.0) < 1e-10: break
            return front * f

        p_one = 0.5 * ibeta(x, a, b)   # P(T > |t|) unilateral
        return round(min(2.0 * p_one, 1.0), 6)  # bilateral

    # ── Colunas numéricas ──────────────────────────────────────────
    cols = [
        [float(row[j] or 0) for row in rows]
        for j in range(K)
    ]
    ranked = [rankear(c) for c in cols]

    # ── Matrizes 5×5 ──────────────────────────────────────────────
    mat_p   = []  # Pearson
    mat_s   = []  # Spearman
    mat_pv  = []  # p-valores (sobre Pearson)

    for i in range(K):
        row_p  = []
        row_s  = []
        row_pv = []
        for j in range(K):
            if i == j:
                row_p.append(1.0); row_s.append(1.0); row_pv.append(0.0)
            else:
                rp = round(pearson_r(cols[i],   cols[j]),   4)
                rs = round(pearson_r(ranked[i], ranked[j]), 4)
                pv = pvalor(rp, N)
                row_p.append(rp); row_s.append(rs); row_pv.append(pv)
        mat_p.append(row_p); mat_s.append(row_s); mat_pv.append(row_pv)

    return Response({
        "rotulos":  ROTULOS,
        "pearson":  mat_p,
        "spearman": mat_s,
        "pvalores": mat_pv,
        "n":        N,
    })
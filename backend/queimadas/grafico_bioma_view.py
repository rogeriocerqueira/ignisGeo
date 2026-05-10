from django.db.models import Avg, Count, Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AreaRisco, FocoQueimada


@api_view(["GET"])
def grafico_bioma_view(request):
    """
    GET /api/grafico-bioma/

    Agrega AreaRisco por bioma e devolve os 5 critérios médios do TOPSIS Fuzzy,
    prontos para alimentar o GraficoTopsis3D.vue.

    Filtros opcionais: estado, data_inicio, data_fim, nivel_risco

    Resposta (lista ordenada por score_medio desc):
    [
      {
        "bioma":                  "CERRADO",
        "bioma_display":          "Cerrado",
        "n_municipios":           87,
        "total_focos":            4820,
        "frp_media":              32.5,
        "risco_historico_medio":  0.88,
        "dias_sem_chuva_medio":   85.0,
        "precipitacao_media":     12.0,
        "score_medio":            0.724
      },
      ...
    ]
    """
    BIOMA_DISPLAY = dict(FocoQueimada.BIOMAS)

    qs = AreaRisco.objects.all()

    estado      = request.query_params.get("estado")
    nivel       = request.query_params.get("nivel_risco")
    data_inicio = request.query_params.get("data_inicio")
    data_fim    = request.query_params.get("data_fim")

    if estado:      qs = qs.filter(estado=estado.upper())
    if nivel:       qs = qs.filter(nivel_risco=nivel.upper())
    if data_inicio: qs = qs.filter(periodo_inicio__gte=data_inicio)
    if data_fim:    qs = qs.filter(periodo_fim__lte=data_fim)

    por_bioma = (
        qs.values("bioma")
        .annotate(
            n_municipios          = Count("id"),
            total_focos           = Sum("total_focos"),
            frp_media             = Avg("frp_media"),
            risco_historico_medio = Avg("risco_historico_medio"),
            dias_sem_chuva_medio  = Avg("dias_sem_chuva_medio"),
            precipitacao_media    = Avg("precipitacao_media"),
            score_medio           = Avg("score_topsis"),
        )
        .order_by("-score_medio")
    )

    return Response([
        {
            "bioma":                  row["bioma"],
            "bioma_display":          BIOMA_DISPLAY.get(row["bioma"], row["bioma"].title()),
            "n_municipios":           row["n_municipios"],
            "total_focos":            row["total_focos"] or 0,
            "frp_media":              round(row["frp_media"]             or 0, 2),
            "risco_historico_medio":  round(row["risco_historico_medio"] or 0, 4),
            "dias_sem_chuva_medio":   round(row["dias_sem_chuva_medio"]  or 0, 1),
            "precipitacao_media":     round(row["precipitacao_media"]     or 0, 2),
            "score_medio":            round(row["score_medio"]            or 0, 4),
        }
        for row in por_bioma
    ])
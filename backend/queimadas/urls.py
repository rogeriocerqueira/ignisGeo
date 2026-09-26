from django.urls import path
from . import views
from .grafico_bioma_view import grafico_bioma_view

urlpatterns = [
    # Focos de queimada
    path("focos/geojson/", views.FocosGeoJSONView.as_view(), name="focos-geojson"),
    path("focos/",         views.FocosListView.as_view(),    name="focos-list"),

    # Áreas de risco (resultado do TOPSIS)
    path("areas-risco/geojson/", views.AreasRiscoGeoJSONView.as_view(), name="areas-geojson"),
    path("ranking/",             views.RankingView.as_view(),           name="ranking"),

    # Ações
    path("calcular-topsis/", views.calcular_topsis_view, name="calcular-topsis"),
    path("importar-csv/",    views.importar_csv_view,    name="importar-csv"),

    # Dashboard
    path("estatisticas/",   views.estatisticas_view,    name="estatisticas"),

    # Gráficos — dados dinâmicos
    path("serie-temporal/", views.serie_temporal_view,  name="serie-temporal"),
    path("graficos-dados/", views.graficos_dados_view,  name="graficos-dados"),

    # Análise estatística
    path("correlacao/",     views.correlacao_view,      name="correlacao"),

    # Gráfico 3D Fuzzy TOPSIS — dados agregados por bioma
    path("grafico-bioma/",  grafico_bioma_view,         name="grafico-bioma"),
]
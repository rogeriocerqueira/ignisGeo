from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import FocoQueimada, AreaRisco


class FocoQueimadaGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = FocoQueimada
        geo_field = "localizacao"
        fields = [
            "id", "localizacao", "data_hora",
            "municipio", "estado", "bioma",
            "frp", "risco_historico",
            "dias_sem_chuva", "precipitacao", "satelite",
        ]


class FocoQueimadaListSerializer(serializers.ModelSerializer):
    latitude  = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    class Meta:
        model = FocoQueimada
        fields = [
            "id", "latitude", "longitude",
            "data_hora", "municipio", "estado",
            "bioma", "frp", "risco_historico",
        ]


class AreaRiscoGeoSerializer(GeoFeatureModelSerializer):
    nivel_risco_display = serializers.CharField(
        source="get_nivel_risco_display", read_only=True
    )

    class Meta:
        model = AreaRisco
        geo_field = "geometria"
        fields = [
            "id", "geometria", "nome", "estado", "bioma",
            "score_topsis", "ranking", "nivel_risco",
            "nivel_risco_display", "total_focos", "frp_media",
            "risco_historico_medio", "dias_sem_chuva_medio",
            "precipitacao_media", "periodo_inicio", "periodo_fim",
            "atualizado_em",
        ]


class AreaRiscoRankingSerializer(serializers.ModelSerializer):
    """Ranking completo — inclui todos os critérios do TOPSIS."""
    nivel_risco_display = serializers.CharField(
        source="get_nivel_risco_display", read_only=True
    )

    class Meta:
        model = AreaRisco
        fields = [
            "id", "nome", "estado", "bioma",
            "score_topsis", "ranking",
            "nivel_risco", "nivel_risco_display",
            "total_focos", "frp_media",
            "risco_historico_medio",       # ← C3
            "dias_sem_chuva_medio",        # ← C4
            "precipitacao_media",          # ← C5
            "periodo_inicio", "periodo_fim",
        ]
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField
from .models import FocoQueimada, AreaRisco


class FocoQueimadaGeoSerializer(GeoFeatureModelSerializer):
    """Serializa focos de queimada como GeoJSON Feature."""

    class Meta:
        model = FocoQueimada
        geo_field = "localizacao"
        fields = [
            "id",
            "localizacao",
            "data_hora",
            "municipio",
            "estado",
            "bioma",
            "frp",
            "risco_historico",
            "vento_ms",
            "ndvi",
            "satelite",
        ]


class FocoQueimadaListSerializer(serializers.ModelSerializer):
    """Serializer simples (sem GeoJSON) para listagens rápidas."""
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    class Meta:
        model = FocoQueimada
        fields = [
            "id", "latitude", "longitude",
            "data_hora", "municipio", "estado",
            "bioma", "frp", "risco_historico",
        ]


class AreaRiscoGeoSerializer(GeoFeatureModelSerializer):
    """Serializa áreas de risco como GeoJSON Feature com todos os atributos."""
    nivel_risco_display = serializers.CharField(
        source="get_nivel_risco_display", read_only=True
    )

    class Meta:
        model = AreaRisco
        geo_field = "geometria"
        fields = [
            "id",
            "geometria",
            "nome",
            "estado",
            "bioma",
            "score_topsis",
            "ranking",
            "nivel_risco",
            "nivel_risco_display",
            "total_focos",
            "frp_media",
            "risco_historico_medio",
            "vento_medio",
            "ndvi_medio",
            "periodo_inicio",
            "periodo_fim",
            "atualizado_em",
        ]


class AreaRiscoRankingSerializer(serializers.ModelSerializer):
    """Serializer para o painel de ranking (sem geometria para ser leve)."""
    nivel_risco_display = serializers.CharField(
        source="get_nivel_risco_display", read_only=True
    )

    class Meta:
        model = AreaRisco
        fields = [
            "id", "nome", "estado", "bioma",
            "score_topsis", "ranking", "nivel_risco",
            "nivel_risco_display", "total_focos",
            "frp_media", "periodo_inicio", "periodo_fim",
        ]

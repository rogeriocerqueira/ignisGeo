from django.contrib.gis.db import models


class FocoQueimada(models.Model):
    """Foco de queimada importado do INPE BDQueimadas."""

    BIOMAS = [
        ("AMAZONIA", "Amazônia"),
        ("CERRADO", "Cerrado"),
        ("CAATINGA", "Caatinga"),
        ("MATA_ATLANTICA", "Mata Atlântica"),
        ("PANTANAL", "Pantanal"),
        ("PAMPA", "Pampa"),
    ]

    # Localização geográfica (ponto com SRID 4326 = WGS84)
    localizacao = models.PointField(srid=4326)

    # Dados do foco
    data_hora = models.DateTimeField(db_index=True)
    municipio = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    bioma = models.CharField(max_length=20, choices=BIOMAS)

    # Potência radiativa do fogo (Fire Radiative Power) em MW
    frp = models.FloatField(help_text="Fire Radiative Power em MW")

    # Risco histórico acumulado na célula (0 a 1)
    risco_historico = models.FloatField(default=0.0)

    # Velocidade do vento em m/s (dado complementar)
    vento_ms = models.FloatField(null=True, blank=True)

    # Índice de vegetação (NDVI, de -1 a 1)
    ndvi = models.FloatField(null=True, blank=True)

    # Satélite de detecção
    satelite = models.CharField(max_length=50, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_hora"]
        indexes = [
            models.Index(fields=["bioma"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["data_hora"]),
        ]

    def __str__(self):
        return f"Foco {self.municipio}/{self.estado} — {self.data_hora:%d/%m/%Y}"

    @property
    def latitude(self):
        return self.localizacao.y

    @property
    def longitude(self):
        return self.localizacao.x


class AreaRisco(models.Model):
    """
    Área geográfica com score de risco calculado pelo TOPSIS Fuzzy.
    Pode representar um município, uma célula de grade ou um bioma.
    """

    NIVEIS = [
        ("CRITICO", "Crítico"),
        ("ALTO", "Alto"),
        ("MEDIO", "Médio"),
        ("BAIXO", "Baixo"),
    ]

    nome = models.CharField(max_length=200)
    estado = models.CharField(max_length=2)
    bioma = models.CharField(max_length=20)

    # Polígono da área (MultiPolygon para compatibilidade com shapefiles)
    geometria = models.MultiPolygonField(srid=4326, null=True, blank=True)


    # Score TOPSIS (0 a 1, quanto maior = maior risco)
    score_topsis = models.FloatField()

    # Posição no ranking geral
    ranking = models.PositiveIntegerField()

    # Nível de risco derivado do score
    nivel_risco = models.CharField(max_length=10, choices=NIVEIS)

    # Métricas que alimentaram o TOPSIS
    total_focos = models.IntegerField(default=0)
    frp_media = models.FloatField(default=0.0)
    risco_historico_medio = models.FloatField(default=0.0)
    vento_medio = models.FloatField(default=0.0)
    ndvi_medio = models.FloatField(default=0.0)

    # Período de referência do cálculo
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ranking"]

    def __str__(self):
        return f"{self.nome} — Score: {self.score_topsis:.3f} ({self.nivel_risco})"

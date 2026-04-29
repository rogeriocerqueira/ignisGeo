from django.contrib.gis.db import models


class FocoQueimada(models.Model):
    """
    Foco de queimada importado do INPE BDQueimadas.
    Cada instância representa um foco detectado por satélite.
    Campos derivados do CSV padrão: DataHora, Estado, Municipio,
    Bioma, FRP, RiscoFogo, DiaSemChuva, Precipitacao, Lat, Lon.
    """

    BIOMAS = [
        ("AMAZONIA",       "Amazônia"),
        ("CERRADO",        "Cerrado"),
        ("CAATINGA",       "Caatinga"),
        ("MATA_ATLANTICA", "Mata Atlântica"),
        ("PANTANAL",       "Pantanal"),
        ("PAMPA",          "Pampa"),
    ]

    # Localização geográfica — ponto WGS84 com índice espacial GIST
    localizacao = models.PointField(srid=4326)

    # Dados temporais e de identificação
    data_hora = models.DateTimeField(db_index=True)
    municipio = models.CharField(max_length=100)
    estado    = models.CharField(max_length=2)
    bioma     = models.CharField(max_length=20, choices=BIOMAS)
    satelite  = models.CharField(max_length=50, blank=True)

    # Intensidade do fogo — Fire Radiative Power em MW
    frp = models.FloatField(help_text="Fire Radiative Power em MW")

    # Risco histórico INPE — índice sintético [0, 1]
    risco_historico = models.FloatField(default=0.0)

    # Dias consecutivos sem chuva — campo DiaSemChuva do CSV INPE
    dias_sem_chuva = models.FloatField(
        null=True, blank=True,
        help_text="Número de dias consecutivos sem chuva"
    )

    # Precipitação acumulada — campo Precipitacao do CSV INPE (mm)
    precipitacao = models.FloatField(
        null=True, blank=True,
        help_text="Precipitação acumulada em mm"
    )

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
    Resultado do TOPSIS Fuzzy por município.
    Cada instância representa a agregação de todos os focos
    de um município no período analisado, com score e ranking
    calculados pelo algoritmo multicritério.

    Critérios utilizados (todos do CSV padrão INPE BDQueimadas):
      C1 — total_focos           : contagem de focos no período
      C2 — frp_media             : Fire Radiative Power médio (MW)
      C3 — risco_historico_medio : índice de risco INPE [0,1]
      C4 — dias_sem_chuva_medio  : média de dias sem chuva (benefício)
      C5 — precipitacao_media    : precipitação média em mm (custo)
    """

    NIVEIS = [
        ("CRITICO", "Crítico"),
        ("ALTO",    "Alto"),
        ("MEDIO",   "Médio"),
        ("BAIXO",   "Baixo"),
    ]

    nome   = models.CharField(max_length=200, unique=True)
    estado = models.CharField(max_length=2)
    bioma  = models.CharField(max_length=20)

    # Polígono do município — preenchido com shapefile IBGE quando disponível
    geometria = models.MultiPolygonField(srid=4326, null=True, blank=True)

    # Score TOPSIS Fuzzy — coeficiente de similaridade CC ∈ [0, 1]
    score_topsis = models.FloatField()

    # Posição no ranking e nível de risco por percentil
    ranking     = models.PositiveIntegerField()
    nivel_risco = models.CharField(max_length=10, choices=NIVEIS)

    # Métricas agregadas que alimentaram o TOPSIS (5 critérios)
    total_focos           = models.IntegerField(default=0)   # C1
    frp_media             = models.FloatField(default=0.0)   # C2
    risco_historico_medio = models.FloatField(default=0.0)   # C3
    dias_sem_chuva_medio  = models.FloatField(default=0.0)   # C4
    precipitacao_media    = models.FloatField(default=0.0)   # C5

    # Período de referência do cálculo
    periodo_inicio = models.DateField()
    periodo_fim    = models.DateField()

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ranking"]

    def __str__(self):
        return f"{self.nome} — Score: {self.score_topsis:.3f} ({self.nivel_risco})"
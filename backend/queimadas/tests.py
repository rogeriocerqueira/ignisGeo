"""
Testes do backend IgnisGeo.

Cobertura:
  - NumeroFuzzy (distância, operações)
  - normalizar_fuzzy
  - calcular_topsis_fuzzy (algoritmo completo)
  - classificar_nivel
  - FocoQueimada model
  - AreaRisco model
  - Endpoints da API REST
"""

from datetime import date, datetime
from django.utils import timezone


from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.test import TestCase
from rest_framework.test import APIClient

from .models import AreaRisco, FocoQueimada
from .topsis_fuzzy import (
    NumeroFuzzy,
    calcular_topsis_fuzzy,
    classificar_nivel,
    normalizar_fuzzy,
)


# ══════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════

def make_foco(**kwargs) -> FocoQueimada:
    defaults = {
        "localizacao": Point(-36.0, -9.5, srid=4326),
        "data_hora":   timezone.make_aware(datetime(2026, 2, 1, 12, 0, 0)), 
        "municipio":   "CORURIPE",
        "estado":      "AL",
        "bioma":       "MATA_ATLANTICA",
        "frp":         50.0,
        "risco_historico": 0.5,
        "satelite":    "NOAA-20",
    }
    defaults.update(kwargs)
    return FocoQueimada.objects.create(**defaults)

def test_geojson_retorna_feature_collection(self):
    resp = self.client.get("/api/focos/geojson/")
    self.assertEqual(resp.status_code, 200)
    data = resp.json()
    # Agora sem paginação — retorna FeatureCollection direto
    self.assertEqual(data["type"], "FeatureCollection")
    self.assertIn("features", data)
    self.assertIsInstance(data["features"], list)
def make_area(**kwargs) -> AreaRisco:
    """Cria uma AreaRisco com valores padrão."""
    poly = Polygon(((0, 0), (1, 0), (1, 1), (0, 1), (0, 0)), srid=4326)
    defaults = {
        "nome":          "CORURIPE/AL",
        "estado":        "AL",
        "bioma":         "MATA_ATLANTICA",
        "geometria":     MultiPolygon(poly),
        "score_topsis":  0.55,
        "ranking":       1,
        "nivel_risco":   "ALTO",
        "total_focos":   100,
        "frp_media":     45.0,
        "risco_historico_medio": 0.5,
        "vento_medio":   3.0,
        "ndvi_medio":    0.4,
        "periodo_inicio": date(2026, 2, 1),
        "periodo_fim":   date(2026, 4, 22),
    }
    defaults.update(kwargs)
    return AreaRisco.objects.create(**defaults)


# ══════════════════════════════════════════════
# 1. NumeroFuzzy
# ══════════════════════════════════════════════

class NumeroFuzzyTest(TestCase):

    def test_criacao(self):
        nf = NumeroFuzzy(0.2, 0.5, 0.8)
        self.assertEqual(nf.a, 0.2)
        self.assertEqual(nf.b, 0.5)
        self.assertEqual(nf.c, 0.8)

    def test_distancia_identico_eh_zero(self):
        nf = NumeroFuzzy(0.3, 0.5, 0.7)
        self.assertAlmostEqual(nf.distancia(nf), 0.0)

    def test_distancia_ideal_positivo(self):
        """Distância de (0,0,0) para (1,1,1) deve ser 1.0."""
        neg = NumeroFuzzy(0.0, 0.0, 0.0)
        pos = NumeroFuzzy(1.0, 1.0, 1.0)
        self.assertAlmostEqual(neg.distancia(pos), 1.0)

    def test_distancia_simetrica(self):
        a = NumeroFuzzy(0.1, 0.3, 0.6)
        b = NumeroFuzzy(0.4, 0.6, 0.9)
        self.assertAlmostEqual(a.distancia(b), b.distancia(a))

    def test_distancia_formula_vertex(self):
        """Verifica manualmente: sqrt(1/3 * ((0.1)^2 + (0.2)^2 + (0.3)^2))"""
        import math
        a = NumeroFuzzy(0.0, 0.0, 0.0)
        b = NumeroFuzzy(0.1, 0.2, 0.3)
        esperado = math.sqrt((1/3) * (0.01 + 0.04 + 0.09))
        self.assertAlmostEqual(a.distancia(b), esperado, places=6)


# ══════════════════════════════════════════════
# 2. normalizar_fuzzy
# ══════════════════════════════════════════════

class NormalizarFuzzyTest(TestCase):

    def test_valor_minimo_gera_fuzzy_proximo_zero(self):
        nf = normalizar_fuzzy(0.0, 0.0, 100.0)
        self.assertEqual(nf.b, 0.0)
        self.assertEqual(nf.a, 0.0)

    def test_valor_maximo_gera_fuzzy_proximo_um(self):
        nf = normalizar_fuzzy(100.0, 0.0, 100.0)
        self.assertEqual(nf.b, 1.0)
        self.assertEqual(nf.c, 1.0)

    def test_valor_medio(self):
        nf = normalizar_fuzzy(50.0, 0.0, 100.0)
        self.assertAlmostEqual(nf.b, 0.5)
        self.assertAlmostEqual(nf.a, 0.4)
        self.assertAlmostEqual(nf.c, 0.6)

    def test_min_igual_max_retorna_meio(self):
        nf = normalizar_fuzzy(5.0, 5.0, 5.0)
        self.assertEqual(nf.a, 0.5)
        self.assertEqual(nf.b, 0.5)
        self.assertEqual(nf.c, 0.5)

    def test_spread_nao_ultrapassa_limites(self):
        nf = normalizar_fuzzy(0.0, 0.0, 100.0)
        self.assertGreaterEqual(nf.a, 0.0)
        nf2 = normalizar_fuzzy(100.0, 0.0, 100.0)
        self.assertLessEqual(nf2.c, 1.0)


# ══════════════════════════════════════════════
# 3. classificar_nivel
# ══════════════════════════════════════════════

class ClassificarNivelTest(TestCase):

    def test_critico(self):
        self.assertEqual(classificar_nivel(0.45), "CRITICO")
        self.assertEqual(classificar_nivel(1.00), "CRITICO")
        self.assertEqual(classificar_nivel(0.55), "CRITICO")

    def test_alto(self):
        self.assertEqual(classificar_nivel(0.35), "ALTO")
        self.assertEqual(classificar_nivel(0.44), "ALTO")

    def test_medio(self):
        self.assertEqual(classificar_nivel(0.25), "MEDIO")
        self.assertEqual(classificar_nivel(0.34), "MEDIO")

    def test_baixo(self):
        self.assertEqual(classificar_nivel(0.00), "BAIXO")
        self.assertEqual(classificar_nivel(0.24), "BAIXO")

        
# ══════════════════════════════════════════════
# 4. calcular_topsis_fuzzy
# ══════════════════════════════════════════════

def _alternativa(nome, focos, frp, risco, vento, ndvi):
    return {
        "nome": nome, "municipio": nome, "estado": "AL", "bioma": "CAATINGA",
        "total_focos": focos, "frp_media": frp,
        "risco_historico_medio": risco, "vento_medio": vento, "ndvi_medio": ndvi,
    }


class TopsisTest(TestCase):

    def test_lista_vazia_retorna_vazia(self):
        self.assertEqual(calcular_topsis_fuzzy([]), [])

    def test_retorna_mesma_quantidade(self):
        alts = [
            _alternativa("A", 100, 50.0, 0.8, 5.0, 0.3),
            _alternativa("B", 50,  20.0, 0.4, 2.0, 0.6),
            _alternativa("C", 200, 80.0, 0.9, 7.0, 0.2),
        ]
        resultado = calcular_topsis_fuzzy(alts)
        self.assertEqual(len(resultado), 3)

    def test_area_maior_risco_tem_ranking_1(self):
        """A área com mais focos e maior FRP deve ter ranking 1."""
        alts = [
            _alternativa("Baixo",  10,  5.0, 0.1, 1.0, 0.8),
            _alternativa("Alto",  500, 200.0, 0.9, 8.0, 0.1),
        ]
        resultado = calcular_topsis_fuzzy(alts)
        self.assertEqual(resultado[0]["nome"], "Alto")
        self.assertEqual(resultado[0]["ranking"], 1)

    def test_score_entre_zero_e_um(self):
        alts = [
            _alternativa("X", 100, 50.0, 0.5, 3.0, 0.4),
            _alternativa("Y",  50, 20.0, 0.3, 2.0, 0.6),
        ]
        for item in calcular_topsis_fuzzy(alts):
            self.assertGreaterEqual(item["score_topsis"], 0.0)
            self.assertLessEqual(item["score_topsis"], 1.0)

    def test_ranking_sequencial(self):
        alts = [_alternativa(f"Área{i}", i*10, i*5.0, i*0.1, i*1.0, 0.5) for i in range(1, 6)]
        resultado = calcular_topsis_fuzzy(alts)
        rankings = [r["ranking"] for r in resultado]
        self.assertEqual(sorted(rankings), list(range(1, 6)))

    def test_nivel_risco_presente(self):
        alts = [_alternativa("A", 100, 50.0, 0.5, 3.0, 0.4)]
        resultado = calcular_topsis_fuzzy(alts)
        self.assertIn(resultado[0]["nivel_risco"], ["CRITICO", "ALTO", "MEDIO", "BAIXO"])

    def test_alternativa_unica(self):
        alts = [_alternativa("Único", 100, 50.0, 0.5, 3.0, 0.4)]
        resultado = calcular_topsis_fuzzy(alts)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ranking"], 1)


# ══════════════════════════════════════════════
# 5. Models
# ══════════════════════════════════════════════

class FocoQueimadaModelTest(TestCase):

    def test_criacao_basica(self):
        foco = make_foco()
        self.assertIsNotNone(foco.pk)

    def test_str(self):
        foco = make_foco(municipio="MACEIÓ", estado="AL")
        self.assertIn("MACEIÓ", str(foco))
        self.assertIn("AL", str(foco))

    def test_latitude_longitude_property(self):
        foco = make_foco(localizacao=Point(-36.5, -9.7, srid=4326))
        self.assertAlmostEqual(foco.latitude,  -9.7)
        self.assertAlmostEqual(foco.longitude, -36.5)

    def test_bioma_choices_valido(self):
        for bioma, _ in FocoQueimada.BIOMAS:
            f = make_foco(bioma=bioma)
            self.assertEqual(f.bioma, bioma)


class AreaRiscoModelTest(TestCase):

    def test_criacao_basica(self):
        area = make_area()
        self.assertIsNotNone(area.pk)

    def test_str(self):
        area = make_area(nome="CORURIPE/AL", score_topsis=0.55, nivel_risco="ALTO")
        self.assertIn("CORURIPE", str(area))
        self.assertIn("0.550", str(area))

    def test_ordenacao_por_ranking(self):
        make_area(nome="C/AL", ranking=3, score_topsis=0.3)
        make_area(nome="A/AL", ranking=1, score_topsis=0.9)
        make_area(nome="B/AL", ranking=2, score_topsis=0.6)
        areas = list(AreaRisco.objects.all())
        self.assertEqual(areas[0].ranking, 1)
        self.assertEqual(areas[1].ranking, 2)
        self.assertEqual(areas[2].ranking, 3)


# ══════════════════════════════════════════════
# 6. API Endpoints
# ══════════════════════════════════════════════

class EstatisticasAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_estatisticas_banco_vazio(self):
        resp = self.client.get("/api/estatisticas/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_focos"], 0)
        self.assertEqual(data["areas_criticas"], 0)

    def test_estatisticas_com_focos(self):
        make_foco(bioma="CERRADO", frp=30.0)
        make_foco(bioma="CERRADO", frp=50.0)
        make_foco(bioma="CAATINGA", frp=20.0)
        resp = self.client.get("/api/estatisticas/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["total_focos"], 3)


class FocosAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        make_foco(municipio="CORURIPE",  estado="AL", bioma="CAATINGA",    frp=80.0)
        make_foco(municipio="PENEDO",    estado="AL", bioma="MATA_ATLANTICA", frp=30.0)
        make_foco(municipio="ALTAMIRA",  estado="PA", bioma="AMAZONIA",    frp=200.0)

    def test_lista_todos(self):
        resp = self.client.get("/api/focos/")
        self.assertEqual(resp.status_code, 200)

    def test_filtro_estado(self):
        resp = self.client.get("/api/focos/?estado=AL")
        data = resp.json()
        resultados = data.get("results", data)
        for item in resultados:
            self.assertEqual(item["estado"], "AL")

    def test_filtro_bioma(self):
        resp = self.client.get("/api/focos/?bioma=AMAZONIA")
        data = resp.json()
        resultados = data.get("results", data)
        for item in resultados:
            self.assertEqual(item["bioma"], "AMAZONIA") # type: ignore

    def test_geojson_retorna_feature_collection(self):
        resp = self.client.get("/api/focos/geojson/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Com paginação ativa o GeoJSON vem dentro de "results"
        geojson = data.get("results", data)
        if isinstance(geojson, dict):
            self.assertEqual(geojson.get("type"), "FeatureCollection")
        else:
            self.assertIsInstance(geojson, list)


class RankingAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_ranking_vazio(self):
        resp = self.client.get("/api/ranking/")
        self.assertEqual(resp.status_code, 200)

    def test_ranking_com_areas(self):
        make_area(nome="AREA1/AL", ranking=1, score_topsis=0.9)
        make_area(nome="AREA2/AL", ranking=2, score_topsis=0.6)
        resp = self.client.get("/api/ranking/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        resultados = data.get("results", data)
        self.assertGreaterEqual(len(resultados), 2)


class TopsisAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_sem_focos_retorna_mensagem(self):
        resp = self.client.post(
            "/api/calcular-topsis/",
            {"data_inicio": "2026-02-01", "data_fim": "2026-04-22"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("mensagem", resp.json())

    def test_data_invalida_retorna_400(self):
        resp = self.client.post(
            "/api/calcular-topsis/",
            {"data_inicio": "invalida", "data_fim": "tbm-invalida"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_com_focos_calcula_ranking(self):
        for i in range(5):
            make_foco(
                municipio=f"MUNICIPIO{i}",
                estado="AL",
                bioma="CAATINGA",
                frp=float(10 + i * 20),
                risco_historico=0.3 + i * 0.1,
            )
        resp = self.client.post(
            "/api/calcular-topsis/",
            {"data_inicio": "2026-01-01", "data_fim": "2026-12-31"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("top_5", data)

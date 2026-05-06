from django.test import SimpleTestCase
from queimadas.topsis_fuzzy import (
    calcular_topsis_fuzzy, PESOS_LINGUISTICOS, PESOS_PADRAO, CRITERIOS
)

def _alt(nome, focos, frp, risco, dias, precip):
    return {
        "nome": nome, "municipio": nome, "estado": "AL", "bioma": "CAATINGA",
        "total_focos": focos, "frp_media": frp,
        "risco_historico_medio": risco, "dias_sem_chuva_medio": dias,
        "precipitacao_media": precip,
    }

class SensibilidadeTopsisTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alts = [
            _alt("Extremo",     1000, 500.0, 0.9, 45.0,   0.0),
            _alt("Equilibrado",  500, 200.0, 0.5, 20.0,   5.0),
            _alt("Seco",         100,  50.0, 0.3, 60.0,   0.0),
            _alt("Baixo",         10,   5.0, 0.1,  2.0,  50.0),
            _alt("Umidificado",  600, 150.0, 0.4,  5.0, 100.0),
        ]
        base = calcular_topsis_fuzzy(cls.alts, PESOS_PADRAO)
        cls.rank_base = [a["nome"] for a in base]
        cls.top1_base = cls.rank_base[0]
        cls.top3_base = set(cls.rank_base[:3])

    def test_estabilidade_oat(self):
        """OAT: 25 simulacoes — estabilidade Top1 > 70%, Top3 > 60%."""
        escala = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
        total = top1_ok = top3_ok = 0
        relatorio = []
        for crit in CRITERIOS:
            for nivel in escala:
                total += 1
                p = dict(PESOS_PADRAO)
                p[crit] = PESOS_LINGUISTICOS[nivel]
                r = calcular_topsis_fuzzy(self.alts, p)
                nomes = [x["nome"] for x in r]
                ok1 = nomes[0] == self.top1_base
                ok3 = set(nomes[:3]) == self.top3_base
                if ok1: top1_ok += 1
                if ok3: top3_ok += 1
                relatorio.append(
                    f"  {crit:<28} {nivel:<12} "
                    f"Top1={'OK' if ok1 else 'MUDOU'}  "
                    f"Top3={'OK' if ok3 else 'MUDOU'}  {nomes}"
                )
        e1 = top1_ok / total * 100
        e3 = top3_ok / total * 100
        print(f"\n{'='*60}")
        print("RELATORIO DE SENSIBILIDADE — IGNISGEO (OAT)")
        print(f"{'='*60}")
        print(f"Ranking base:  {self.rank_base}")
        print(f"Simulacoes:    {total}")
        print(f"Estab. Top 1:  {e1:.1f}%  ({top1_ok}/{total})")
        print(f"Estab. Top 3:  {e3:.1f}%  ({top3_ok}/{total})")
        print("-"*60)
        for linha in relatorio: print(linha)
        print("="*60)
        self.assertGreater(e1, 70.0, f"Top1={e1:.1f}% < 70%.")
        self.assertGreater(e3, 60.0, f"Top3={e3:.1f}% < 60%.")

    def test_criterio_custo_penaliza_areas_umidas(self):
        """Criterio custo: diferenca de score Seco vs Umido cresce com peso maior."""
        alts_custo = [
            _alt("Seco_X",  500, 200.0, 0.5, 30.0,   5.0),
            _alt("Umido_X", 500, 200.0, 0.5, 30.0,  95.0),
            _alt("Ref",     300, 100.0, 0.3, 15.0,  50.0),
        ]
        p_baixo = {**PESOS_PADRAO, "precipitacao_media": PESOS_LINGUISTICOS["muito_baixo"]}
        p_alto  = {**PESOS_PADRAO, "precipitacao_media": PESOS_LINGUISTICOS["muito_alto"]}
        r_b = calcular_topsis_fuzzy(alts_custo, p_baixo)
        r_a = calcular_topsis_fuzzy(alts_custo, p_alto)
        sc = lambda res, nome: next(x["score_topsis"] for x in res if x["nome"] == nome)
        sb, sa = sc(r_b, "Seco_X"),  sc(r_a, "Seco_X")
        ub, ua = sc(r_b, "Umido_X"), sc(r_a, "Umido_X")
        print(f"\n[custo] MB: Seco={sb:.4f} Umido={ub:.4f} diff={sb-ub:.4f}")
        print(f"[custo] MA: Seco={sa:.4f} Umido={ua:.4f} diff={sa-ua:.4f}")
        self.assertGreaterEqual(sa - ua, sb - ub,
            "Peso maior de precipitacao deve ampliar diferenca de score.")
        self.assertGreater(sa, ua,
            "Com peso alto, area seca deve superar area umida.")

    def test_monotonicidade_extremo_lidera_pesos_maximos(self):
        """Com todos os pesos MA, 'Extremo' (dominante) deve ser #1."""
        p = {c: PESOS_LINGUISTICOS["muito_alto"] for c in CRITERIOS}
        self.assertEqual(calcular_topsis_fuzzy(self.alts, p)[0]["nome"], "Extremo")

    def test_scores_em_ordem_decrescente(self):
        """CCi deve estar em ordem decrescente no resultado retornado."""
        scores = [x["score_topsis"] for x in calcular_topsis_fuzzy(self.alts, PESOS_PADRAO)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_sem_rank_reversal_remocao_dominada(self):
        """Remover alternativa dominada nao deve inverter o Top 2."""
        sem_baixo = [a for a in self.alts if a["nome"] != "Baixo"]
        top2_novo = [x["nome"] for x in calcular_topsis_fuzzy(sem_baixo, PESOS_PADRAO)[:2]]
        print(f"\n[reversal] base={self.rank_base[:2]}  novo={top2_novo}")
        self.assertEqual(top2_novo, self.rank_base[:2])

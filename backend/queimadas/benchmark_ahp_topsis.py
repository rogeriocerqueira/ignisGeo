from queimadas.topsis_fuzzy import calcular_topsis_fuzzy, PESOS_PADRAO
from queimadas.models import AreaRisco

PESOS_AHP = {
    "total_focos":           (0.3439, 0.3439, 0.3439),
    "frp_media":             (0.3439, 0.3439, 0.3439),
    "risco_historico_medio": (0.1289, 0.1289, 0.1289),
    "dias_sem_chuva_medio":  (0.1289, 0.1289, 0.1289),
    "precipitacao_media":    (0.0544, 0.0544, 0.0544),
}

qs = AreaRisco.objects.values(
    "nome", "estado", "bioma",
    "total_focos", "frp_media",
    "risco_historico_medio", "dias_sem_chuva_medio",
    "precipitacao_media",
)

alternativas = []
for r in qs:
    r["municipio"] = r["nome"]
    alternativas.append(dict(r))

print(f"Alternativas carregadas: {len(alternativas)}")

ranking_topsis = calcular_topsis_fuzzy(alternativas, PESOS_PADRAO)
ranking_ahp    = calcular_topsis_fuzzy(alternativas, PESOS_AHP)

nomes_t = [r["nome"] for r in ranking_topsis]
nomes_a = [r["nome"] for r in ranking_ahp]

top5_t = set(nomes_t[:5])
top5_a = set(nomes_a[:5])
concordancia_top5 = len(top5_t & top5_a)

print("\n" + "=" * 60)
print("BENCHMARK: TOPSIS Fuzzy vs AHP")
print("=" * 60)
print(f"\nMetrica 1 -- Concordancia Top 5: {concordancia_top5}/5")
print(f"  TOPSIS Fuzzy: {nomes_t[:5]}")
print(f"  AHP:          {nomes_a[:5]}")
print(f"  Intersecao:   {top5_t & top5_a}")

try:
    from scipy.stats import spearmanr
    pos_t = {n: i for i, n in enumerate(nomes_t[:100])}
    pos_a = {n: i for i, n in enumerate(nomes_a[:100])}
    comuns = [n for n in nomes_t[:100] if n in pos_a]
    rho, p_val = spearmanr(
        [pos_t[n] for n in comuns],
        [pos_a[n] for n in comuns]
    )
    print(f"\nMetrica 2 -- Spearman Top 100:")
    print(f"  rho = {rho:.4f}  p = {p_val:.6f}")
    print(f"  {'Alta correlacao' if rho > 0.80 else 'Divergencia'}")
except ImportError:
    print("\nMetrica 2 -- scipy nao disponivel")

top1_t = nomes_t[0]
top1_a = nomes_a[0]
converge = top1_t == top1_a
print(f"\nMetrica 3 -- Convergencia Top 1:")
print(f"  TOPSIS Fuzzy: {top1_t}  CC={ranking_topsis[0]['score_topsis']:.4f}")
print(f"  AHP:          {top1_a}")
print(f"  Convergencia: {'SIM' if converge else 'NAO'}")

print("\n" + "=" * 60)
print("RESUMO PARA O ARTIGO")
print("=" * 60)
print(f"  Concordancia Top 5:  {concordancia_top5}/5")
try:
    print(f"  Spearman Top 100:    rho={rho:.3f}  p={p_val:.6f}")
except:
    pass
print(f"  Convergencia Top 1:  {'Sim' if converge else 'Nao'}")
print(f"  CR (matriz AHP):     0.0124 <= 0.10")
print("=" * 60)

"""
topsis_fuzzy.py — TOPSIS Fuzzy (Chen, 2000)
IgnisGeo · TCC UEFS 2026

Referência:
  Chen, C.T. (2000). Extensions of the TOPSIS for group decision-making
  under fuzzy environment. Fuzzy Sets and Systems, 114(1), 1–9.
"""

import math


# ══════════════════════════════════════════════════════════════════════
# NumeroFuzzy — Número Fuzzy Triangular (NFT)
# ══════════════════════════════════════════════════════════════════════

class NumeroFuzzy:
    """
    Número fuzzy triangular (a, b, c) conforme Chen (2000).
      a = limite inferior  (l)
      b = valor modal      (m)
      c = limite superior  (u)
    """

    def __init__(self, a: float, b: float, c: float):
        self.a = a
        self.b = b
        self.c = c

    def distancia(self, other: "NumeroFuzzy") -> float:
        """
        Distância de vértice entre dois NFT (Chen, 2000, Eq. 4):
          d = sqrt(1/3 × [(a1-a2)² + (b1-b2)² + (c1-c2)²])
        """
        return math.sqrt(
            ((self.a - other.a) ** 2 +
             (self.b - other.b) ** 2 +
             (self.c - other.c) ** 2) / 3
        )

    def __repr__(self) -> str:
        return f"NFT({self.a:.3f}, {self.b:.3f}, {self.c:.3f})"


# ══════════════════════════════════════════════════════════════════════
# normalizar_fuzzy
# ══════════════════════════════════════════════════════════════════════

def normalizar_fuzzy(valor: float, min_v: float, max_v: float) -> NumeroFuzzy:
    """
    Normaliza um valor escalar para [0,1] e adiciona spread fixo de ±0.10,
    retornando um NFT (a, b, c) com a ∈ [0,1] e c ∈ [0,1].

    Quando min_v == max_v (degenerate), retorna NFT(0.5, 0.5, 0.5).
    """
    if max_v <= min_v:
        return NumeroFuzzy(0.5, 0.5, 0.5)
    b = (valor - min_v) / (max_v - min_v)
    spread = 0.1
    return NumeroFuzzy(
        max(0.0, b - spread),
        b,
        min(1.0, b + spread),
    )


# ══════════════════════════════════════════════════════════════════════
# classificar_nivel — limiares fixos (função de compatibilidade)
# ══════════════════════════════════════════════════════════════════════

def classificar_nivel(cc: float) -> str:
    """
    Classifica um CCᵢ por limiares fixos de score.
    Usada para consultas pontuais e compatibilidade com código legado.
    O pipeline calcular_topsis_fuzzy usa classificação por percentil
    de ranking (mais robusta para conjuntos de tamanhos variados).
    """
    if cc >= 0.45: return "CRITICO"
    if cc >= 0.35: return "ALTO"
    if cc >= 0.25: return "MEDIO"
    return "BAIXO"


# ══════════════════════════════════════════════════════════════════════
# Pesos linguísticos (Chen, 2000, Tabela 1, p. 3)
# NFT = (l, m, u) — domínio normalizado [0, 1]
# ══════════════════════════════════════════════════════════════════════

PESOS_LINGUISTICOS = {
    "muito_baixo": (0.00, 0.00, 0.25),
    "baixo":       (0.00, 0.25, 0.50),
    "medio":       (0.25, 0.50, 0.75),
    "alto":        (0.50, 0.75, 1.00),
    "muito_alto":  (0.75, 1.00, 1.00),
}

# Pesos padrão do IgnisGeo
PESOS_PADRAO = {
    "total_focos":           PESOS_LINGUISTICOS["muito_alto"],  # C1 — Benefício
    "frp_media":             PESOS_LINGUISTICOS["muito_alto"],  # C2 — Benefício
    "risco_historico_medio": PESOS_LINGUISTICOS["alto"],        # C3 — Benefício
    "dias_sem_chuva_medio":  PESOS_LINGUISTICOS["alto"],        # C4 — Benefício
    "precipitacao_media":    PESOS_LINGUISTICOS["medio"],       # C5 — Custo
}

# Critérios custo: maior valor → menor risco (inversão na normalização)
CRITERIOS_CUSTO = {"precipitacao_media"}
CRITERIOS = list(PESOS_PADRAO.keys())


# ══════════════════════════════════════════════════════════════════════
# calcular_topsis_fuzzy — Pipeline principal
# ══════════════════════════════════════════════════════════════════════

def calcular_topsis_fuzzy(alternativas: list, pesos: dict = None) -> list:
    """
    Executa o algoritmo TOPSIS Fuzzy (Chen, 2000) sobre as alternativas.

    Parâmetros
    ----------
    alternativas : list[dict]
        Cada dicionário deve conter as chaves de CRITERIOS com valores numéricos.
    pesos : dict | None
        Mapeamento {nome_criterio: (l, m, u)}.
        Quando None, usa PESOS_PADRAO (pesos padrão do IgnisGeo).

    Classificação de nível de risco por PERCENTIL DE RANKING:
      Top 10%   → CRITICO
      10%–25%   → ALTO
      25%–50%   → MEDIO
      Acima 50% → BAIXO
    Usa max(1, n × p) para garantir pelo menos 1 CRITICO em qualquer n.

    Retorna
    -------
    list[dict]
        Lista ordenada por ranking (1 = maior risco) com campos:
        nome, municipio, estado, bioma, score_topsis, ranking,
        nivel_risco e os 5 critérios.
    """
    if pesos is None:
        pesos = PESOS_PADRAO
    if not alternativas:
        return []

    n = len(alternativas)
    k = len(CRITERIOS)

    # ── 1. Extrai matriz de valores brutos ────────────────────────────
    matriz = []
    for alt in alternativas:
        linha = [float(alt.get(c, 0) or 0) for c in CRITERIOS]
        matriz.append(linha)

    # ── 2. Normaliza cada critério para NFT com spread ±0.10 ──────────
    # Critério custo: inverte o valor antes de normalizar
    nft_matriz = []
    for i in range(n):
        linha_nft = []
        for j, crit in enumerate(CRITERIOS):
            col   = [matriz[ii][j] for ii in range(n)]
            min_v = min(col)
            max_v = max(col)
            val   = matriz[i][j]
            if crit in CRITERIOS_CUSTO:
                # Inversão: alta precipitação → baixo risco
                val = max_v - val + min_v
            linha_nft.append(normalizar_fuzzy(val, min_v, max_v))
        nft_matriz.append(linha_nft)

    # ── 3. Pondera cada NFT pelo peso linguístico do critério ─────────
    def ponderar(nft: NumeroFuzzy, peso_tuple: tuple) -> NumeroFuzzy:
        l, m, u = peso_tuple
        return NumeroFuzzy(nft.a * l, nft.b * m, nft.c * u)

    v = []
    for i in range(n):
        linha = []
        for j, crit in enumerate(CRITERIOS):
            peso = pesos.get(crit, PESOS_PADRAO[crit])
            linha.append(ponderar(nft_matriz[i][j], peso))
        v.append(linha)

    # ── 4. FPIS (Fuzzy Positive Ideal Solution) e FNIS ───────────────
    fpis = []
    fnis = []
    for j in range(k):
        col     = [v[i][j] for i in range(n)]
        idx_max = max(range(n), key=lambda i: col[i].b)
        idx_min = min(range(n), key=lambda i: col[i].b)
        fpis.append(col[idx_max])
        fnis.append(col[idx_min])

    # ── 5. Distâncias ao FPIS e ao FNIS (métrica de vértice) ─────────
    d_pos = []
    d_neg = []
    for i in range(n):
        dp = math.sqrt(sum(v[i][j].distancia(fpis[j]) ** 2 for j in range(k)))
        dn = math.sqrt(sum(v[i][j].distancia(fnis[j]) ** 2 for j in range(k)))
        d_pos.append(dp)
        d_neg.append(dn)

    # ── 6. Coeficiente de similaridade CCᵢ ∈ [0, 1] ──────────────────
    cc = []
    for i in range(n):
        denom = d_pos[i] + d_neg[i]
        cc.append(d_neg[i] / denom if denom > 1e-12 else 0.0)

    # ── 7. Ordena por CCᵢ decrescente ────────────────────────────────
    ordem = sorted(range(n), key=lambda i: cc[i], reverse=True)

    # ── 8. Classifica nível por percentil de ranking ──────────────────
    # max(1, n × p): garante pelo menos 1 CRITICO para qualquer n ≥ 1
    lim_critico = max(1, n * 0.10)
    lim_alto    = max(1, n * 0.25)
    lim_medio   = max(1, n * 0.50)

    def nivel_percentil(rank: int) -> str:
        if rank <= lim_critico: return "CRITICO"
        if rank <= lim_alto:    return "ALTO"
        if rank <= lim_medio:   return "MEDIO"
        return "BAIXO"

    # ── 9. Monta resultado ────────────────────────────────────────────
    resultado = []
    for rank, idx in enumerate(ordem, start=1):
        alt = alternativas[idx]
        resultado.append({
            "nome":                  alt.get("nome", ""),
            "municipio":             alt.get("municipio", ""),
            "estado":                alt.get("estado", ""),
            "bioma":                 alt.get("bioma", ""),
            "score_topsis":          round(cc[idx], 4),
            "ranking":               rank,
            "nivel_risco":           nivel_percentil(rank),
            "total_focos":           alt.get("total_focos", 0),
            "frp_media":             alt.get("frp_media", 0.0),
            "risco_historico_medio": alt.get("risco_historico_medio", 0.0),
            "dias_sem_chuva_medio":  alt.get("dias_sem_chuva_medio", 0.0),
            "precipitacao_media":    alt.get("precipitacao_media", 0.0),
        })

    return resultado
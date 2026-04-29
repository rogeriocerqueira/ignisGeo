"""
TOPSIS Fuzzy — Technique for Order of Preference by Similarity to Ideal Solution
com números fuzzy triangulares (a, b, c).

Referência: Chen, C.T. (2000). Extensions of the TOPSIS for group decision-making
under fuzzy environment. Fuzzy Sets and Systems, 114(1), 1-9.

Critérios utilizados (todos do CSV padrão INPE BDQueimadas):
  C1 — total_focos           : contagem de focos no período         (benefício)
  C2 — frp_media             : Fire Radiative Power médio em MW     (benefício)
  C3 — risco_historico_medio : índice de risco histórico INPE [0,1] (benefício)
  C4 — dias_sem_chuva_medio  : média de dias consecutivos sem chuva (benefício)
  C5 — precipitacao_media    : precipitação acumulada média em mm   (custo)
"""

import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class NumeroFuzzy:
    """Número fuzzy triangular (a, b, c) onde a ≤ b ≤ c."""
    a: float
    b: float
    c: float

    def distancia(self, outro: "NumeroFuzzy") -> float:
        """Distância entre dois números fuzzy triangulares (vertex method)."""
        return np.sqrt(
            (1 / 3) * (
                (self.a - outro.a) ** 2 +
                (self.b - outro.b) ** 2 +
                (self.c - outro.c) ** 2
            )
        )


# Escala linguística fuzzy para os pesos dos critérios (Chen, 2000)
PESOS_LINGUISTICOS = {
    "muito_baixo": NumeroFuzzy(0.0,  0.0,  0.25),
    "baixo":       NumeroFuzzy(0.0,  0.25, 0.50),
    "medio":       NumeroFuzzy(0.25, 0.50, 0.75),
    "alto":        NumeroFuzzy(0.50, 0.75, 1.00),
    "muito_alto":  NumeroFuzzy(0.75, 1.00, 1.00),
}

# Critérios de custo — valor alto significa MENOR risco (invertidos na normalização)
CRITERIOS_CUSTO = {"precipitacao_media"}


def normalizar_fuzzy(valor: float, minimo: float, maximo: float) -> NumeroFuzzy:
    """
    Converte um valor numérico real em número fuzzy triangular normalizado [0,1].
    O spread de ±0,10 captura a incerteza inerente ao sensoriamento remoto.
    """
    if maximo == minimo:
        return NumeroFuzzy(0.5, 0.5, 0.5)

    norm = (valor - minimo) / (maximo - minimo)
    a = max(0.0, norm - 0.10)
    b = norm
    c = min(1.0, norm + 0.10)
    return NumeroFuzzy(a, b, c)


def classificar_por_percentil(resultado: list) -> list:
    """
    Classifica os níveis de risco com base nos percentis do conjunto calculado.

    Abordagem relativa: a classificação reflete a posição do município
    no conjunto analisado, garantindo distribuição real entre os níveis
    independente do tamanho da amostra ou da completude dos dados.

      Top 10%  → CRÍTICO
      10–25%   → ALTO
      25–50%   → MÉDIO
      abaixo   → BAIXO
    """
    if not resultado:
        return resultado

    scores = sorted([r["score_topsis"] for r in resultado], reverse=True)
    n = len(scores)

    p10 = scores[max(0, int(n * 0.10) - 1)]
    p25 = scores[max(0, int(n * 0.25) - 1)]
    p50 = scores[max(0, int(n * 0.50) - 1)]

    for r in resultado:
        s = r["score_topsis"]
        if s >= p10:
            r["nivel_risco"] = "CRITICO"
        elif s >= p25:
            r["nivel_risco"] = "ALTO"
        elif s >= p50:
            r["nivel_risco"] = "MEDIO"
        else:
            r["nivel_risco"] = "BAIXO"

    return resultado


def calcular_topsis_fuzzy(
    alternativas: List[dict],
    pesos: dict = None
) -> List[dict]:
    """
    Executa o TOPSIS Fuzzy e retorna as alternativas com score e ranking.

    Parâmetros
    ----------
    alternativas : lista de dicts com as métricas de cada município.
        Cada dict deve conter:
          nome, municipio, estado, bioma,
          total_focos, frp_media, risco_historico_medio,
          dias_sem_chuva_medio, precipitacao_media

    pesos : dict com pesos linguísticos por critério (opcional).
        Se None, usa os pesos padrão definidos abaixo.

    Retorna
    -------
    Lista de dicts com score_topsis, nivel_risco e ranking,
    ordenada por score decrescente.
    """

    if not alternativas:
        return []

    # Pesos padrão — escala linguística fuzzy (Chen, 2000)
    # Justificativa: critérios são indicadores já processados pelo INPE,
    # cuja hierarquia é objetivamente derivada da natureza dos dados,
    # dispensando comparações par-a-par do AHP.
    if pesos is None:
        pesos = {
            "total_focos":           PESOS_LINGUISTICOS["muito_alto"],  # C1
            "frp_media":             PESOS_LINGUISTICOS["muito_alto"],  # C2
            "risco_historico_medio": PESOS_LINGUISTICOS["alto"],        # C3
            "dias_sem_chuva_medio":  PESOS_LINGUISTICOS["alto"],        # C4
            "precipitacao_media":    PESOS_LINGUISTICOS["medio"],       # C5 (custo)
        }

    criterios  = list(pesos.keys())
    n_alt      = len(alternativas)
    n_crit     = len(criterios)

    # --- Passo 1: Normalizar os valores reais em números fuzzy ---
    valores_brutos = {c: [a[c] for a in alternativas] for c in criterios}
    minimos = {c: min(v) for c, v in valores_brutos.items()}
    maximos = {c: max(v) for c, v in valores_brutos.items()}

    matriz_fuzzy = []
    for alt in alternativas:
        linha = []
        for c in criterios:
            if c in CRITERIOS_CUSTO:
                # Critério de custo: inverte antes de normalizar
                # precipitação alta = menor risco → inverte para benefício
                val_inv = maximos[c] - alt[c] + minimos[c]
                fuz = normalizar_fuzzy(val_inv, minimos[c], maximos[c])
            else:
                fuz = normalizar_fuzzy(alt[c], minimos[c], maximos[c])
            linha.append(fuz)
        matriz_fuzzy.append(linha)

    # --- Passo 2: Matriz de decisão fuzzy ponderada ---
    # v_ij = w_j ⊗ r_ij (multiplicação componente a componente)
    def multiplicar_fuzzy(w: NumeroFuzzy, r: NumeroFuzzy) -> NumeroFuzzy:
        return NumeroFuzzy(w.a * r.a, w.b * r.b, w.c * r.c)

    pesos_lista = [pesos[c] for c in criterios]
    matriz_ponderada = [
        [multiplicar_fuzzy(pesos_lista[j], matriz_fuzzy[i][j])
         for j in range(n_crit)]
        for i in range(n_alt)
    ]

    # --- Passo 3: Soluções ideais positiva (A+) e negativa (A-) ---
    ideal_pos = [NumeroFuzzy(1.0, 1.0, 1.0)] * n_crit
    ideal_neg = [NumeroFuzzy(0.0, 0.0, 0.0)] * n_crit

    # --- Passo 4: Distâncias às soluções ideais (vertex method) ---
    distancias_pos = []
    distancias_neg = []

    for i in range(n_alt):
        d_pos = sum(
            matriz_ponderada[i][j].distancia(ideal_pos[j])
            for j in range(n_crit)
        )
        d_neg = sum(
            matriz_ponderada[i][j].distancia(ideal_neg[j])
            for j in range(n_crit)
        )
        distancias_pos.append(d_pos)
        distancias_neg.append(d_neg)

    # --- Passo 5: Coeficiente de similaridade CC_i ---
    # CC_i = d_neg / (d_pos + d_neg) ∈ [0, 1]
    # Quanto maior CC_i, maior o risco relativo do município
    scores = []
    for i in range(n_alt):
        denominador = distancias_pos[i] + distancias_neg[i]
        score = distancias_neg[i] / denominador if denominador > 0 else 0.0
        scores.append(score)

    # --- Passo 6: Monta resultado, ordena e atribui ranking ---
    resultado = []
    for i, alt in enumerate(alternativas):
        resultado.append({
            **alt,
            "score_topsis": round(scores[i], 4),
            "nivel_risco":  "BAIXO",  # sobrescrito pelo percentil
        })

    resultado.sort(key=lambda x: x["score_topsis"], reverse=True)
    for rank, item in enumerate(resultado, start=1):
        item["ranking"] = rank

    # Classifica por percentil — garante distribuição real entre os níveis
    resultado = classificar_por_percentil(resultado)

    return resultado


def classificar_nivel(score: float) -> str:
    """
    Classificação por threshold fixo — mantida para compatibilidade
    com testes unitários existentes.
    Para classificação do conjunto completo, use classificar_por_percentil().
    """
    if score >= 0.45:
        return "CRITICO"
    elif score >= 0.35:
        return "ALTO"
    elif score >= 0.25:
        return "MEDIO"
    else:
        return "BAIXO"
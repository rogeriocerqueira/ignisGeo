"""
TOPSIS Fuzzy — Technique for Order of Preference by Similarity to Ideal Solution
com números fuzzy triangulares (a, b, c).

Referência: Chen, C.T. (2000). Extensions of the TOPSIS for group decision-making
under fuzzy environment. Fuzzy Sets and Systems, 114(1), 1-9.
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


# Escala linguística fuzzy para os pesos dos critérios
PESOS_LINGUISTICOS = {
    "muito_baixo": NumeroFuzzy(0.0, 0.0, 0.25),
    "baixo":       NumeroFuzzy(0.0, 0.25, 0.50),
    "medio":       NumeroFuzzy(0.25, 0.50, 0.75),
    "alto":        NumeroFuzzy(0.50, 0.75, 1.00),
    "muito_alto":  NumeroFuzzy(0.75, 1.00, 1.00),
}

# Escala linguística fuzzy para os valores dos critérios
RATINGS_LINGUISTICOS = {
    "muito_ruim":  NumeroFuzzy(0, 0, 1),
    "ruim":        NumeroFuzzy(0, 1, 3),
    "medio_ruim":  NumeroFuzzy(1, 3, 5),
    "medio":       NumeroFuzzy(3, 5, 7),
    "medio_bom":   NumeroFuzzy(5, 7, 9),
    "bom":         NumeroFuzzy(7, 9, 10),
    "muito_bom":   NumeroFuzzy(9, 10, 10),
}


def normalizar_fuzzy(valor: float, minimo: float, maximo: float) -> NumeroFuzzy:
    """
    Converte um valor numérico real em número fuzzy triangular normalizado [0,1].
    Quanto maior o valor, maior o número fuzzy (critério de benefício).
    """
    if maximo == minimo:
        return NumeroFuzzy(0.5, 0.5, 0.5)

    norm = (valor - minimo) / (maximo - minimo)
    # Spread de 10% para capturar incerteza
    a = max(0.0, norm - 0.10)
    b = norm
    c = min(1.0, norm + 0.10)
    return NumeroFuzzy(a, b, c)


def calcular_topsis_fuzzy(
    alternativas: List[dict],
    pesos: dict = None
) -> List[dict]:
    """
    Executa o TOPSIS Fuzzy e retorna as alternativas com score e ranking.

    Parâmetros
    ----------
    alternativas : lista de dicts com as métricas de cada área
        Cada dict deve conter: nome, total_focos, frp_media,
        risco_historico_medio, vento_medio, ndvi_medio
    pesos : dict com pesos linguísticos por critério (opcional)

    Retorna
    -------
    Lista de dicts com score_topsis e ranking, ordenada por score decrescente.
    """

    if not alternativas:
        return []

    # Pesos padrão dos critérios (importância relativa)
    if pesos is None:
        pesos = {
            "total_focos":          PESOS_LINGUISTICOS["muito_alto"],
            "frp_media":            PESOS_LINGUISTICOS["muito_alto"],
            "risco_historico_medio": PESOS_LINGUISTICOS["alto"],
            "vento_medio":          PESOS_LINGUISTICOS["medio"],
            "ndvi_medio":           PESOS_LINGUISTICOS["alto"],
        }

    criterios = list(pesos.keys())
    n_alt = len(alternativas)
    n_crit = len(criterios)

    # --- Passo 1: Normalizar os valores reais em números fuzzy ---
    valores_brutos = {c: [a[c] for a in alternativas] for c in criterios}
    minimos = {c: min(v) for c, v in valores_brutos.items()}
    maximos = {c: max(v) for c, v in valores_brutos.items()}

    # Inverter NDVI: vegetação mais densa = menor risco
    # (NDVI alto = menos risco, então tratamos como critério de custo invertendo)
    matriz_fuzzy = []
    for alt in alternativas:
        linha = []
        for c in criterios:
            if c == "ndvi_medio":
                # Critério de custo: normaliza invertido
                val_inv = maximos[c] - alt[c] + minimos[c]
                fuz = normalizar_fuzzy(val_inv, minimos[c], maximos[c])
            else:
                fuz = normalizar_fuzzy(alt[c], minimos[c], maximos[c])
            linha.append(fuz)
        matriz_fuzzy.append(linha)

    # --- Passo 2: Matriz de decisão fuzzy ponderada ---
    # v_ij = w_j ⊗ r_ij (multiplicação de fuzzy triangulares)
    def multiplicar_fuzzy(w: NumeroFuzzy, r: NumeroFuzzy) -> NumeroFuzzy:
        return NumeroFuzzy(w.a * r.a, w.b * r.b, w.c * r.c)

    pesos_lista = [pesos[c] for c in criterios]
    matriz_ponderada = [
        [multiplicar_fuzzy(pesos_lista[j], matriz_fuzzy[i][j])
         for j in range(n_crit)]
        for i in range(n_alt)
    ]

    # --- Passo 3: Solução ideal positiva (A+) e negativa (A-) ---
    # Para critérios de benefício: A+ = (1,1,1), A- = (0,0,0)
    ideal_pos = [NumeroFuzzy(1.0, 1.0, 1.0)] * n_crit
    ideal_neg = [NumeroFuzzy(0.0, 0.0, 0.0)] * n_crit

    # --- Passo 4: Distância de cada alternativa às soluções ideais ---
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

    # --- Passo 5: Coeficiente de similaridade (score TOPSIS) ---
    # CCi = d_neg / (d_pos + d_neg) — quanto maior, maior o risco
    scores = []
    for i in range(n_alt):
        denominador = distancias_pos[i] + distancias_neg[i]
        score = distancias_neg[i] / denominador if denominador > 0 else 0.0
        scores.append(score)

    # --- Passo 6: Classificar e retornar ---
    resultado = []
    for i, alt in enumerate(alternativas):
        nivel = classificar_nivel(scores[i])
        resultado.append({
            **alt,
            "score_topsis": round(scores[i], 4),
            "nivel_risco": nivel,
        })

    resultado.sort(key=lambda x: x["score_topsis"], reverse=True)
    for rank, item in enumerate(resultado, start=1):
        item["ranking"] = rank

    return resultado


def classificar_nivel(score: float) -> str:
    """
    Classifica o nível de risco com base no score TOPSIS.
    Thresholds calibrados empiricamente — NDVI ausente nos dados INPE
    comprime o score máximo para ~0.55, portanto os limiares são ajustados.
    """
    if score >= 0.45:
        return "CRITICO"
    elif score >= 0.35:
        return "ALTO"
    elif score >= 0.25:
        return "MEDIO"
    else:
        return "BAIXO"
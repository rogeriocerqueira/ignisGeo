<template>
  <div class="graficos-page">

    <!-- Cabeçalho -->
    <div class="page-header">
      <div>
        <h2 class="page-titulo">Resultados da Análise TOPSIS Fuzzy</h2>
        <p class="page-sub">
          IgnisGeo · <strong>{{ totalAreas.toLocaleString("pt-BR") }}</strong> municípios ·
          <strong>{{ totalFocos.toLocaleString("pt-BR") }}</strong> focos ·
          <span v-if="periodo">{{ periodo }}</span>
        </p>
      </div>
      <div class="header-badges">
        <span class="badge azul">TOPSIS Fuzzy — Chen (2000)</span>
        <span class="badge verde">INPE BDQueimadas</span>
        <span v-if="carregando" class="badge cinza">⟳ Carregando...</span>
      </div>
    </div>

    <!-- Linha 1: Bioma + Série temporal (lado a lado) -->
    <div class="linha">
      <div class="card card-medio">
        <div class="card-header">
          <span class="card-titulo">Focos por Bioma</span>
          <span class="card-badge">C1 · C2</span>
        </div>
        <canvas ref="c1" class="canvas"></canvas>
        <p class="card-nota">Total de focos e FRP médio (MW) por bioma</p>
      </div>

      <div class="card card-grande">
        <div class="card-header">
          <span class="card-titulo">Série Temporal — Focos por Mês</span>
          <span class="card-badge">Sazonalidade</span>
        </div>
        <canvas ref="c2" class="canvas"></canvas>
        <p class="card-nota">Pico em setembro/2025 · sazonalidade jul–out</p>
      </div>
    </div>

    <!-- Linha 2: Top 10 (largura total) -->
    <div class="linha">
      <div class="card card-full">
        <div class="card-header">
          <span class="card-titulo">Top 10 Municípios — Ranking TOPSIS Fuzzy</span>
          <span class="card-badge">CCᵢ ∈ [0,1]</span>
        </div>
        <canvas ref="c3" class="canvas" style="height:280px"></canvas>
        <p class="card-nota">Classificação por percentis P₉₀ P₇₅ P₅₀ · todos Crítico</p>
      </div>
    </div>

    <!-- Linha 3: Radar + Scatter -->
    <div class="linha">
      <div class="card card-medio">
        <div class="card-header">
          <span class="card-titulo">Perfil Multicritério — Top 5</span>
          <span class="card-badge">Radar</span>
        </div>
        <canvas ref="c4" class="canvas" style="height:300px"></canvas>
        <p class="card-nota">Valores normalizados [0,1] · C1–C5</p>
      </div>

      <div class="card card-medio">
        <div class="card-header">
          <span class="card-titulo">Score TOPSIS × Focos</span>
          <span class="card-badge">Dispersão</span>
        </div>
        <canvas ref="c5" class="canvas" style="height:300px"></canvas>
        <p class="card-nota">Volume de focos não é o único determinante — MCDM discrimina pelos 5 critérios</p>
      </div>
    </div>

    <!-- Linha 4: Distribuição + Boxplot -->
    <div class="linha">
      <div class="card card-grande">
        <div class="card-header">
          <span class="card-titulo">Distribuição dos Scores por Nível</span>
          <div class="card-controles">
            <label class="toggle">
              <input type="checkbox" v-model="mostrarGauss" @change="redesenharG6" />
              <span class="toggle-slider"></span>
              <span class="toggle-label">Curva de Gauss</span>
            </label>
            <span class="card-badge">Histograma</span>
          </div>
        </div>
        <canvas ref="c6" class="canvas" style="height:260px"></canvas>
        <p class="card-nota">
          Crítico: {{ niv.CRITICO?.n ?? 0 }} ·
          Alto: {{ niv.ALTO?.n ?? 0 }} ·
          Médio: {{ niv.MEDIO?.n ?? 0 }} ·
          Baixo: {{ niv.BAIXO?.n ?? 0 }}
        </p>
      </div>

      <div class="card card-medio">
        <div class="card-header">
          <span class="card-titulo">Boxplot por Nível de Risco</span>
          <span class="card-badge">Percentis</span>
        </div>
        <canvas ref="c7" class="canvas" style="height:260px"></canvas>
        <p class="card-nota">Mediana · IQR · whiskers 1,5×IQR · percentis P₉₀ P₇₅ P₅₀</p>
      </div>
    </div>

    <!-- Tabela top 10 -->
    <div class="card card-full tabela-card">
      <div class="card-header">
        <span class="card-titulo">Tabela de Resultados — Top 10 Municípios</span>
        <span class="card-badge">Dados reais do banco</span>
      </div>
      <div class="tabela-wrap">
        <table class="tabela">
          <thead>
            <tr>
              <th>Rank</th><th>Município / UF / Bioma</th><th>Score CCᵢ</th>
              <th>Nível</th><th>Focos</th><th>FRP médio (MW)</th>
              <th>Risco histórico</th><th>Dias s/ chuva</th><th>Precip. (mm)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in dadosGraficos.top10" :key="a.ranking">
              <td class="rank-cell">#{{ a.ranking }}</td>
              <td class="nome-cell">{{ a.nome }}</td>
              <td class="score-cell">{{ fmt4(a.score_topsis) }}</td>
              <td>
                <span :class="['nivel-badge', `nivel-${(a.nivel_risco||'').toLowerCase()}`]">
                  {{ a.nivel_risco }}
                </span>
              </td>
              <td class="num-cell">{{ (a.total_focos||0).toLocaleString("pt-BR") }}</td>
              <td class="num-cell">{{ fmt2(a.frp_media) }}</td>
              <td class="num-cell">{{ fmt3(a.risco_historico_medio) }}</td>
              <td class="num-cell">{{ fmt1(a.dias_sem_chuva_medio) }}</td>
              <td class="num-cell">{{ fmt2(a.precipitacao_media) }}</td>
            </tr>
            <tr v-if="!dadosGraficos.top10?.length">
              <td colspan="9" class="vazio-cell">
                Execute o TOPSIS Fuzzy para ver os resultados.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="tabela-ref">
        Chen, C.T. (2000). Extensions of the TOPSIS for group decision-making under fuzzy environment.
        <em>Fuzzy Sets and Systems</em>, 114(1), 1–9. · Fonte: INPE BDQueimadas (2026)
      </p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { useQueimadasStore } from "@/stores/queimadas";
import api from "@/api";

const store = useQueimadasStore();

// Canvas refs
const c1 = ref(null); const c2 = ref(null); const c3 = ref(null);
const c4 = ref(null); const c5 = ref(null); const c6 = ref(null);
const c7 = ref(null);

const carregando    = ref(false);
const mostrarGauss  = ref(false);
const dadosGraficos = reactive({
  por_bioma: [], serie_temporal: [], top10: [],
  top5_radar: [], scores_por_nivel: {}, scatter: {},
});

// ── Computed ──
const niv = computed(() => dadosGraficos.scores_por_nivel || {});
const totalAreas = computed(() => store.rankingTotal || 0);
const totalFocos = computed(() => store.totalFocos    || 0);
const periodo    = computed(() => {
  const t = dadosGraficos.top10?.[0];
  if (!t) return "";
  return `${t.periodo_inicio || ""} → ${t.periodo_fim || ""}`;
});

// ── Paleta ──
const P = {
  verm:    "#B71C1C", lrj: "#E65100", amar: "#F9A825",
  verde:   "#2E7D32", azul: "#1565C0", roxo: "#4527A0",
  cinza:   "#546E7A", bco: "#FFFFFF",
};
const COR_NIVEL = {
  CRITICO: P.verm, ALTO: P.lrj, MEDIO: P.amar, BAIXO: P.verde,
};
const COR_BIOMA = {
  CERRADO: P.lrj, AMAZONIA: P.verde, CAATINGA: P.verm,
  MATA_ATLANTICA: P.azul, PANTANAL: P.roxo, PAMPA: P.cinza,
};
const NOME_BIOMA = {
  CERRADO: "Cerrado", AMAZONIA: "Amazônia", CAATINGA: "Caatinga",
  MATA_ATLANTICA: "Mata Atlântica", PANTANAL: "Pantanal", PAMPA: "Pampa",
};

// ── Formatação ──
const fmt1 = (v) => v != null ? Number(v).toFixed(1) : "—";
const fmt2 = (v) => v != null ? Number(v).toFixed(2) : "—";
const fmt3 = (v) => v != null ? Number(v).toFixed(3) : "—";
const fmt4 = (v) => v != null ? Number(v).toFixed(4) : "—";

// ── Helpers canvas ──
function initCanvas(ref, h) {
  const el = ref.value; if (!el) return null;
  el.width  = el.parentElement?.clientWidth || 600;
  el.height = h || parseInt(el.style.height) || 220;
  return el.getContext("2d");
}
function roundRect(cx, x, y, w, h, r) {
  cx.beginPath();
  cx.moveTo(x + r, y);
  cx.lineTo(x + w - r, y);
  cx.quadraticCurveTo(x + w, y, x + w, y + r);
  cx.lineTo(x + w, y + h - r);
  cx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  cx.lineTo(x + r, y + h);
  cx.quadraticCurveTo(x, y + h, x, y + h - r);
  cx.lineTo(x, y + r);
  cx.quadraticCurveTo(x, y, x + r, y);
  cx.closePath();
}

// ══════════════════════════════════════════════════
// G1 — Focos por bioma
// ══════════════════════════════════════════════════
function desenharG1() {
  const cx = initCanvas(c1, 220); if (!cx) return;
  const W = c1.value.width; const H = c1.value.height;
  const PL = 120; const PR = 180; const PT = 14; const PB = 14;
  const dados = dadosGraficos.por_bioma;
  if (!dados.length) return;
  const maxV = Math.max(...dados.map((d) => d.total));
  const bH   = (H - PT - PB) / dados.length - 5;

  cx.clearRect(0, 0, W, H);
  cx.font = "11px system-ui";

  dados.forEach((d, i) => {
    const y  = PT + i * ((H - PT - PB) / dados.length);
    const bW = ((W - PL - PR) * d.total) / maxV;
    const cor = COR_BIOMA[d.bioma] || P.cinza;

    cx.fillStyle = cor;
    roundRect(cx, PL, y, Math.max(bW, 2), bH, 3);
    cx.fill();

    cx.fillStyle = "#374151"; cx.textAlign = "right";
    cx.font = "11px system-ui";
    cx.fillText(NOME_BIOMA[d.bioma] || d.bioma, PL - 6, y + bH / 2 + 4);

    cx.textAlign = "left"; cx.fillStyle = "#6B7280"; cx.font = "10px system-ui";
    const txt = `${d.total.toLocaleString("pt-BR")} · FRP: ${Number(d.frp_medio||0).toFixed(1)} MW`;
    cx.fillText(txt, PL + bW + 6, y + bH / 2 + 4);
  });
}

// ══════════════════════════════════════════════════
// G2 — Série temporal
// ══════════════════════════════════════════════════
function desenharG2() {
  const cx = initCanvas(c2, 220); if (!cx) return;
  const W = c2.value.width; const H = c2.value.height;
  const PL = 52; const PR = 16; const PT = 24; const PB = 28;
  const serie = dadosGraficos.serie_temporal;
  if (!serie.length) return;
  const vals  = serie.map((s) => s.focos);
  const maxV  = Math.max(...vals);
  const n     = serie.length;

  cx.clearRect(0, 0, W, H);

  const xOf = (i) => PL + (i / Math.max(n - 1, 1)) * (W - PL - PR);
  const yOf = (v) => PT + (1 - v / maxV) * (H - PT - PB);

  // Área
  cx.beginPath();
  cx.moveTo(xOf(0), yOf(0));
  vals.forEach((v, i) => cx.lineTo(xOf(i), yOf(v)));
  cx.lineTo(xOf(n - 1), H - PB); cx.lineTo(xOf(0), H - PB); cx.closePath();
  cx.fillStyle = "rgba(230,81,0,0.10)"; cx.fill();

  // Linha
  cx.beginPath(); cx.moveTo(xOf(0), yOf(vals[0]));
  vals.forEach((v, i) => cx.lineTo(xOf(i), yOf(v)));
  cx.strokeStyle = P.lrj; cx.lineWidth = 2.5; cx.stroke();

  // Pontos
  vals.forEach((v, i) => {
    cx.beginPath(); cx.arc(xOf(i), yOf(v), 3, 0, Math.PI * 2);
    cx.fillStyle = P.lrj; cx.fill();
  });

  // Pico
  const idxP = vals.indexOf(maxV);
  cx.fillStyle = P.verm; cx.font = "bold 9px system-ui"; cx.textAlign = "center";
  cx.fillText(`▲ ${maxV.toLocaleString("pt-BR")}`, xOf(idxP), yOf(maxV) - 8);

  // Labels X (a cada ~3 meses)
  cx.font = "9px system-ui"; cx.fillStyle = "#6B7280"; cx.textAlign = "center";
  serie.forEach((s, i) => {
    if (i % 3 === 0) cx.fillText(s.mes.slice(0, 7), xOf(i), H - PB + 14);
  });

  // Labels Y
  cx.textAlign = "right";
  [0, Math.round(maxV / 2), maxV].forEach((v) => {
    const lbl = v >= 1000 ? `${Math.round(v / 1000)}k` : v;
    cx.fillText(lbl, PL - 4, yOf(v) + 3);
  });
}

// ══════════════════════════════════════════════════
// G3 — Top 10 barras horizontais
// ══════════════════════════════════════════════════
function desenharG3() {
  const cx = initCanvas(c3, 280); if (!cx) return;
  const W = c3.value.width; const H = c3.value.height;
  const dados = dadosGraficos.top10;
  if (!dados.length) return;
  const PL = 200; const PR = 90; const PT = 10; const PB = 10;
  const n  = dados.length;
  const bH = (H - PT - PB) / n - 4;
  const scores  = dados.map((d) => d.score_topsis);
  const minS    = Math.min(...scores) * 0.98;
  const maxS    = Math.max(...scores) * 1.01;

  cx.clearRect(0, 0, W, H);
  cx.font = "10px system-ui";

  [...dados].reverse().forEach((d, i) => {
    const y  = PT + i * ((H - PT - PB) / n);
    const bW = ((W - PL - PR) * (d.score_topsis - minS)) / (maxS - minS);

    cx.fillStyle = COR_NIVEL[d.nivel_risco] || P.cinza;
    roundRect(cx, PL, y, Math.max(bW, 2), bH, 3);
    cx.fill();

    const rank = n - i;
    cx.fillStyle = "#9CA3AF"; cx.textAlign = "right"; cx.font = "bold 10px system-ui";
    cx.fillText(`#${rank}`, PL - 140, y + bH / 2 + 4);

    const nome = d.nome.length > 28 ? d.nome.slice(0, 27) + "…" : d.nome;
    cx.fillStyle = "#374151"; cx.font = "10px system-ui";
    cx.fillText(nome, PL - 8, y + bH / 2 + 4);

    cx.textAlign = "left"; cx.fillStyle = "#374151"; cx.font = "bold 10px system-ui";
    cx.fillText(Number(d.score_topsis).toFixed(4), PL + bW + 5, y + bH / 2 + 4);
  });
}

// ══════════════════════════════════════════════════
// G4 — Radar
// ══════════════════════════════════════════════════
function desenharG4() {
  const cx = initCanvas(c4, 300); if (!cx) return;
  const W = c4.value.width; const H = c4.value.height;
  const top5 = dadosGraficos.top5_radar;
  if (!top5.length) return;

  const N   = 5;
  const crit = ["Focos", "FRP", "Risco Hist.", "Dias s/ Chuva", "Precip (inv)"];
  const campos = ["total_focos", "frp_media", "risco_historico_medio",
                  "dias_sem_chuva_medio", "precipitacao_media"];
  const cores5 = [P.verm, P.lrj, P.verde, P.azul, P.roxo];
  const cx0 = W / 2; const cy0 = H / 2 - 20;
  const R = Math.min(W, H) / 2 - 55;

  const ang = (i) => Math.PI / 2 + (2 * Math.PI * i) / N;
  const px  = (i, r) => cx0 + r * Math.cos(ang(i));
  const py  = (i, r) => cy0 - r * Math.sin(ang(i));

  cx.clearRect(0, 0, W, H);

  // Grade
  [0.25, 0.5, 0.75, 1].forEach((r) => {
    cx.beginPath();
    for (let i = 0; i < N; i++) {
      i === 0 ? cx.moveTo(px(i, R * r), py(i, R * r))
              : cx.lineTo(px(i, R * r), py(i, R * r));
    }
    cx.closePath(); cx.strokeStyle = "#E5E7EB"; cx.lineWidth = 0.8; cx.stroke();
  });

  // Eixos e labels
  for (let i = 0; i < N; i++) {
    cx.beginPath(); cx.moveTo(cx0, cy0);
    cx.lineTo(px(i, R), py(i, R));
    cx.strokeStyle = "#D1D5DB"; cx.lineWidth = 0.8; cx.stroke();
    cx.fillStyle = "#374151"; cx.font = "bold 10px system-ui"; cx.textAlign = "center";
    cx.fillText(crit[i], px(i, R + 16), py(i, R + 16) + 3);
  }

  // Séries
  top5.forEach((item, k) => {
    const vals = campos.map((c) => item.valores?.[c] ?? 0);
    cx.beginPath();
    for (let i = 0; i < N; i++) {
      const r = vals[i] * R;
      i === 0 ? cx.moveTo(px(i, r), py(i, r)) : cx.lineTo(px(i, r), py(i, r));
    }
    cx.closePath();
    cx.strokeStyle = cores5[k]; cx.lineWidth = 2; cx.stroke();
    cx.fillStyle = cores5[k] + "18"; cx.fill();
  });

  // Legenda
  cx.font = "9px system-ui";
  top5.forEach((item, k) => {
    const ly = H - 78 + k * 14;
    cx.fillStyle = cores5[k];
    cx.fillRect(8, ly - 7, 9, 9);
    cx.fillStyle = "#374151"; cx.textAlign = "left";
    const nm = item.nome.length > 22 ? item.nome.slice(0, 21) + "…" : item.nome;
    cx.fillText(nm, 22, ly);
  });
}

// ══════════════════════════════════════════════════
// G5 — Scatter
// ══════════════════════════════════════════════════
function desenharG5() {
  const cx = initCanvas(c5, 300); if (!cx) return;
  const W = c5.value.width; const H = c5.value.height;
  const scatter = dadosGraficos.scatter;
  if (!scatter || !Object.keys(scatter).length) return;
  const PL = 46; const PR = 12; const PT = 16; const PB = 28;

  // Ranges
  const allS = Object.values(scatter).flat().map((p) => p.score);
  const allF = Object.values(scatter).flat().map((p) => p.focos);
  if (!allS.length) return;
  const smin = Math.min(...allS); const smax = Math.max(...allS);
  const fmax = Math.max(...allF, 1);

  cx.clearRect(0, 0, W, H);

  const xOf = (f) => PL + (Math.log10(f + 1) / Math.log10(fmax + 1)) * (W - PL - PR);
  const yOf = (s) => PT + (1 - (s - smin) / ((smax - smin) || 1)) * (H - PT - PB);

  // Eixos
  cx.strokeStyle = "#E5E7EB"; cx.lineWidth = 1;
  cx.beginPath(); cx.moveTo(PL, PT); cx.lineTo(PL, H - PB);
  cx.lineTo(W - PR, H - PB); cx.stroke();

  // Pontos
  const ORDEM = ["BAIXO", "MEDIO", "ALTO", "CRITICO"];
  ORDEM.forEach((nivel) => {
    const pontos = scatter[nivel] || [];
    pontos.forEach((p) => {
      cx.beginPath();
      cx.arc(xOf(p.focos), yOf(p.score), 3.5, 0, Math.PI * 2);
      cx.fillStyle = (COR_NIVEL[nivel] || "#999") + "99";
      cx.fill();
    });
  });

  // Limites horizontais
  const limites = dadosGraficos.scores_por_nivel;
  if (limites?.CRITICO?.min) {
    [
      { s: limites.CRITICO.min, cor: P.verm, lbl: "Crítico" },
      { s: limites.ALTO.min,    cor: P.lrj,  lbl: "Alto"    },
    ].forEach(({ s, cor, lbl }) => {
      cx.setLineDash([3, 3]); cx.strokeStyle = cor; cx.lineWidth = 1;
      cx.beginPath(); cx.moveTo(PL, yOf(s)); cx.lineTo(W - PR, yOf(s)); cx.stroke();
      cx.setLineDash([]);
      cx.fillStyle = cor; cx.font = "9px system-ui"; cx.textAlign = "right";
      cx.fillText(lbl, W - PR - 2, yOf(s) - 3);
    });
  }

  // Labels Y
  cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF"; cx.textAlign = "right";
  [smin, (smin + smax) / 2, smax].forEach((s) => {
    cx.fillText(s.toFixed(2), PL - 3, yOf(s) + 3);
  });
  cx.textAlign = "center";
  cx.fillText("Focos (log)", W / 2, H - 4);

  // Legenda
  let lx = PL;
  ORDEM.slice().reverse().forEach((nivel) => {
    cx.fillStyle = COR_NIVEL[nivel];
    cx.fillRect(lx, PT + 2, 8, 8);
    cx.fillStyle = "#374151"; cx.font = "9px system-ui"; cx.textAlign = "left";
    cx.fillText(nivel.charAt(0) + nivel.slice(1).toLowerCase(), lx + 11, PT + 10);
    lx += 56;
  });
}

// ══════════════════════════════════════════════════
// G6 — Histograma com toggle Gauss
// ══════════════════════════════════════════════════
function desenharG6() {
  const cx = initCanvas(c6, 260); if (!cx) return;
  const W = c6.value.width; const H = c6.value.height;
  const snivel = dadosGraficos.scores_por_nivel;
  if (!snivel || !Object.keys(snivel).length) return;
  const PL = 46; const PR = 12; const PT = 24; const PB = 28;

  const NIVEIS = ["CRITICO", "ALTO", "MEDIO", "BAIXO"];
  const BINS = 40;

  // Coleta todos os scores
  const allScores = NIVEIS.flatMap((n) => snivel[n]?.scores || []);
  if (!allScores.length) return;
  const smin = Math.min(...allScores); const smax = Math.max(...allScores);
  const bW   = (smax - smin) / BINS;

  // Histograma empilhado por nível
  const hist = Array.from({ length: BINS }, () => ({}));
  NIVEIS.forEach((nivel) => {
    (snivel[nivel]?.scores || []).forEach((s) => {
      const b = Math.min(BINS - 1, Math.max(0, Math.floor((s - smin) / bW)));
      hist[b][nivel] = (hist[b][nivel] || 0) + 1;
    });
  });
  const maxCount = Math.max(...hist.map((b) => Object.values(b).reduce((a, v) => a + v, 0)));

  cx.clearRect(0, 0, W, H);
  const drawW = W - PL - PR;
  const bPx   = drawW / BINS;

  const xOf = (i) => PL + i * bPx;
  const yOf = (v) => PT + (1 - v / maxCount) * (H - PT - PB);

  // Barras empilhadas
  hist.forEach((bin, i) => {
    let base = H - PB;
    NIVEIS.forEach((nivel) => {
      const cnt = bin[nivel] || 0;
      if (!cnt) return;
      const bH = (cnt / maxCount) * (H - PT - PB);
      cx.fillStyle = (COR_NIVEL[nivel] || P.cinza) + "CC";
      cx.fillRect(xOf(i) + 0.5, base - bH, bPx - 1, bH);
      base -= bH;
    });
  });

  // Curva Gauss por nível (toggle)
  if (mostrarGauss.value) {
    NIVEIS.forEach((nivel) => {
      const d = snivel[nivel];
      if (!d?.scores?.length) return;
      const mu  = d.media;
      const std = Math.max(
        0.001,
        Math.sqrt(d.scores.reduce((s, v) => s + (v - mu) ** 2, 0) / d.scores.length)
      );
      const n   = d.scores.length;
      const amp = (n / (maxCount * std * Math.sqrt(2 * Math.PI))) * bW;

      cx.beginPath();
      for (let px_ = PL; px_ <= W - PR; px_ += 1) {
        const s  = smin + ((px_ - PL) / drawW) * (smax - smin);
        const gv = amp * Math.exp(-0.5 * ((s - mu) / std) ** 2);
        const gy = yOf(gv);
        px_ === PL ? cx.moveTo(px_, gy) : cx.lineTo(px_, gy);
      }
      cx.strokeStyle = COR_NIVEL[nivel]; cx.lineWidth = 2.5;
      cx.setLineDash([]);
      cx.stroke();
    });
  }

  // Linhas de percentil
  NIVEIS.slice(0, 3).forEach((nivel, i) => {
    const s  = snivel[nivel]?.min;
    if (s == null) return;
    const lx = PL + ((s - smin) / (smax - smin)) * drawW;
    cx.setLineDash([3, 3]);
    cx.strokeStyle = COR_NIVEL[nivel]; cx.lineWidth = 1;
    cx.beginPath(); cx.moveTo(lx, PT); cx.lineTo(lx, H - PB); cx.stroke();
    cx.setLineDash([]);
  });

  // Labels X
  cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF"; cx.textAlign = "center";
  [smin, (smin + smax) / 2, smax].forEach((s) => {
    const lx = PL + ((s - smin) / (smax - smin)) * drawW;
    cx.fillText(s.toFixed(2), lx, H - PB + 12);
  });
  cx.fillText("Score TOPSIS (CCᵢ)", W / 2, H - 4);

  // Legenda
  let lx = PL;
  NIVEIS.forEach((nivel) => {
    cx.fillStyle = COR_NIVEL[nivel];
    cx.fillRect(lx, PT - 16, 8, 8);
    cx.fillStyle = "#374151"; cx.font = "9px system-ui"; cx.textAlign = "left";
    const lbl = `${nivel.charAt(0)}${nivel.slice(1).toLowerCase()} (${snivel[nivel]?.n ?? 0})`;
    cx.fillText(lbl, lx + 11, PT - 9);
    lx += cx.measureText(lbl).width + 24;
  });
}

function redesenharG6() { desenharG6(); }

// ══════════════════════════════════════════════════
// G7 — Boxplot manual
// ══════════════════════════════════════════════════
function desenharG7() {
  const cx = initCanvas(c7, 260); if (!cx) return;
  const W = c7.value.width; const H = c7.value.height;
  const snivel = dadosGraficos.scores_por_nivel;
  if (!snivel || !Object.keys(snivel).length) return;
  const PL = 46; const PR = 16; const PT = 24; const PB = 28;

  const NIVEIS = ["CRITICO", "ALTO", "MEDIO", "BAIXO"];
  const allScores = NIVEIS.flatMap((n) => snivel[n]?.scores || []);
  if (!allScores.length) return;
  const smin = Math.min(...allScores); const smax = Math.max(...allScores);

  cx.clearRect(0, 0, W, H);
  const yOf = (s) => PT + (1 - (s - smin) / ((smax - smin) || 1)) * (H - PT - PB);

  const step = (W - PL - PR) / NIVEIS.length;

  NIVEIS.forEach((nivel, i) => {
    const scores = (snivel[nivel]?.scores || []).slice().sort((a, b) => a - b);
    if (!scores.length) return;
    const n   = scores.length;
    const q1  = scores[Math.floor(n * 0.25)];
    const q2  = scores[Math.floor(n * 0.50)];
    const q3  = scores[Math.floor(n * 0.75)];
    const iqr = q3 - q1;
    const wlo = Math.max(scores[0], q1 - 1.5 * iqr);
    const whi = Math.min(scores[n - 1], q3 + 1.5 * iqr);
    const cx0 = PL + i * step + step / 2;
    const bw  = step * 0.4;
    const cor = COR_NIVEL[nivel];

    // Caixa IQR
    cx.fillStyle = cor + "CC";
    cx.fillRect(cx0 - bw / 2, yOf(q3), bw, yOf(q1) - yOf(q3));
    cx.strokeStyle = cor; cx.lineWidth = 1.5;
    cx.strokeRect(cx0 - bw / 2, yOf(q3), bw, yOf(q1) - yOf(q3));

    // Mediana
    cx.beginPath(); cx.moveTo(cx0 - bw / 2, yOf(q2));
    cx.lineTo(cx0 + bw / 2, yOf(q2));
    cx.strokeStyle = P.bco; cx.lineWidth = 2.5; cx.stroke();

    // Whiskers
    cx.strokeStyle = cor; cx.lineWidth = 1.2;
    [[wlo, q1], [q3, whi]].forEach(([a, b]) => {
      cx.beginPath(); cx.moveTo(cx0, yOf(a)); cx.lineTo(cx0, yOf(b)); cx.stroke();
      cx.beginPath(); cx.moveTo(cx0 - bw * 0.25, yOf(a));
      cx.lineTo(cx0 + bw * 0.25, yOf(a)); cx.stroke();
    });

    // Outliers
    scores.forEach((s) => {
      if (s < wlo || s > whi) {
        cx.beginPath(); cx.arc(cx0, yOf(s), 2.5, 0, Math.PI * 2);
        cx.fillStyle = cor + "88"; cx.fill();
      }
    });

    // Valor mediana
    cx.fillStyle = "#374151"; cx.font = "bold 9px system-ui"; cx.textAlign = "center";
    cx.fillText(q2.toFixed(3), cx0, yOf(q1) + 16);

    // Label X
    cx.fillStyle = "#6B7280"; cx.font = "9px system-ui";
    const lbl = nivel.charAt(0) + nivel.slice(1).toLowerCase();
    cx.fillText(lbl, cx0, H - PB + 14);
  });

  // Labels Y
  cx.textAlign = "right"; cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF";
  [smin, (smin + smax) / 2, smax].forEach((s) => {
    cx.fillText(s.toFixed(2), PL - 4, yOf(s) + 3);
  });
  cx.fillStyle = "#6B7280"; cx.font = "bold 9px system-ui"; cx.textAlign = "center";
  cx.fillText("Score TOPSIS (CCᵢ)", W / 2, H - 4);
}

// ══════════════════════════════════════════════════
// Carregamento de dados dinâmicos
// ══════════════════════════════════════════════════
async function carregarDados() {
  carregando.value = true;
  try {
    const params = store.filtrosAtivos ? store.filtrosAtivos() : {};
    const resp   = await api.get("/graficos-dados/", { params });
    const d      = resp.data;

    dadosGraficos.por_bioma         = d.por_bioma         || [];
    dadosGraficos.serie_temporal    = d.serie_temporal     || [];
    dadosGraficos.top10             = d.top10              || [];
    dadosGraficos.top5_radar        = d.top5_radar         || [];
    dadosGraficos.scores_por_nivel  = d.scores_por_nivel   || {};
    dadosGraficos.scatter           = d.scatter            || {};
  } catch (e) {
    console.error("Erro ao carregar dados dos gráficos:", e);
  } finally {
    carregando.value = false;
    requestAnimationFrame(desenharTudo);
  }
}

function desenharTudo() {
  desenharG1(); desenharG2(); desenharG3(); desenharG4();
  desenharG5(); desenharG6(); desenharG7();
}

// Recarrega quando TOPSIS é executado ou filtros mudam
watch(() => store.rankingAtualizado, () => carregarDados());
watch(() => store.filtros, () => carregarDados(), { deep: true });

onMounted(() => carregarDados());
</script>

<style scoped>
.graficos-page {
  padding: 20px 24px;
  overflow-y: auto;
  height: 100%;
}

/* Header */
.page-header {
  display: flex; align-items: flex-start;
  justify-content: space-between; flex-wrap: wrap;
  gap: 12px; margin-bottom: 20px;
}
.page-titulo { font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 3px; }
.page-sub    { font-size: 12px; color: #6B7280; }
.header-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.badge { font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 500; }
.badge.azul  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge.verde { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.badge.cinza { background: #F3F4F6; color: #6B7280; border: 1px solid #E5E7EB; }

/* Layout em linhas */
.linha {
  display: flex; gap: 16px; margin-bottom: 16px; align-items: stretch;
}
.card         { background: #fff; border-radius: 10px; padding: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.07);
                border: 1px solid #E5E7EB; min-width: 0; }
.card-medio   { flex: 1; }
.card-grande  { flex: 1.8; }
.card-full    { width: 100%; }

.card-header {
  display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap;
}
.card-titulo  { font-size: 13px; font-weight: 600; color: #111827; }
.card-badge   { font-size: 10px; padding: 2px 8px; background: #F3F4F6;
                color: #6B7280; border-radius: 999px; white-space: nowrap; }
.card-controles { display: flex; align-items: center; gap: 10px; }
.card-nota    { font-size: 10px; color: #9CA3AF; margin-top: 8px; font-style: italic; }
.canvas       { width: 100% !important; display: block; height: 220px; }

/* Toggle Gauss */
.toggle { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.toggle input { display: none; }
.toggle-slider {
  width: 32px; height: 18px; background: #D1D5DB; border-radius: 999px;
  position: relative; transition: background 0.2s; flex-shrink: 0;
}
.toggle-slider::after {
  content: ""; position: absolute; width: 14px; height: 14px;
  background: white; border-radius: 50%; top: 2px; left: 2px;
  transition: left 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}
.toggle input:checked + .toggle-slider { background: #1D4ED8; }
.toggle input:checked + .toggle-slider::after { left: 16px; }
.toggle-label { font-size: 11px; color: #374151; font-weight: 500; }

/* Tabela */
.tabela-card { margin-bottom: 24px; }
.tabela-wrap { overflow-x: auto; margin-bottom: 8px; }
.tabela { width: 100%; border-collapse: collapse; font-size: 12px; }
.tabela th {
  text-align: left; padding: 8px 10px; background: #F9FAFB;
  color: #6B7280; font-weight: 600; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid #E5E7EB; white-space: nowrap;
}
.tabela td    { padding: 9px 10px; border-bottom: 1px solid #F3F4F6; color: #374151; }
.tabela tr:hover td { background: #F9FAFB; }
.rank-cell  { font-weight: 700; color: #9CA3AF; }
.nome-cell  { font-weight: 500; color: #111827; max-width: 220px;
              overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.score-cell { font-weight: 700; color: #1D4ED8; font-variant-numeric: tabular-nums; }
.num-cell   { font-variant-numeric: tabular-nums; color: #6B7280; }
.vazio-cell { text-align: center; color: #9CA3AF; padding: 24px; font-style: italic; }

.nivel-badge { font-size: 9px; font-weight: 600; padding: 2px 7px;
               border-radius: 999px; text-transform: uppercase; }
.nivel-critico { background: #FEF2F2; color: #B91C1C; }
.nivel-alto    { background: #FFF7ED; color: #C2410C; }
.nivel-medio   { background: #FEFCE8; color: #92400E; }
.nivel-baixo   { background: #F0FDF4; color: #15803D; }

.tabela-ref { font-size: 10px; color: #9CA3AF; font-style: italic; }

/* Responsivo */
@media (max-width: 860px) {
  .linha { flex-direction: column; }
  .card-grande, .card-medio { flex: unset; width: 100%; }
}
</style>
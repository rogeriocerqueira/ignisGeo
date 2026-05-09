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
        <div class="canvas-wrap" style="position:relative;">
          <canvas ref="c2" class="canvas"
            @mousemove="g2MouseMove"
            @mouseleave="g2MouseLeave"
            style="cursor:crosshair;">
          </canvas>
          <div v-if="g2Tooltip.visible" class="g2-tooltip"
            :style="{ left: g2Tooltip.x + 'px', top: g2Tooltip.y + 'px' }">
            <div class="g2-tt-mes">{{ g2Tooltip.mes }}</div>
            <div class="g2-tt-focos">
              {{ g2Tooltip.focos.toLocaleString("pt-BR") }} focos
            </div>
            <div class="g2-tt-frp">FRP médio: {{ g2Tooltip.frp }} MW</div>
          </div>
        </div>
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
        <canvas ref="c3" class="canvas" style="height:340px"></canvas>
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
              <span class="toggle-label">Curva Normal (dist. total)</span>
            </label>
            <span class="card-badge">Histograma</span>
          </div>
        </div>
        <canvas ref="c6" class="canvas" style="height:260px"></canvas>
        <p class="card-nota">
          Histograma de <strong>densidade</strong> normalizado ·
          Crítico: {{ niv.CRITICO?.n ?? 0 }} ·
          Alto: {{ niv.ALTO?.n ?? 0 }} ·
          Médio: {{ niv.MEDIO?.n ?? 0 }} ·
          Baixo: {{ niv.BAIXO?.n ?? 0 }} ·
          Curva Normal única sobre todos os scores (μ, σ)
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

    <!-- Linha 5: Matriz de Correlação + Interpretação -->
    <div class="linha">
      <div class="card card-heatmap">
        <div class="card-header">
          <span class="card-titulo">Matriz de Correlação entre Critérios TOPSIS</span>
          <div class="card-controles">
            <div class="tipo-corr-toggle">
              <button
                :class="['tipo-btn', { ativo: tipoCorr === 'pearson' }]"
                @click="tipoCorr = 'pearson'; redesenharG8()"
              >Pearson (r)</button>
              <button
                :class="['tipo-btn', { ativo: tipoCorr === 'spearman' }]"
                @click="tipoCorr = 'spearman'; redesenharG8()"
              >Spearman (ρ)</button>
            </div>
            <span class="card-badge">5 × 5</span>
          </div>
        </div>
        <canvas ref="c8" class="canvas" style="height:340px"></canvas>
        <p class="card-nota">
          N = {{ dadosCorr.n?.toLocaleString("pt-BR") || "—" }} áreas ·
          *** p &lt; 0,001 · ** p &lt; 0,01 · * p &lt; 0,05 ·
          Ref.: Cohen (1988) — |r| ≥ 0,5 grande
        </p>
      </div>

      <div class="card card-interp">
        <div class="card-header">
          <span class="card-titulo">Independência dos Critérios</span>
          <span class="card-badge">MCDM</span>
        </div>
        <div class="interp-corpo" v-if="dadosCorr.n">
          <div class="interp-badge" :class="indepClass">
            <span class="interp-icone">{{ indepIcone }}</span>
            <span class="interp-texto">{{ indepLabel }}</span>
          </div>
          <p class="interp-desc">
            Correlação média entre critérios:
            <strong>|r̄| = {{ corrMediaAbs }}</strong>
          </p>
          <p class="interp-desc">
            Em MCDM, critérios correlacionados duplicam peso implicitamente.
            Valores |r| &lt; 0,5 indicam contribuição independente ao ranking.
          </p>
          <ul class="interp-lista">
            <li v-for="par in parDestaque" :key="par.label" :class="par.cls">
              <strong>{{ par.label }}:</strong> {{ par.valor }}
              <span class="interp-star">{{ par.star }}</span>
            </li>
          </ul>
          <div class="interp-ref">
            <p>Referências:</p>
            <p>Chen, C.T. (2000). <em>Fuzzy Sets and Systems</em>, 114(1), 1–9.</p>
            <p>Cohen, J. (1988). <em>Statistical Power Analysis</em>. 2ª ed.</p>
          </div>
        </div>
        <div v-else class="interp-vazio">
          Carregando análise de correlação...
        </div>
      </div>
    </div>
    <div class="card card-full tabela-card">
      <div class="card-header">
        <span class="card-titulo">Tabela de Resultados — Top 10 Municípios</span>
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="card-badge">Dados reais do banco</span>
          <span class="tabela-pag-info" v-if="dadosGraficos.top10?.length">
            {{ paginaTabela }}/{{ totalPaginasTabela }}
          </span>
        </div>
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
            <tr v-for="a in top10Paginado" :key="a.ranking">
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
      <!-- Controles de paginação -->
      <div class="tabela-pag-controles" v-if="totalPaginasTabela > 1">
        <button class="pag-btn" :disabled="paginaTabela <= 1" @click="paginaTabela--">← Anterior</button>
        <button
          v-for="p in totalPaginasTabela" :key="p"
          class="pag-btn"
          :class="{ 'pag-btn-ativo': p === paginaTabela }"
          @click="paginaTabela = p"
        >{{ p }}</button>
        <button class="pag-btn" :disabled="paginaTabela >= totalPaginasTabela" @click="paginaTabela++">Próxima →</button>
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

// Paginação da tabela
const paginaTabela  = ref(1);
const TPP           = 5; // itens por página

// Heatmap de correlação
const c8       = ref(null);
const tipoCorr = ref("pearson");   // "pearson" | "spearman"
const dadosCorr = reactive({ rotulos: [], pearson: [], spearman: [], pvalores: [], n: 0 });
const c7 = ref(null);

const carregando    = ref(false);
const mostrarGauss  = ref(false);
const dadosGraficos = reactive({
  por_bioma: [], serie_temporal: [], top10: [],
  top5_radar: [], scores_por_nivel: {}, scatter: {},
});

// Tooltip da série temporal (G2)
const g2Tooltip = reactive({
  visible: false, x: 0, y: 0,
  mes: "", focos: 0, frp: "—",
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
// Paginação da tabela
const totalPaginasTabela = computed(() =>
  Math.ceil((dadosGraficos.top10?.length || 0) / TPP)
);
const top10Paginado = computed(() => {
  const inicio = (paginaTabela.value - 1) * TPP;
  return (dadosGraficos.top10 || []).slice(inicio, inicio + TPP);
});

// ── Interpretação automática da matriz de correlação ──
const matrizAtiva = computed(() =>
  tipoCorr.value === "pearson" ? dadosCorr.pearson : dadosCorr.spearman
);
const corrMediaAbs = computed(() => {
  const mat = matrizAtiva.value;
  if (!mat.length) return "—";
  const K = mat.length;
  let soma = 0, cnt = 0;
  for (let i = 0; i < K; i++)
    for (let j = i + 1; j < K; j++) {
      soma += Math.abs(mat[i][j]); cnt++;
    }
  return cnt ? (soma / cnt).toFixed(3) : "—";
});
const indepClass = computed(() => {
  const v = parseFloat(corrMediaAbs.value);
  if (isNaN(v)) return "";
  if (v < 0.3)  return "badge-verde";
  if (v < 0.5)  return "badge-amar";
  return "badge-verm";
});
const indepIcone = computed(() => {
  const v = parseFloat(corrMediaAbs.value);
  if (isNaN(v)) return "?";
  if (v < 0.3)  return "✓";
  if (v < 0.5)  return "~";
  return "⚠";
});
const indepLabel = computed(() => {
  const v = parseFloat(corrMediaAbs.value);
  if (isNaN(v)) return "Sem dados";
  if (v < 0.3)  return "Critérios Independentes";
  if (v < 0.5)  return "Baixa Redundância";
  return "Redundância Moderada — revisar pesos";
});
const parDestaque = computed(() => {
  const mat = matrizAtiva.value;
  const pv  = dadosCorr.pvalores;
  const rot = dadosCorr.rotulos;
  if (!mat.length || !rot.length) return [];
  const K    = mat.length;
  const pares = [];
  for (let i = 0; i < K; i++)
    for (let j = i + 1; j < K; j++) {
      const r  = mat[i][j];
      const p  = pv[i]?.[j] ?? 1;
      const star = p < 0.001 ? "***" : p < 0.01 ? "**" : p < 0.05 ? "*" : "";
      pares.push({
        label: `${rot[i].split("—")[0].trim()} × ${rot[j].split("—")[0].trim()}`,
        valor: r.toFixed(3),
        abs:   Math.abs(r),
        star,
        cls:   Math.abs(r) >= 0.5 ? "par-alto" : Math.abs(r) >= 0.3 ? "par-medio" : "par-baixo",
      });
    }
  // Top 4 por |r| decrescente
  return pares.sort((a, b) => b.abs - a.abs).slice(0, 4);
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
// G2 — Tooltip interativo
// ══════════════════════════════════════════════════
const MESES_BR_FULL = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                       "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];

function g2MouseLeave() {
  g2Tooltip.visible = false;
  // Redesenha sem o crosshair
  desenharG2();
}

function g2MouseMove(evt) {
  const serie = dadosGraficos.serie_temporal;
  if (!serie.length || !c2.value) return;

  const rect  = c2.value.getBoundingClientRect();
  const mouseX = evt.clientX - rect.left;
  const mouseY = evt.clientY - rect.top;

  // Reproduz os mesmos parâmetros de layout do desenharG2
  const W = c2.value.width;
  const H = c2.value.height;
  const PL = 68; const PR = 16; const PT = 24; const PB = 44;
  const drawW = W - PL - PR;
  const n     = serie.length;

  // Encontra o ponto mais próximo no eixo X
  const xOf = (i) => PL + (i / Math.max(n - 1, 1)) * drawW;
  let idxMin = 0;
  let distMin = Infinity;
  serie.forEach((_, i) => {
    const d = Math.abs(xOf(i) - mouseX);
    if (d < distMin) { distMin = d; idxMin = i; }
  });

  // Só mostra tooltip se o cursor está dentro da área do gráfico
  if (mouseX < PL || mouseX > W - PR || mouseY < PT || mouseY > H - PB) {
    g2Tooltip.visible = false;
    desenharG2();
    return;
  }

  const ponto  = serie[idxMin];
  const [ano, mes] = ponto.mes.split("-");
  const nomeMes = MESES_BR_FULL[parseInt(mes, 10) - 1];

  g2Tooltip.mes   = `${nomeMes} de ${ano}`;
  g2Tooltip.focos = ponto.focos;
  g2Tooltip.frp   = Number(ponto.frp_medio || 0).toFixed(1);

  // Posição do tooltip: à direita do ponto se couber, senão à esquerda
  const TW = 168; // largura estimada do tooltip
  const px  = xOf(idxMin);
  g2Tooltip.x = (px + TW + 12 < rect.width) ? px + 12 : px - TW - 12;
  g2Tooltip.y = Math.max(8, mouseY - 40);
  g2Tooltip.visible = true;

  // Redesenha com o crosshair no ponto
  desenharG2(idxMin);
}

// ══════════════════════════════════════════════════
// G2 — Série temporal
// ══════════════════════════════════════════════════
function desenharG2(idxAtivo = -1) {
  const cx = initCanvas(c2, 240); if (!cx) return;
  const W = c2.value.width; const H = c2.value.height;
  // PL maior p/ rótulo Y rotacionado; PB maior p/ rótulo X + título
  const PL = 68; const PR = 16; const PT = 24; const PB = 44;
  const serie = dadosGraficos.serie_temporal;
  if (!serie.length) return;
  const vals  = serie.map((s) => s.focos);
  const maxV  = Math.max(...vals);
  const n     = serie.length;

  cx.clearRect(0, 0, W, H);

  const drawW = W - PL - PR;
  const drawH = H - PT - PB;
  const xOf   = (i) => PL + (i / Math.max(n - 1, 1)) * drawW;
  const yOf   = (v) => PT + (1 - v / maxV) * drawH;

  // Grade horizontal (4 linhas) — padrão científico
  cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF"; cx.textAlign = "right";
  [0, 0.25, 0.5, 0.75, 1].forEach((frac) => {
    const v  = Math.round(maxV * frac);
    const y  = yOf(v);
    cx.strokeStyle = frac === 0 ? "#D1D5DB" : "#F3F4F6";
    cx.lineWidth   = frac === 0 ? 1 : 0.7;
    cx.setLineDash(frac === 0 ? [] : [3, 3]);
    cx.beginPath(); cx.moveTo(PL, y); cx.lineTo(W - PR, y); cx.stroke();
    cx.setLineDash([]);
    const lbl = v >= 1000 ? `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)}k` : v;
    cx.fillText(lbl, PL - 6, y + 3);
  });

  // Eixo X — linha base
  cx.strokeStyle = "#D1D5DB"; cx.lineWidth = 1;
  cx.beginPath(); cx.moveTo(PL, H - PB); cx.lineTo(W - PR, H - PB); cx.stroke();

  // Área
  cx.beginPath();
  cx.moveTo(xOf(0), yOf(vals[0]));
  vals.forEach((v, i) => cx.lineTo(xOf(i), yOf(v)));
  cx.lineTo(xOf(n - 1), H - PB); cx.lineTo(xOf(0), H - PB); cx.closePath();
  cx.fillStyle = "rgba(230,81,0,0.10)"; cx.fill();

  // Linha
  cx.beginPath(); cx.moveTo(xOf(0), yOf(vals[0]));
  vals.forEach((v, i) => cx.lineTo(xOf(i), yOf(v)));
  cx.strokeStyle = P.lrj; cx.lineWidth = 2.5; cx.setLineDash([]); cx.stroke();

  // Pontos
  vals.forEach((v, i) => {
    cx.beginPath(); cx.arc(xOf(i), yOf(v), 3, 0, Math.PI * 2);
    cx.fillStyle = P.lrj; cx.fill();
  });

  // Pico
  const idxP = vals.indexOf(maxV);
  cx.fillStyle = P.verm; cx.font = "bold 9px system-ui"; cx.textAlign = "center";
  cx.fillText(`▲ ${maxV.toLocaleString("pt-BR")}`, xOf(idxP), yOf(maxV) - 8);

  // ── Labels X — formato brasileiro + ticks inteligentes ──────────
  // Converte "YYYY-MM" para "Mmm/AA" (ex: "2025-09" → "Set/25")
  const MESES_BR = ["Jan","Fev","Mar","Abr","Mai","Jun",
                    "Jul","Ago","Set","Out","Nov","Dez"];
  const fmtMes = (mesStr) => {
    const [ano, mes] = mesStr.split("-");
    return `${MESES_BR[parseInt(mes, 10) - 1]}/${ano.slice(2)}`;
  };

  // Densidade adaptativa: mostra label a cada N meses
  // para que os textos nunca se sobreponham
  // Largura estimada de cada label: ~38px; espaço disponível: drawW
  const labelW  = 40;
  const maxLabels = Math.max(1, Math.floor(drawW / labelW));
  const step  = Math.ceil(n / maxLabels);

  cx.font = "9px system-ui"; cx.fillStyle = "#4B5563"; cx.textAlign = "center";

  serie.forEach((s, i) => {
    const x = xOf(i);
    // Traço de tick em todos os meses
    cx.strokeStyle = "#D1D5DB"; cx.lineWidth = 0.8;
    cx.beginPath(); cx.moveTo(x, H - PB); cx.lineTo(x, H - PB + 4); cx.stroke();

    // Label apenas nos meses selecionados pela densidade
    if (i % step === 0 || i === n - 1) {
      // Destaque para janeiro de cada ano (início de ano)
      const isJan = s.mes.endsWith("-01");
      if (isJan) {
        cx.font = "bold 9px system-ui";
        cx.fillStyle = "#1F2937";
      } else {
        cx.font = "9px system-ui";
        cx.fillStyle = "#4B5563";
      }
      cx.fillText(fmtMes(s.mes), x, H - PB + 14);

      // Linha vertical tracejada leve nos Janeiros (marca virada de ano)
      if (isJan && i > 0) {
        cx.save();
        cx.strokeStyle = "#D1D5DB"; cx.lineWidth = 0.6;
        cx.setLineDash([2, 4]);
        cx.beginPath(); cx.moveTo(x, PT + 4); cx.lineTo(x, H - PB); cx.stroke();
        cx.setLineDash([]);
        cx.restore();
      }
    }
  });

  // Título eixo X
  cx.font = "bold 10px system-ui"; cx.fillStyle = "#374151"; cx.textAlign = "center";
  cx.fillText("Mês", W / 2, H - 4);

  // Título eixo Y — rotacionado 90°
  cx.save();
  cx.translate(14, PT + drawH / 2);
  cx.rotate(-Math.PI / 2);
  cx.font = "bold 10px system-ui"; cx.fillStyle = "#374151"; cx.textAlign = "center";
  cx.fillText("Nº de Focos", 0, 0);
  cx.restore();

  // ── Crosshair e ponto destacado (tooltip) ──────────────────────
  if (idxAtivo >= 0 && idxAtivo < n) {
    const xA = xOf(idxAtivo);
    const yA = yOf(vals[idxAtivo]);

    // Linha vertical tracejada
    cx.save();
    cx.strokeStyle = "#374151"; cx.lineWidth = 1;
    cx.setLineDash([4, 4]);
    cx.beginPath(); cx.moveTo(xA, PT); cx.lineTo(xA, H - PB); cx.stroke();
    cx.setLineDash([]);

    // Linha horizontal tracejada
    cx.strokeStyle = "#374151"; cx.lineWidth = 1;
    cx.setLineDash([4, 4]);
    cx.beginPath(); cx.moveTo(PL, yA); cx.lineTo(W - PR, yA); cx.stroke();
    cx.setLineDash([]);
    cx.restore();

    // Círculo destacado no ponto
    cx.beginPath();
    cx.arc(xA, yA, 6, 0, Math.PI * 2);
    cx.fillStyle = "#fff"; cx.fill();
    cx.strokeStyle = P.lrj; cx.lineWidth = 2.5; cx.stroke();

    cx.beginPath();
    cx.arc(xA, yA, 3, 0, Math.PI * 2);
    cx.fillStyle = P.lrj; cx.fill();
  }
}

// ══════════════════════════════════════════════════
// G3 — Top 10 barras horizontais
// ══════════════════════════════════════════════════
function desenharG3() {
  const cx = initCanvas(c3, 340); if (!cx) return;
  const W = c3.value.width; const H = c3.value.height;
  const dados = dadosGraficos.top10;
  if (!dados.length) return;

  // Colunas fixas (px): rank | nome | ← barra → | score
  const COL_RANK  = 32;   // largura da coluna de rank
  const COL_NOME  = 195;  // largura da coluna de nome
  const COL_SCORE = 72;   // largura da coluna de score (direita)
  const PT = 12; const PB = 12;
  const BAR_X = COL_RANK + COL_NOME;         // início das barras
  const BAR_W = W - BAR_X - COL_SCORE;       // largura da área de barras

  const n  = dados.length;
  const bH = Math.floor((H - PT - PB) / n) - 4;
  const scores  = dados.map((d) => d.score_topsis);
  const minS    = Math.min(...scores) * 0.98;
  const maxS    = Math.max(...scores) * 1.02;

  cx.clearRect(0, 0, W, H);

  // Cabeçalho de colunas
  cx.font = "bold 9px system-ui"; cx.fillStyle = "#9CA3AF";
  cx.textAlign = "center";
  cx.fillText("Rank",  COL_RANK / 2, PT - 2);
  cx.textAlign = "left";
  cx.fillText("Município / UF / Bioma", COL_RANK + 4, PT - 2);
  cx.textAlign = "left";
  cx.fillText("Score CCᵢ", BAR_X + BAR_W + 4, PT - 2);

  // Grade vertical (dentro da área de barras)
  [0.25, 0.5, 0.75, 1].forEach((frac) => {
    const x = BAR_X + frac * BAR_W;
    cx.strokeStyle = "#F3F4F6"; cx.lineWidth = 0.7;
    cx.setLineDash([2, 3]);
    cx.beginPath(); cx.moveTo(x, PT); cx.lineTo(x, H - PB); cx.stroke();
    cx.setLineDash([]);
  });

  [...dados].reverse().forEach((d, i) => {
    const y    = PT + i * Math.floor((H - PT - PB) / n);
    const bW   = BAR_W * Math.max(0, (d.score_topsis - minS) / (maxS - minS));
    const rank = n - i;
    const cor  = COR_NIVEL[d.nivel_risco] || P.cinza;

    // Faixa de fundo alternada (legibilidade)
    if (i % 2 === 0) {
      cx.fillStyle = "#F9FAFB";
      cx.fillRect(0, y, W, bH + 4);
    }

    // Col rank
    cx.fillStyle = rank <= 3 ? cor : "#9CA3AF";
    cx.font = "bold 10px system-ui"; cx.textAlign = "center";
    cx.fillText(`#${rank}`, COL_RANK / 2, y + bH / 2 + 4);

    // Col nome — clipping para não vazar
    cx.save();
    cx.beginPath();
    cx.rect(COL_RANK + 2, y - 2, COL_NOME - 4, bH + 6);
    cx.clip();
    const partes = d.nome.split("/");          // MUNICIPIO / UF / BIOMA
    const mun    = partes[0] || d.nome;
    const sub    = partes.slice(1).join("/");  // UF/BIOMA
    cx.fillStyle = "#111827"; cx.font = "bold 10px system-ui"; cx.textAlign = "left";
    cx.fillText(mun, COL_RANK + 6, y + bH / 2);
    if (sub) {
      cx.fillStyle = "#9CA3AF"; cx.font = "9px system-ui";
      cx.fillText(sub, COL_RANK + 6, y + bH / 2 + 11);
    }
    cx.restore();

    // Barra
    cx.fillStyle = cor + "CC";
    roundRect(cx, BAR_X + 2, y + 2, Math.max(bW - 4, 2), bH - 2, 3);
    cx.fill();
    // Contorno
    cx.strokeStyle = cor; cx.lineWidth = 1;
    roundRect(cx, BAR_X + 2, y + 2, Math.max(bW - 4, 2), bH - 2, 3);
    cx.stroke();

    // Col score
    cx.fillStyle = "#1D4ED8"; cx.font = "bold 10px system-ui"; cx.textAlign = "left";
    cx.fillText(Number(d.score_topsis).toFixed(4), BAR_X + BAR_W + 5, y + bH / 2 + 4);
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
// G6 — Histograma de densidade + Curva Normal única
// Correção estatística: Y em densidade (count/N·bW)
// para que histograma e curva compartilhem a mesma escala.
// Referência: Chen (2000) · distribuição de CCᵢ ∈ [0,1]
// ══════════════════════════════════════════════════
function desenharG6() {
  const cx = initCanvas(c6, 290); if (!cx) return;
  const W = c6.value.width; const H = c6.value.height;
  const snivel = dadosGraficos.scores_por_nivel;
  if (!snivel || !Object.keys(snivel).length) return;

  const PL = 62; const PR = 12; const PT = 32; const PB = 50;
  const drawW = W - PL - PR;
  const drawH = H - PT - PB;

  const NIVEIS = ["CRITICO", "ALTO", "MEDIO", "BAIXO"];
  const BINS   = 40;

  // ── 1. Coleta todos os scores e estatísticas globais ──
  const allScores = NIVEIS.flatMap((nv) => snivel[nv]?.scores || []);
  if (!allScores.length) return;
  const N    = allScores.length;
  const smin = Math.min(...allScores);
  const smax = Math.max(...allScores);
  const binW = (smax - smin) / BINS || 0.001;

  // μ e σ globais (todos os scores)
  const mu    = allScores.reduce((s, v) => s + v, 0) / N;
  const sigma = Math.max(
    0.001,
    Math.sqrt(allScores.reduce((s, v) => s + (v - mu) ** 2, 0) / N)
  );

  // ── 2. Histograma normalizado para DENSIDADE ──
  // density = count / (N × binWidth)  →  ∫ density dx ≈ 1
  const hist = Array.from({ length: BINS }, () => ({}));
  NIVEIS.forEach((nv) => {
    (snivel[nv]?.scores || []).forEach((s) => {
      const b = Math.min(BINS - 1, Math.max(0, Math.floor((s - smin) / binW)));
      hist[b][nv] = (hist[b][nv] || 0) + 1;
    });
  });
  const histDens = hist.map((bin) => {
    const byNv = {};
    NIVEIS.forEach((nv) => { byNv[nv] = (bin[nv] || 0) / (N * binW); });
    byNv._total = NIVEIS.reduce((a, nv) => a + byNv[nv], 0);
    return byNv;
  });

  // ── 3. Escala Y: max(histograma, gaussMax) × 1.15 ──
  const gaussPeak = 1 / (sigma * Math.sqrt(2 * Math.PI));
  const histPeak  = Math.max(...histDens.map((b) => b._total));
  const maxDens   = Math.max(gaussPeak, histPeak) * 1.15;

  cx.clearRect(0, 0, W, H);

  const xOf  = (s) => PL + ((s - smin) / (smax - smin)) * drawW;
  const xOfI = (i) => PL + (i / BINS) * drawW;
  const yOf  = (d) => PT + (1 - d / maxDens) * drawH;

  // ── 4. Região de destaque: cauda crítica (> limiar Crítico) ──
  const limiarCrit = snivel.CRITICO?.min;
  if (limiarCrit != null) {
    const x0 = xOf(limiarCrit);
    const grd = cx.createLinearGradient(x0, 0, W - PR, 0);
    grd.addColorStop(0, "rgba(183,28,28,0.06)");
    grd.addColorStop(1, "rgba(183,28,28,0.14)");
    cx.fillStyle = grd;
    cx.fillRect(x0, PT, W - PR - x0, drawH);
    // Rótulo "Região Crítica"
    cx.fillStyle = P.verm + "AA"; cx.font = "bold 9px system-ui";
    cx.textAlign = "center";
    cx.fillText("↑ Crítico", x0 + (W - PR - x0) / 2, PT + 14);
  }

  // ── 5. Gridlines horizontais ──
  cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF"; cx.textAlign = "right";
  const nTicks = 4;
  for (let t = 0; t <= nTicks; t++) {
    const d = (maxDens * t) / nTicks;
    const y = yOf(d);
    cx.strokeStyle = t === 0 ? "#D1D5DB" : "#F3F4F6";
    cx.lineWidth   = t === 0 ? 1 : 0.7;
    cx.setLineDash(t === 0 ? [] : [3, 3]);
    cx.beginPath(); cx.moveTo(PL, y); cx.lineTo(W - PR, y); cx.stroke();
    cx.setLineDash([]);
    cx.fillText(d.toFixed(1), PL - 4, y + 3);
  }

  // ── 6. Barras de densidade empilhadas por nível ──
  histDens.forEach((bin, i) => {
    let base = H - PB;
    const bPx = drawW / BINS;
    NIVEIS.forEach((nv) => {
      const d = bin[nv] || 0;
      if (!d) return;
      const bHpx = (d / maxDens) * drawH;
      cx.fillStyle = (COR_NIVEL[nv] || P.cinza) + "BB";
      cx.fillRect(xOfI(i) + 0.5, base - bHpx, bPx - 1, bHpx);
      base -= bHpx;
    });
  });

  // ── 7. Curva Normal ÚNICA — mesma escala Y de densidade ──
  if (mostrarGauss.value) {
    // Preenchimento abaixo da curva (área = 1)
    cx.beginPath();
    cx.moveTo(PL, H - PB);
    for (let px_ = PL; px_ <= W - PR; px_++) {
      const s  = smin + ((px_ - PL) / drawW) * (smax - smin);
      const d  = (1 / (sigma * Math.sqrt(2 * Math.PI))) *
                 Math.exp(-0.5 * ((s - mu) / sigma) ** 2);
      px_ === PL
        ? cx.lineTo(px_, yOf(d))
        : cx.lineTo(px_, yOf(d));
    }
    cx.lineTo(W - PR, H - PB); cx.closePath();
    cx.fillStyle = "rgba(31,41,55,0.06)"; cx.fill();

    // Linha da curva
    cx.beginPath();
    for (let px_ = PL; px_ <= W - PR; px_++) {
      const s = smin + ((px_ - PL) / drawW) * (smax - smin);
      const d = (1 / (sigma * Math.sqrt(2 * Math.PI))) *
                Math.exp(-0.5 * ((s - mu) / sigma) ** 2);
      px_ === PL ? cx.moveTo(px_, yOf(d)) : cx.lineTo(px_, yOf(d));
    }
    cx.strokeStyle = "#1F2937"; cx.lineWidth = 2.2;
    cx.setLineDash([]); cx.stroke();

    // Linha μ (média)
    const xMu = xOf(mu);
    cx.strokeStyle = "#1F2937"; cx.lineWidth = 1.2; cx.setLineDash([4, 3]);
    cx.beginPath(); cx.moveTo(xMu, PT + 4); cx.lineTo(xMu, H - PB); cx.stroke();
    cx.setLineDash([]);
    cx.fillStyle = "#1F2937"; cx.font = "bold 9px system-ui"; cx.textAlign = "center";
    cx.fillText(`μ=${mu.toFixed(3)}`, xMu, PT + 2);

    // Linhas μ±σ
    [mu - sigma, mu + sigma].forEach((s, side) => {
      if (s < smin || s > smax) return;
      const x_ = xOf(s);
      cx.strokeStyle = "#6B7280"; cx.lineWidth = 0.9; cx.setLineDash([2, 4]);
      cx.beginPath(); cx.moveTo(x_, PT + 18); cx.lineTo(x_, H - PB); cx.stroke();
      cx.setLineDash([]);
      cx.fillStyle = "#374151"; cx.font = "bold 9px system-ui"; cx.textAlign = "center";
      cx.fillText(side === 0 ? "μ−σ" : "μ+σ", x_, PT + 17);
    });
  }

  // ── 8. Eixo X — valores numéricos + título ──
  cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF"; cx.textAlign = "center";
  const nXTicks = 5;
  for (let t = 0; t <= nXTicks; t++) {
    const s  = smin + (t / nXTicks) * (smax - smin);
    const lx = xOf(s);
    cx.fillText(s.toFixed(2), lx, H - PB + 12);
  }
  cx.font = "bold 10px system-ui"; cx.fillStyle = "#374151";
  cx.fillText("Score TOPSIS  (CCᵢ)", W / 2, H - PB + 27);

  // ── 9. Título eixo Y — rotacionado 90° ──
  cx.save();
  cx.translate(13, PT + drawH / 2);
  cx.rotate(-Math.PI / 2);
  cx.font = "bold 10px system-ui"; cx.fillStyle = "#374151"; cx.textAlign = "center";
  cx.fillText("Densidade", 0, 0);
  cx.restore();

  // ── 10. Legenda no topo ──
  let lx = PL;
  NIVEIS.forEach((nv) => {
    cx.fillStyle = COR_NIVEL[nv];
    cx.fillRect(lx, PT - 20, 8, 8);
    cx.fillStyle = "#374151"; cx.font = "9px system-ui"; cx.textAlign = "left";
    const lbl = `${nv.charAt(0)}${nv.slice(1).toLowerCase()} (n=${snivel[nv]?.n ?? 0})`;
    cx.fillText(lbl, lx + 11, PT - 13);
    lx += cx.measureText(lbl).width + 26;
  });
  // Item legenda curva Normal
  if (mostrarGauss.value) {
    cx.strokeStyle = "#1F2937"; cx.lineWidth = 2;
    cx.beginPath(); cx.moveTo(lx, PT - 17); cx.lineTo(lx + 18, PT - 17); cx.stroke();
    cx.fillStyle = "#374151"; cx.font = "9px system-ui"; cx.textAlign = "left";
    cx.fillText(`N(${mu.toFixed(3)}, ${sigma.toFixed(3)})`, lx + 22, PT - 13);
  }
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
// G8 — Heatmap de correlação (Pearson / Spearman)
// Colormap divergente: azul→branco→vermelho
// Significância: teste t bilateral, df = N−2
// ══════════════════════════════════════════════════
function corrColor(r) {
  // r ∈ [-1, 1] → divergente azul→branco→vermelho
  const t = (r + 1) / 2;
  const lerp = (a, b, f) => Math.round(a + (b - a) * f);
  let rgb;
  if (t < 0.5) {
    const f = t * 2;
    // azul #1565C0 → branco #F5F5F5
    rgb = [lerp(21,245,f), lerp(101,245,f), lerp(192,245,f)];
  } else {
    const f = (t - 0.5) * 2;
    // branco #F5F5F5 → vermelho #B71C1C
    rgb = [lerp(245,183,f), lerp(245,28,f), lerp(245,28,f)];
  }
  return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
}

function starStr(pv) {
  if (pv < 0.001) return "***";
  if (pv < 0.01)  return "**";
  if (pv < 0.05)  return "*";
  return "";
}

function desenharG8() {
  const cx = initCanvas(c8, 340); if (!cx) return;
  const W = c8.value.width; const H = c8.value.height;
  const mat = tipoCorr.value === "pearson" ? dadosCorr.pearson : dadosCorr.spearman;
  const pv  = dadosCorr.pvalores;
  const rot = dadosCorr.rotulos;
  if (!mat.length || !rot.length) return;

  const K  = mat.length;
  // Margens: esquerda p/ rótulos Y, baixo p/ rótulos X + barra de cor
  const PL = 105; const PR = 16; const PT = 20; const PB = 80;
  const drawW = W - PL - PR;
  const drawH = H - PT - PB;
  const cell  = Math.min(drawW / K, drawH / K);
  // Centraliza a grade
  const offX  = PL + (drawW - cell * K) / 2;
  const offY  = PT + (drawH - cell * K) / 2;

  cx.clearRect(0, 0, W, H);

  // ── Células ──
  for (let i = 0; i < K; i++) {
    for (let j = 0; j < K; j++) {
      const r   = mat[i][j];
      const x0  = offX + j * cell;
      const y0  = offY + i * cell;

      // Fundo colorido
      cx.fillStyle = i === j ? "#374151" : corrColor(r);
      cx.fillRect(x0, y0, cell, cell);

      // Borda
      cx.strokeStyle = "#E5E7EB"; cx.lineWidth = 0.5;
      cx.strokeRect(x0, y0, cell, cell);

      if (i === j) {
        // Diagonal: sigla do critério
        cx.fillStyle = "#fff";
        cx.font = "bold 9px system-ui"; cx.textAlign = "center";
        const sigla = rot[i].split("—")[0].trim(); // "C1", "C2"...
        cx.fillText(sigla, x0 + cell / 2, y0 + cell / 2 + 3);
      } else {
        // Valor de r
        const textColor = Math.abs(r) > 0.5 ? "#fff" : "#1F2937";
        cx.fillStyle = textColor;
        cx.font = `${Math.abs(r) > 0.5 ? "bold " : ""}11px system-ui`;
        cx.textAlign = "center";
        cx.fillText(r.toFixed(2), x0 + cell / 2, y0 + cell / 2 + 1);

        // Stars de significância
        const star = starStr(pv[i]?.[j] ?? 1);
        if (star) {
          cx.font = "bold 8px system-ui";
          cx.fillStyle = Math.abs(r) > 0.5 ? "#FFD700" : P.verm;
          cx.fillText(star, x0 + cell / 2, y0 + cell / 2 + 11);
        }
      }
    }
  }

  // ── Rótulos Y (linhas) ──
  cx.font = "10px system-ui"; cx.fillStyle = "#374151"; cx.textAlign = "right";
  for (let i = 0; i < K; i++) {
    const y0 = offY + i * cell + cell / 2 + 3;
    // Critério completo à esquerda
    const partes = rot[i].split("—");
    cx.font = "bold 9px system-ui"; cx.fillStyle = "#6B7280";
    cx.fillText(partes[0].trim(), offX - 6, y0 - 4);
    cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF";
    cx.fillText((partes[1] || "").trim(), offX - 6, y0 + 6);
  }

  // ── Rótulos X (colunas) — rotacionados 45° ──
  cx.save();
  cx.font = "9px system-ui"; cx.fillStyle = "#374151"; cx.textAlign = "right";
  for (let j = 0; j < K; j++) {
    const x0 = offX + j * cell + cell / 2;
    const y0 = offY + K * cell + 6;
    cx.save();
    cx.translate(x0, y0);
    cx.rotate(-Math.PI / 4);
    const partes = rot[j].split("—");
    cx.font = "bold 9px system-ui"; cx.fillStyle = "#374151";
    cx.fillText(partes[0].trim(), 0, 0);
    cx.font = "9px system-ui"; cx.fillStyle = "#9CA3AF";
    cx.fillText((partes[1] || "").trim(), 0, 10);
    cx.restore();
  }
  cx.restore();

  // ── Barra de cor (colorbar) ──
  const cbY  = H - 22;
  const cbX  = offX;
  const cbW  = cell * K;
  const cbH  = 10;
  const grad = cx.createLinearGradient(cbX, 0, cbX + cbW, 0);
  grad.addColorStop(0,   corrColor(-1));
  grad.addColorStop(0.5, corrColor(0));
  grad.addColorStop(1,   corrColor(1));
  cx.fillStyle = grad;
  cx.fillRect(cbX, cbY, cbW, cbH);
  cx.strokeStyle = "#D1D5DB"; cx.lineWidth = 0.5;
  cx.strokeRect(cbX, cbY, cbW, cbH);

  // Ticks da barra
  cx.font = "8px system-ui"; cx.fillStyle = "#6B7280"; cx.textAlign = "center";
  [[-1,"−1"], [-0.5,"−0,5"], [0,"0"], [0.5,"0,5"], [1,"1"]].forEach(([v, lbl]) => {
    const lx = cbX + ((v + 1) / 2) * cbW;
    cx.fillText(lbl, lx, cbY + cbH + 10);
  });
  cx.fillStyle = "#9CA3AF"; cx.font = "8px system-ui"; cx.textAlign = "center";
  const tipoLabel = tipoCorr.value === "pearson"
    ? "Correlação de Pearson (r)"
    : "Correlação de Spearman (ρ)";
  cx.fillText(tipoLabel, cbX + cbW / 2, cbY - 4);

  // ── Título N ──
  cx.fillStyle = "#9CA3AF"; cx.font = "9px system-ui"; cx.textAlign = "left";
  cx.fillText(`n = ${dadosCorr.n.toLocaleString("pt-BR")} áreas`, offX, PT - 4);
}

function redesenharG8() { requestAnimationFrame(desenharG8); }

// ══════════════════════════════════════════════════
// Carregamento de dados dinâmicos
// ══════════════════════════════════════════════════
async function carregarCorrelacao() {
  try {
    const resp = await api.get("/correlacao/");
    const d    = resp.data;
    dadosCorr.rotulos  = d.rotulos   || [];
    dadosCorr.pearson  = d.pearson   || [];
    dadosCorr.spearman = d.spearman  || [];
    dadosCorr.pvalores = d.pvalores  || [];
    dadosCorr.n        = d.n         || 0;
    requestAnimationFrame(desenharG8);
  } catch (e) {
    console.error("Erro ao carregar correlação:", e);
  }
}
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
  desenharG5(); desenharG6(); desenharG7(); desenharG8();
}

// Recarrega quando TOPSIS é executado ou filtros mudam
watch(() => store.rankingAtualizado, () => { carregarDados(); carregarCorrelacao(); });
watch(() => store.filtros, () => { carregarDados(); carregarCorrelacao(); }, { deep: true });

onMounted(() => { carregarDados(); carregarCorrelacao(); });
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
.page-sub    { font-size: 12px; color: #4B5563; }
.header-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.badge { font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 500; }
.badge.azul  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge.verde { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.badge.cinza { background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB; }

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
                color: #4B5563; border-radius: 999px; white-space: nowrap; }
.card-controles { display: flex; align-items: center; gap: 10px; }
.card-nota    { font-size: 10px; color: #4B5563; margin-top: 8px; font-style: italic; }
.canvas       { width: 100% !important; display: block; height: 220px; }

/* Tooltip G2 */
.g2-tooltip {
  position: absolute;
  pointer-events: none;
  background: rgba(17,24,39,0.92);
  color: #fff;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  line-height: 1.6;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  z-index: 10;
  backdrop-filter: blur(4px);
}
.g2-tt-mes   { font-size: 11px; color: #9CA3AF; margin-bottom: 2px; }
.g2-tt-focos { font-size: 14px; font-weight: 700; color: #F97316; }
.g2-tt-frp   { font-size: 11px; color: #D1D5DB; margin-top: 2px; }

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
  color: #4B5563; font-weight: 600; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid #E5E7EB; white-space: nowrap;
}
.tabela td    { padding: 9px 10px; border-bottom: 1px solid #F3F4F6; color: #374151; }
.tabela tr:hover td { background: #F9FAFB; }
.rank-cell  { font-weight: 700; color: #4B5563; }
.nome-cell  { font-weight: 500; color: #111827; max-width: 220px;
              overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.score-cell { font-weight: 700; color: #1D4ED8; font-variant-numeric: tabular-nums; }
.num-cell   { font-variant-numeric: tabular-nums; color: #374151; }
.vazio-cell { text-align: center; color: #4B5563; padding: 24px; font-style: italic; }

.nivel-badge { font-size: 9px; font-weight: 600; padding: 2px 7px;
               border-radius: 999px; text-transform: uppercase; }
.nivel-critico { background: #FEF2F2; color: #B91C1C; }
.nivel-alto    { background: #FFF7ED; color: #C2410C; }
.nivel-medio   { background: #FEFCE8; color: #92400E; }
.nivel-baixo   { background: #F0FDF4; color: #15803D; }

.tabela-ref { font-size: 10px; color: #4B5563; font-style: italic; }

/* Paginação da tabela */
.tabela-pag-controles {
  display: flex; align-items: center; gap: 4px;
  margin: 10px 0 6px; flex-wrap: wrap;
}
.tabela-pag-info {
  font-size: 11px; color: #4B5563;
}
.pag-btn {
  font-size: 11px; font-weight: 500;
  padding: 4px 10px; border-radius: 6px; border: 1px solid #E5E7EB;
  background: #fff; color: #374151; cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.pag-btn:hover:not(:disabled) { background: #F3F4F6; border-color: #D1D5DB; }
.pag-btn:disabled { opacity: 0.4; cursor: default; }
.pag-btn-ativo {
  background: #1D4ED8 !important; color: #fff !important;
  border-color: #1D4ED8 !important;
}

/* Responsivo */
@media (max-width: 860px) {
  .linha { flex-direction: column; }
  .card-grande, .card-medio, .card-heatmap, .card-interp { flex: unset; width: 100%; }
}

/* Heatmap + Interpretação */
.card-heatmap { flex: 1.5; min-width: 0; }
.card-interp  { flex: 1;   min-width: 200px; display: flex; flex-direction: column; }

/* Toggle Pearson/Spearman */
.tipo-corr-toggle { display: flex; background: #F3F4F6; border-radius: 6px;
                    padding: 2px; gap: 2px; }
.tipo-btn {
  font-size: 11px; font-weight: 500; padding: 3px 10px;
  border: none; background: transparent; border-radius: 4px;
  color: #4B5563; cursor: pointer; transition: all 0.15s;
}
.tipo-btn.ativo { background: #fff; color: #1D4ED8;
                  box-shadow: 0 1px 2px rgba(0,0,0,0.1); }

/* Card de interpretação */
.interp-corpo { display: flex; flex-direction: column; gap: 10px; flex: 1; }
.interp-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-radius: 8px; font-weight: 600; font-size: 13px;
}
.badge-verde { background: #F0FDF4; color: #15803D; }
.badge-amar  { background: #FEFCE8; color: #92400E; }
.badge-verm  { background: #FEF2F2; color: #B91C1C; }
.interp-icone { font-size: 16px; }
.interp-texto { font-size: 12px; font-weight: 600; }
.interp-desc  { font-size: 11px; color: #374151; line-height: 1.5; margin: 0; }
.interp-lista { list-style: none; padding: 0; margin: 0;
                display: flex; flex-direction: column; gap: 5px; }
.interp-lista li { font-size: 11px; padding: 5px 8px;
                   border-radius: 5px; color: #374151; }
.par-alto   { background: #FEF2F2; border-left: 3px solid #EF4444; }
.par-medio  { background: #FFFBEB; border-left: 3px solid #F59E0B; }
.par-baixo  { background: #F0FDF4; border-left: 3px solid #22C55E; }
.interp-star { color: #EF4444; font-size: 10px; margin-left: 3px; }
.interp-ref { font-size: 9px; color: #4B5563; font-style: italic;
              margin-top: auto; padding-top: 8px;
              border-top: 1px solid #F3F4F6; }
.interp-ref p { margin: 1px 0; }
.interp-vazio { font-size: 12px; color: #4B5563;
                text-align: center; margin: auto; padding: 20px; }
</style>
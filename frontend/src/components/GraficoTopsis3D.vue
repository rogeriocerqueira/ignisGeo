<template>
  <div class="grafico-topsis">
    <!-- Cabeçalho -->
    <div class="grafico-header">
      <span class="grafico-titulo">Superfície de Risco — Fuzzy TOPSIS 3D</span>
      <div class="grafico-controles">
        <select v-model="eixoX" @change="renderizar">
          <option value="risco_historico_medio">Risco de Fogo</option>
          <option value="total_focos">Focos</option>
          <option value="dias_sem_chuva_medio">Dias sem chuva</option>
          <option value="frp_media">FRP</option>
          <option value="precipitacao_media">Precipitação</option>
        </select>
        <select v-model="eixoY" @change="renderizar">
          <option value="total_focos">Focos</option>
          <option value="risco_historico_medio">Risco de Fogo</option>
          <option value="dias_sem_chuva_medio">Dias sem chuva</option>
          <option value="frp_media">FRP</option>
          <option value="precipitacao_media">Precipitação</option>
        </select>
        <select v-model="tipoGrafico" @change="renderizar">
          <option value="surface">Superfície 3D</option>
          <option value="scatter3d">Dispersão 3D</option>
        </select>
      </div>
    </div>

    <!-- Preset de pesos -->
    <div class="preset-bar">
      <span class="preset-label">Pesos:</span>
      <button
        v-for="p in presets"
        :key="p.id"
        :class="['preset-btn', { ativo: presetAtivo === p.id }]"
        @click="aplicarPreset(p.id)"
      >{{ p.label }}</button>
      <span class="pesos-resumo">
        RF: <b>{{ (pesos.risco_historico_medio * 100).toFixed(0) }}%</b> &nbsp;
        Focos: <b>{{ (pesos.total_focos * 100).toFixed(0) }}%</b> &nbsp;
        DSC: <b>{{ (pesos.dias_sem_chuva_medio * 100).toFixed(0) }}%</b> &nbsp;
        FRP: <b>{{ (pesos.frp_media * 100).toFixed(0) }}%</b> &nbsp;
        Prec: <b>{{ (pesos.precipitacao_media * 100).toFixed(0) }}%</b>
      </span>
    </div>

    <!-- Métricas -->
    <div class="metrics-row">
      <div class="metric-card">
        <span class="metric-label">Biomas</span>
        <span class="metric-value">{{ biomasAtivos.length }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Critérios fuzzy</span>
        <span class="metric-value">5</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Total de focos</span>
        <span class="metric-value">{{ totalFocosStr }}</span>
      </div>
      <div class="metric-card critico">
        <span class="metric-label">Município mais crítico</span>
        <span class="metric-value municipio">{{ municipioTop1 }}</span>
      </div>
    </div>

    <!-- Barra de contexto: fonte + período -->
    <div class="contexto-bar">
      <span class="fonte-badge" :class="usandoDadosReais ? 'fonte-real' : 'fonte-sintetica'">
        <span v-if="usandoDadosReais">
        
          <span v-if="periodoLabel" class="periodo-inline"> · 📅 {{ periodoLabel }}</span>
          <span v-else class="periodo-inline"> · 📅 Todos os dados</span>
        </span>
        <span v-else>⚠ Execute o TOPSIS para carregar dados reais</span>
      </span>
    </div>

    <!-- Gráfico -->
    <div v-if="carregando" class="grafico-loading">
      <span class="loading-spinner"></span>
      <span>Calculando Fuzzy TOPSIS...</span>
    </div>
    <div ref="plotEl" class="grafico-plot"></div>

    <!-- Ranking -->
    <div class="ranking-section">
      <p class="ranking-titulo">Ranking TOPSIS — Ci (proximidade ao ideal positivo)</p>
      <div class="ranking-lista">
        <div
          v-for="(item, idx) in ranking"
          :key="item.bio"
          class="ranking-item"
        >
          <span class="rank-pos">{{ idx + 1 }}.</span>
          <span class="rank-bio">{{ item.bio }}</span>
          <div class="rank-bar-wrap">
            <div
              class="rank-bar"
              :style="{ width: (item.ci * 100).toFixed(1) + '%', background: coresBioma[item.i] }"
            ></div>
          </div>
          <span class="rank-pct">{{ (item.ci * 100).toFixed(1) }}%</span>
          <span class="rank-detalhe">
            RF:{{ rawData.risco_historico_medio[item.i].toFixed(2) }}
            F:{{ rawData.total_focos[item.i].toLocaleString('pt-BR') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useQueimadasStore } from '@/stores/queimadas'

// ─── Props ────────────────────────────────────────────────────────────────────
const props = defineProps({
  altura: { type: Number, default: 420 },
})

// ─── Store ────────────────────────────────────────────────────────────────────
const store = useQueimadasStore()

// ─── Refs de controle ─────────────────────────────────────────────────────────
const plotEl      = ref(null)
const carregando  = ref(true)
const eixoX       = ref('risco_historico_medio')
const eixoY       = ref('total_focos')
const tipoGrafico = ref('surface')
const presetAtivo = ref('padrao')
let   plotlyInst  = null

// ─── Biomas e cores ───────────────────────────────────────────────────────────
const BIOMA_DISPLAY = {
  AMAZONIA:       'Amazônia',
  CERRADO:        'Cerrado',
  CAATINGA:       'Caatinga',
  MATA_ATLANTICA: 'Mata Atlântica',
  PANTANAL:       'Pantanal',
  PAMPA:          'Pampa',
}

const BIOMA_CORES = {
  CERRADO:        '#E24B4A',
  AMAZONIA:       '#1D9E75',
  CAATINGA:       '#BA7517',
  MATA_ATLANTICA: '#378ADD',
  PANTANAL:       '#7F77DD',
  PAMPA:          '#888780',
}

// ─── Fallback sintético (enquanto não há dados reais) ─────────────────────────
const FALLBACK = [
  { bioma: 'CERRADO',        bioma_display: 'Cerrado',        total_focos: 4820, frp_media: 32.0, risco_historico_medio: 0.88, dias_sem_chuva_medio: 85,  precipitacao_media: 12  },
  { bioma: 'AMAZONIA',       bioma_display: 'Amazônia',       total_focos: 2100, frp_media: 18.0, risco_historico_medio: 0.42, dias_sem_chuva_medio: 42,  precipitacao_media: 88  },
  { bioma: 'CAATINGA',       bioma_display: 'Caatinga',       total_focos: 3650, frp_media: 41.0, risco_historico_medio: 0.91, dias_sem_chuva_medio: 110, precipitacao_media: 5   },
  { bioma: 'MATA_ATLANTICA', bioma_display: 'Mata Atlântica', total_focos: 480,  frp_media: 7.5,  risco_historico_medio: 0.21, dias_sem_chuva_medio: 18,  precipitacao_media: 120 },
  { bioma: 'PANTANAL',       bioma_display: 'Pantanal',       total_focos: 1540, frp_media: 23.0, risco_historico_medio: 0.65, dias_sem_chuva_medio: 55,  precipitacao_media: 38  },
  { bioma: 'PAMPA',          bioma_display: 'Pampa',          total_focos: 210,  frp_media: 6.0,  risco_historico_medio: 0.18, dias_sem_chuva_medio: 22,  precipitacao_media: 95  },
]

// ─── Fonte de dados: store.dadosBioma ou fallback ────────────────────────────
const usandoDadosReais = computed(() =>
  Array.isArray(store.dadosBioma) && store.dadosBioma.length > 0
)

const fonte = computed(() =>
  usandoDadosReais.value ? store.dadosBioma : FALLBACK
)

const biomasAtivos = computed(() => fonte.value)

// Nomes para exibição
const biomasNomes = computed(() =>
  fonte.value.map(r => r.bioma_display ?? BIOMA_DISPLAY[r.bioma] ?? r.bioma)
)

// Cores indexadas pela posição da lista
const coresBioma = computed(() =>
  fonte.value.map(r => BIOMA_CORES[r.bioma] ?? '#888780')
)

// rawData no formato { campo: [val0, val1, ...] }
const rawData = computed(() => {
  const campos = [
    'risco_historico_medio',
    'total_focos',
    'frp_media',
    'dias_sem_chuva_medio',
    'precipitacao_media',
  ]
  const out = {}
  for (const c of campos) {
    out[c] = fonte.value.map(r => r[c] ?? 0)
  }
  return out
})

const totalFocosStr = computed(() =>
  rawData.value.total_focos.reduce((a, b) => a + b, 0).toLocaleString('pt-BR')
)

// Município #1 → "CORUMBÁ/MS"
const municipioTop1 = computed(() => {
  const top = store.rankingItems?.[0]
  if (!top) return '—'
  const partes = (top.nome ?? '').split('/')
  return partes.length >= 2 ? `${partes[0]}/${partes[1]}` : (top.nome ?? '—')
})

// Período do filtro ativo → "01/01/2025 — 30/09/2025"
const periodoLabel = computed(() => {
  const { dataInicio, dataFim } = store.filtros ?? {}
  const fmt = (d) => d ? new Date(d + 'T00:00:00').toLocaleDateString('pt-BR') : null
  const di = fmt(dataInicio), df = fmt(dataFim)
  if (di && df) return `${di} — ${df}`
  if (di)       return `A partir de ${di}`
  if (df)       return `Até ${df}`
  return null
})

// ─── Pesos Fuzzy TOPSIS ───────────────────────────────────────────────────────
// Chaves == nomes reais dos campos do modelo
const pesos = ref({
  risco_historico_medio: 0.30,
  total_focos:           0.25,
  dias_sem_chuva_medio:  0.20,
  frp_media:             0.15,
  precipitacao_media:    0.10,
})

const presets = [
  {
    id: 'padrao', label: 'Padrão',
    w: { risco_historico_medio: 0.30, total_focos: 0.25, dias_sem_chuva_medio: 0.20, frp_media: 0.15, precipitacao_media: 0.10 },
  },
  {
    id: 'risco', label: 'Risco',
    w: { risco_historico_medio: 0.40, total_focos: 0.30, dias_sem_chuva_medio: 0.15, frp_media: 0.10, precipitacao_media: 0.05 },
  },
  {
    id: 'frp', label: 'FRP',
    w: { risco_historico_medio: 0.15, total_focos: 0.15, dias_sem_chuva_medio: 0.20, frp_media: 0.40, precipitacao_media: 0.10 },
  },
  {
    id: 'balanced', label: 'Balanceado',
    w: { risco_historico_medio: 0.20, total_focos: 0.20, dias_sem_chuva_medio: 0.20, frp_media: 0.20, precipitacao_media: 0.20 },
  },
]

function aplicarPreset(id) {
  presetAtivo.value = id
  pesos.value = { ...presets.find(p => p.id === id).w }
  renderizar()
}

// ─── Fuzzy TOPSIS ─────────────────────────────────────────────────────────────
const CUSTO = new Set(['precipitacao_media'])  // critérios de custo (invertidos)

function minMax(arr) {
  const mn = Math.min(...arr), mx = Math.max(...arr)
  return arr.map(v => (mx === mn ? 0.5 : (v - mn) / (mx - mn)))
}
function tfn(v) { return [Math.max(0, v - 0.15), v, Math.min(1, v + 0.15)] }
function distEuclid(a, b) {
  return Math.sqrt(((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) / 3)
}

function computarTOPSIS() {
  const W    = pesos.value
  const data = rawData.value
  const norm = {}

  for (const k in data) {
    const n = minMax(data[k])
    norm[k] = CUSTO.has(k) ? n.map(v => 1 - v) : n
  }

  const wFuzzy = {}
  for (const k in norm) {
    wFuzzy[k] = norm[k].map(v => {
      const [l, m, u] = tfn(v)
      return [l * W[k], m * W[k], u * W[k]]
    })
  }

  const fpis = {}, fnis = {}
  for (const k in wFuzzy) {
    fpis[k] = [W[k], W[k], W[k]]
    fnis[k] = [0, 0, 0]
  }

  return biomasNomes.value.map((bio, i) => {
    let dp = 0, dn = 0
    for (const k in wFuzzy) {
      dp += distEuclid(wFuzzy[k][i], fpis[k])
      dn += distEuclid(wFuzzy[k][i], fnis[k])
    }
    return { bio, ci: +((dn / (dp + dn)).toFixed(3)), i }
  }).sort((a, b) => b.ci - a.ci)
}

const ranking = ref([])

// ─── Labels dos eixos ─────────────────────────────────────────────────────────
const labelEixo = {
  risco_historico_medio: 'Risco de Fogo (0–1)',
  total_focos:           'Nº de Focos',
  dias_sem_chuva_medio:  'Dias sem chuva',
  frp_media:             'FRP médio (MW)',
  precipitacao_media:    'Precipitação média (mm)',
}

// ─── Superfície ───────────────────────────────────────────────────────────────
function gerarSuperficie(xKey, yKey, rank) {
  const n    = 45
  const xArr = rawData.value[xKey]
  const yArr = rawData.value[yKey]
  const xMin = Math.min(...xArr), xMax = Math.max(...xArr)
  const yMin = Math.min(...yArr), yMax = Math.max(...yArr)
  const xs   = Array.from({ length: n }, (_, i) => xMin + (xMax - xMin) * i / (n - 1))
  const ys   = Array.from({ length: n }, (_, j) => yMin + (yMax - yMin) * j / (n - 1))
  const z    = ys.map(yv => xs.map(xv => {
    const xN = (xv - xMin) / (xMax - xMin || 1)
    const yN = (yv - yMin) / (yMax - yMin || 1)
    let score = 0
    biomasNomes.value.forEach((_, idx) => {
      const bx = (xArr[idx] - xMin) / (xMax - xMin || 1)
      const by = (yArr[idx] - yMin) / (yMax - yMin || 1)
      const d  = Math.sqrt((xN - bx) ** 2 + (yN - by) ** 2)
      score   += rank.find(r => r.i === idx).ci * Math.exp(-9 * d * d)
    })
    return +(score * 100).toFixed(2)
  }))
  return { xs, ys, z }
}

// ─── Renderização Plotly ──────────────────────────────────────────────────────
async function renderizar() {
  if (!plotEl.value) return
  carregando.value = true

  ranking.value = computarTOPSIS()
  await nextTick()

  const isDark = matchMedia('(prefers-color-scheme: dark)').matches
  const bg     = isDark ? '#1e2227' : '#ffffff'
  const gcol   = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.09)'
  const tcol   = isDark ? '#c9cdd4' : '#444444'
  const rank   = ranking.value
  const xKey   = eixoX.value
  const yKey   = eixoY.value
  const cores  = coresBioma.value

  const colorscale = [
    [0,    '#185FA5'],
    [0.25, '#1D9E75'],
    [0.55, '#EF9F27'],
    [0.80, '#E24B4A'],
    [1,    '#7c0000'],
  ]

  const traces = []

  if (tipoGrafico.value === 'surface') {
    const { xs, ys, z } = gerarSuperficie(xKey, yKey, rank)
    traces.push({
      type: 'surface', x: xs, y: ys, z, colorscale,
      showscale: true,
      colorbar: {
        title: { text: 'Ci (%)', side: 'right' },
        len: 0.6, thickness: 12, x: 1.02,
        tickfont: { color: tcol, size: 10 },
        titlefont: { color: tcol, size: 11 },
      },
      opacity: 0.90,
      contours: { z: { show: true, usecolormap: true, highlightcolor: '#fff', project: { z: true } } },
    })

    biomasNomes.value.forEach((bio, i) => {
      const ci = rank.find(r => r.i === i).ci
      traces.push({
        type: 'scatter3d', mode: 'markers+text',
        x: [rawData.value[xKey][i]],
        y: [rawData.value[yKey][i]],
        z: [ci * 100 + 1.5],
        text: [bio], textposition: 'top center',
        marker: { size: 7, color: cores[i], line: { color: '#fff', width: 1 } },
        textfont: { size: 10, color: cores[i] },
        showlegend: false,
      })
    })
  } else {
    biomasNomes.value.forEach((bio, i) => {
      const ci = rank.find(r => r.i === i).ci
      traces.push({
        type: 'scatter3d', mode: 'markers+text',
        x: [rawData.value[xKey][i]],
        y: [rawData.value[yKey][i]],
        z: [ci * 100],
        text: [bio], textposition: 'top center',
        marker: { size: 14, color: cores[i], opacity: 0.9, line: { color: '#fff', width: 1 } },
        textfont: { size: 11, color: cores[i] },
        name: bio,
      })
    })
  }

  const layout = {
    margin: { l: 0, r: 0, t: 10, b: 0 },
    height: props.altura,
    paper_bgcolor: bg,
    scene: {
      bgcolor: bg,
      xaxis: { title: { text: labelEixo[xKey], font: { color: tcol, size: 11 } }, gridcolor: gcol, tickfont: { color: tcol, size: 9 } },
      yaxis: { title: { text: labelEixo[yKey], font: { color: tcol, size: 11 } }, gridcolor: gcol, tickfont: { color: tcol, size: 9 } },
      zaxis: { title: { text: 'Ci TOPSIS (%)', font: { color: tcol, size: 11 } }, gridcolor: gcol, tickfont: { color: tcol, size: 9 } },
      camera: { eye: { x: 1.6, y: 1.4, z: 1.0 } },
    },
    legend: { bgcolor: 'rgba(0,0,0,0)', font: { color: tcol, size: 10 } },
  }

  if (plotlyInst) {
    await window.Plotly.react(plotEl.value, traces, layout, { responsive: true, displayModeBar: false })
  } else {
    await window.Plotly.newPlot(plotEl.value, traces, layout, { responsive: true, displayModeBar: false })
    plotlyInst = true
  }

  carregando.value = false
}

// ─── Plotly via CDN ───────────────────────────────────────────────────────────
import Plotly from 'plotly.js-dist-min'

onMounted(async () => {
  window.Plotly = Plotly
  await renderizar()
})

onBeforeUnmount(() => {
  if (plotEl.value && window.Plotly) window.Plotly.purge(plotEl.value)
})

// Reage quando o store atualiza dadosBioma (novo TOPSIS ou filtro)
watch(() => store.dadosBioma, async () => {
  await nextTick()
  renderizar()
}, { deep: true })
</script>

<style scoped>
.grafico-topsis {
  background: var(--color-surface, #ffffff);
  border-radius: 10px;
  border: 1px solid var(--color-border, #e5e7eb);
  padding: 14px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.grafico-header {
  display: flex; align-items: center;
  justify-content: space-between; flex-wrap: wrap; gap: 8px;
}
.grafico-titulo {
  font-size: 13px; font-weight: 600;
  color: var(--color-text, #111827); letter-spacing: 0.01em;
}
.grafico-controles { display: flex; gap: 6px; flex-wrap: wrap; }
.grafico-controles select {
  font-size: 12px; padding: 3px 6px;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 6px; background: var(--color-surface, #fff);
  color: var(--color-text, #374151); cursor: pointer;
}

.preset-bar { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; }
.preset-label { color: var(--color-text-muted, #6b7280); font-size: 11px; }
.preset-btn {
  font-size: 11px; padding: 2px 10px;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 999px; background: transparent;
  color: var(--color-text, #374151); cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.preset-btn:hover, .preset-btn.ativo { background: #E24B4A; color: #fff; border-color: #E24B4A; }
.pesos-resumo { font-size: 11px; color: var(--color-text-muted, #6b7280); margin-left: 4px; }

.metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; }
.metric-card {
  background: var(--color-surface-alt, #f9fafb);
  border-radius: 8px; padding: 10px 12px;
  display: flex; flex-direction: column; gap: 2px;
}
.metric-label  { font-size: 11px; color: var(--color-text-muted, #6b7280); }
.metric-value  { font-size: 20px; font-weight: 600; color: var(--color-text, #111827); }
.metric-card.critico .metric-value { font-size: 13px; color: #E24B4A; }
.metric-value.municipio { font-size: 12px; line-height: 1.3; }

/* Barra de contexto */
.contexto-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.fonte-badge {
  font-size: 11px; padding: 3px 10px; border-radius: 6px; font-weight: 500;
}
.fonte-real      { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.fonte-sintetica { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }
.periodo-inline  { font-weight: 400; opacity: 0.85; }

.grafico-loading {
  display: flex; align-items: center; justify-content: center;
  gap: 10px; height: 200px;
  color: var(--color-text-muted, #6b7280); font-size: 13px;
}
.loading-spinner {
  width: 18px; height: 18px;
  border: 2px solid #e5e7eb; border-top-color: #E24B4A;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.grafico-plot { width: 100%; min-height: 300px; border-radius: 8px; overflow: hidden; }

.ranking-section { display: flex; flex-direction: column; gap: 8px; }
.ranking-titulo {
  font-size: 11px; font-weight: 600;
  color: var(--color-text-muted, #6b7280);
  margin: 0; text-transform: uppercase; letter-spacing: 0.04em;
}
.ranking-lista { display: flex; flex-direction: column; gap: 5px; }
.ranking-item  { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.rank-pos      { width: 16px; text-align: right; color: var(--color-text-muted, #9ca3af); flex-shrink: 0; }
.rank-bio      { width: 100px; font-weight: 600; color: var(--color-text, #111827); flex-shrink: 0; }
.rank-bar-wrap { flex: 1; background: var(--color-surface-alt, #f3f4f6); border-radius: 4px; height: 12px; overflow: hidden; }
.rank-bar      { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.rank-pct      { width: 40px; text-align: right; color: var(--color-text-muted, #6b7280); flex-shrink: 0; }
.rank-detalhe  { width: 90px; font-size: 10px; color: var(--color-text-muted, #9ca3af); flex-shrink: 0; }

@media (prefers-color-scheme: dark) {
  .grafico-topsis     { background: #1e2227; border-color: #2e3440; }
  .grafico-titulo     { color: #e5e7eb; }
  .preset-btn         { border-color: #374151; color: #d1d5db; }
  .metric-card        { background: #252b34; }
  .metric-value       { color: #f3f4f6; }
  .rank-bio           { color: #e5e7eb; }
  .rank-bar-wrap      { background: #2e3440; }
  .grafico-controles select { background: #252b34; border-color: #374151; color: #e5e7eb; }
}
</style>
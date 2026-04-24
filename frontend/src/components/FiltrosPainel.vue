<template>
  <aside class="filtros-painel">
    <h2 class="painel-titulo">Filtros</h2>

    <div class="campo">
      <label>Bioma</label>
      <select v-model="form.bioma">
        <option value="">Todos</option>
        <option value="AMAZONIA">Amazônia</option>
        <option value="CERRADO">Cerrado</option>
        <option value="CAATINGA">Caatinga</option>
        <option value="MATA_ATLANTICA">Mata Atlântica</option>
        <option value="PANTANAL">Pantanal</option>
        <option value="PAMPA">Pampa</option>
      </select>
    </div>

    <div class="campo">
      <label>Estado (UF)</label>
      <select v-model="form.estado">
        <option value="">Todos</option>
        <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
      </select>
    </div>

    <div class="campo">
      <label>Nível de risco</label>
      <select v-model="form.nivelRisco">
        <option value="">Todos</option>
        <option value="CRITICO">Crítico</option>
        <option value="ALTO">Alto</option>
        <option value="MEDIO">Médio</option>
        <option value="BAIXO">Baixo</option>
      </select>
    </div>

    <div class="campo">
      <label>Data início</label>
      <input type="date" v-model="form.dataInicio" />
    </div>

    <div class="campo">
      <label>Data fim</label>
      <input type="date" v-model="form.dataFim" />
    </div>

    <div class="acoes">
      <button class="btn-aplicar" @click="aplicar">Aplicar filtros</button>
      <button class="btn-limpar" @click="limpar">Limpar</button>
    </div>

    <hr class="divisor" />

    <!-- Painel TOPSIS -->
    <h2 class="painel-titulo">Calcular TOPSIS</h2>
    <p class="painel-desc">
      Recalcula o ranking de áreas prioritárias com TOPSIS Fuzzy.
    </p>

    <div class="campo">
      <label>Período início</label>
      <input type="date" v-model="topsis.inicio" />
    </div>
    <div class="campo">
      <label>Período fim</label>
      <input type="date" v-model="topsis.fim" />
    </div>

    <button
      class="btn-topsis"
      :disabled="store.carregando"
      @click="executarTopsis"
    >
      {{ store.carregando ? "Calculando..." : "Executar TOPSIS Fuzzy" }}
    </button>

    <div v-if="resultadoTopsis" class="resultado-topsis">
      <p class="resultado-titulo">Cálculo concluído!</p>
      <p>{{ resultadoTopsis.areas_atualizadas }} áreas atualizadas</p>
      <p class="resultado-sub">Top área de risco:</p>
      <p v-if="resultadoTopsis.top_5?.length" class="resultado-top">
        {{ resultadoTopsis.top_5[0].nome }}<br/>
        Score: <strong>{{ resultadoTopsis.top_5[0].score_topsis }}</strong>
      </p>
    </div>

    <div v-if="store.erro" class="erro">{{ store.erro }}</div>
  </aside>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useQueimadasStore } from "@/stores/queimadas";

const store = useQueimadasStore();

const form = reactive({
  bioma: "",
  estado: "",
  nivelRisco: "",
  dataInicio: "",
  dataFim: "",
});

const topsis = reactive({
  inicio: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    .toISOString().split("T")[0],
  fim: new Date().toISOString().split("T")[0],
});

const resultadoTopsis = ref(null);

const ufs = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA",
  "MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN",
  "RO","RR","RS","SC","SE","SP","TO",
];

function aplicar() {
  store.aplicarFiltros({
    bioma:      form.bioma,
    estado:     form.estado,
    nivelRisco: form.nivelRisco,
    dataInicio: form.dataInicio,
    dataFim:    form.dataFim,
  });
}

function limpar() {
  Object.assign(form, { bioma:"", estado:"", nivelRisco:"", dataInicio:"", dataFim:"" });
  store.limparFiltros();
}

async function executarTopsis() {
  resultadoTopsis.value = null;
  try {
    const resultado = await store.executarTopsis(topsis.inicio, topsis.fim);
    resultadoTopsis.value = resultado;
  } catch (_) {}
}
</script>

<style scoped>
.filtros-painel {
  width: 260px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 20px 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.painel-titulo {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 14px;
}

.painel-desc {
  font-size: 12px;
  color: #6b7280;
  margin: -10px 0 12px;
  line-height: 1.5;
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.campo label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}

.campo select,
.campo input[type="date"] {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 13px;
  color: #1f2937;
  background: #f9fafb;
  outline: none;
  transition: border-color 0.15s;
}

.campo select:focus,
.campo input:focus {
  border-color: #3b82f6;
  background: #fff;
}

.acoes {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.btn-aplicar {
  flex: 1;
  padding: 8px;
  background: #1d4ed8;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-aplicar:hover { background: #1e40af; }

.btn-limpar {
  padding: 8px 12px;
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
}
.btn-limpar:hover { background: #f3f4f6; }

.divisor {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 4px 0 16px;
}

.btn-topsis {
  width: 100%;
  padding: 9px;
  background: #059669;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 12px;
}
.btn-topsis:hover:not(:disabled) { background: #047857; }
.btn-topsis:disabled { opacity: 0.6; cursor: not-allowed; }

.resultado-topsis {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 12px;
  color: #065f46;
}
.resultado-titulo { font-weight: 600; margin-bottom: 4px; }
.resultado-sub { margin-top: 6px; font-weight: 500; }
.resultado-top { font-size: 13px; color: #047857; }

.erro {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: #b91c1c;
  margin-top: 8px;
}
</style>

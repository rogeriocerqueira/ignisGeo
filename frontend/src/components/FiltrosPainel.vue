<template>
  <aside class="filtros-painel">
    <h2 class="painel-titulo">Filtros</h2>

    <div class="campo">
      <label :for="'estado'">Estado (UF)</label>
      <select id="estado" v-model="form.estado" @change="onEstadoChange">
        <option value="">Todos</option>
        <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
      </select>
    </div>

    <div class="campo">
      <label :for="'bioma'">Bioma</label>
      <select id="bioma" v-model="form.bioma">
        <option value="">Todos</option>
        <option
          v-for="b in biomasDisponiveis"
          :key="b.value"
          :value="b.value"
        >{{ b.label }}</option>
      </select>
      <span v-if="form.estado && biomasDisponiveis.length < 6" class="campo-dica">
        Biomas de {{ form.estado }}
      </span>
    </div>

    <div class="campo">
      <label :for="'nivel'">Nível de risco</label>
      <select id="nivel" v-model="form.nivelRisco">
        <option value="">Todos</option>
        <option value="CRITICO">Crítico</option>
        <option value="ALTO">Alto</option>
        <option value="MEDIO">Médio</option>
        <option value="BAIXO">Baixo</option>
      </select>
    </div>

    <div class="campo">
      <label :for="'dt-ini'">Data início</label>
      <input id="dt-ini" type="date" v-model="form.dataInicio" />
    </div>

    <div class="campo">
      <label :for="'dt-fim'">Data fim</label>
      <input id="dt-fim" type="date" v-model="form.dataFim" />
    </div>

    <div class="acoes">
      <button class="btn-aplicar" @click="aplicar">Aplicar filtros</button>
      <button class="btn-limpar" @click="limpar">Limpar</button>
    </div>

    <div v-if="temFiltrosAtivos" class="filtros-ativos">
      <span class="filtros-ativos-label">Filtros ativos</span>
      <span v-if="form.estado"     class="tag">{{ form.estado }}</span>
      <span v-if="form.bioma"      class="tag">{{ nomeBioma(form.bioma) }}</span>
      <span v-if="form.nivelRisco" class="tag">{{ form.nivelRisco }}</span>
      <span v-if="form.dataInicio" class="tag">De: {{ form.dataInicio }}</span>
      <span v-if="form.dataFim"    class="tag">Até: {{ form.dataFim }}</span>
    </div>

    <hr class="divisor" />

    <!-- TOPSIS — usa os filtros ativos acima -->
    <h2 class="painel-titulo">Análise TOPSIS Fuzzy</h2>
    <p class="painel-desc">
      Calcula o ranking com base nos <strong>filtros ativos</strong> acima.
    </p>

    <button
      class="btn-topsis"
      :disabled="store.carregando"
      @click="executarTopsis"
    >
      {{ store.carregando ? "Calculando..." : "Executar TOPSIS Fuzzy" }}
    </button>

    <p class="painel-nota">
        ⚠️ Executar TOPSIS recalcula e substitui o ranking atual.
        Para o ranking global, limpe os filtros antes de executar.
    </p>

    <div v-if="resultadoTopsis" class="resultado-topsis">
      <p class="resultado-titulo">✓ Cálculo concluído</p>
      <p>{{ resultadoTopsis.areas_atualizadas }} áreas analisadas</p>
      <p v-if="temFiltrosAtivos" class="resultado-filtros">
        {{ descricaoFiltros }}
      </p>
      <template v-if="resultadoTopsis.top_5?.length">
        <p class="resultado-sub">Top área de risco:</p>
        <p class="resultado-top">
          {{ resultadoTopsis.top_5[0].nome }}<br/>
          Score: <strong>{{ resultadoTopsis.top_5[0].score_topsis }}</strong>
          · #{{ resultadoTopsis.top_5[0].ranking }}
        </p>
      </template>
    </div>

    <div v-if="erroLocal" class="erro">{{ erroLocal }}</div>
    <div v-else-if="store.erro" class="erro">{{ store.erro }}</div>
  </aside>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import { useQueimadasStore } from "@/stores/queimadas";
import { BIOMAS_POR_ESTADO, NOME_BIOMA } from "@/biomas";

const store = useQueimadasStore();

const form = reactive({
  estado:     "",
  bioma:      "",
  nivelRisco: "",
  dataInicio: "",
  dataFim:    "",
});

const resultadoTopsis = ref(null);
const erroLocal       = ref(null);

const TODOS_BIOMAS = Object.entries(NOME_BIOMA).map(([value, label]) => ({ value, label }));

const biomasDisponiveis = computed(() => {
  if (!form.estado) return TODOS_BIOMAS;
  const lista = BIOMAS_POR_ESTADO[form.estado] ?? [];
  return TODOS_BIOMAS.filter((b) => lista.includes(b.value));
});

const temFiltrosAtivos = computed(() =>
  form.estado || form.bioma || form.nivelRisco || form.dataInicio || form.dataFim
);

const descricaoFiltros = computed(() => {
  const p = [];
  if (form.estado)     p.push(form.estado);
  if (form.bioma)      p.push(nomeBioma(form.bioma));
  if (form.dataInicio) p.push(`De ${form.dataInicio}`);
  if (form.dataFim)    p.push(`até ${form.dataFim}`);
  return p.join(" · ");
});

const ufs = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA",
  "MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN",
  "RO","RR","RS","SC","SE","SP","TO",
];

function nomeBioma(key) { return NOME_BIOMA[key] ?? key; }

function onEstadoChange() {
  if (!form.estado) return;
  const lista = BIOMAS_POR_ESTADO[form.estado] ?? [];
  if (form.bioma && !lista.includes(form.bioma)) form.bioma = "";
}

function aplicar() {
  erroLocal.value = null;
  resultadoTopsis.value = null;
  store.aplicarFiltros({
    bioma:      form.bioma,
    estado:     form.estado,
    nivelRisco: form.nivelRisco,
    dataInicio: form.dataInicio,
    dataFim:    form.dataFim,
  });
}

function limpar() {
  Object.assign(form, { estado:"", bioma:"", nivelRisco:"", dataInicio:"", dataFim:"" });
  erroLocal.value       = null;
  resultadoTopsis.value = null;
  store.limparFiltros();
}

async function executarTopsis() {
  resultadoTopsis.value = null;
  erroLocal.value = null;
  try {
    // Passa os filtros ativos direto para o TOPSIS
    const resultado = await store.executarTopsis(
      form.dataInicio || null,
      form.dataFim    || null,
      form.estado     || null,
      form.bioma      || null,
    );
    resultadoTopsis.value = resultado;
  } catch {
    erroLocal.value = "Erro ao calcular TOPSIS. Verifique se há dados com os filtros atuais.";
  }
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
.painel-desc strong { color: #374151; }
.campo {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.painel-nota {
  font-size: 11px;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 6px 10px;
  margin-top: -6px;
  margin-bottom: 8px;
  line-height: 1.5;
}
.campo label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}
.campo-dica {
  font-size: 11px;
  color: #3b82f6;
  font-style: italic;
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
.acoes { display: flex; gap: 8px; margin-bottom: 12px; }
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
.filtros-ativos {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
  align-items: center;
}
.filtros-ativos-label {
  font-size: 10px;
  color: #9ca3af;
  font-weight: 500;
  text-transform: uppercase;
  width: 100%;
}
.tag {
  font-size: 11px;
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 2px 8px;
}
.divisor { border: none; border-top: 1px solid #e5e7eb; margin: 4px 0 16px; }
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
  margin-bottom: 8px;
}
.resultado-titulo { font-weight: 600; margin-bottom: 4px; }
.resultado-filtros { color: #0f766e; font-style: italic; margin: 2px 0 4px; font-size: 11px; }
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

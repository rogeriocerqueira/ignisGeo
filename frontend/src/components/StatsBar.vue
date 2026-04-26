<template>
  <div class="stats-bar">
    <div class="card">
      <span class="card-label">Total de focos</span>
      <span class="card-valor">{{ store.totalFocos.toLocaleString("pt-BR") }}</span>
    </div>

    <div class="card card-critico">
      <span class="card-label">Áreas críticas</span>
      <span class="card-valor">{{ store.areasCriticas }}</span>
      <span class="card-sub">score ≥ 0.45</span>

    </div>

    <div
      v-for="bioma in store.porBioma.slice(0, 3)"
      :key="bioma.bioma"
      class="card"
    >
      <span class="card-label">{{ nomeBioma(bioma.bioma) }}</span>
      <span class="card-valor">{{ bioma.total.toLocaleString("pt-BR") }}</span>
      <span class="card-sub">FRP médio: {{ (bioma.frp_media ?? 0).toFixed(0) }} MW</span>
    </div>
  </div>
</template>

<script setup>
import { useQueimadasStore } from "@/stores/queimadas";

const store = useQueimadasStore();

const nomes = {
  AMAZONIA: "Amazônia",
  CERRADO: "Cerrado",
  CAATINGA: "Caatinga",
  MATA_ATLANTICA: "Mata Atlântica",
  PANTANAL: "Pantanal",
  PAMPA: "Pampa",
};

function nomeBioma(key) {
  return nomes[key] ?? key;
}
</script>

<style scoped>
.stats-bar {
  display: flex;
  gap: 10px;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
  flex-shrink: 0;
}

.card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 16px;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-critico {
  border-color: #fecaca;
  background: #fef2f2;
}

.card-label {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.card-valor {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}

.card-critico .card-valor { color: #b91c1c; }

.card-sub {
  font-size: 11px;
  color: #9ca3af;
}
</style>

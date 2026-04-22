<template>
  <section class="ranking-painel">
    <h2 class="titulo">Top áreas prioritárias</h2>

    <div v-if="!ranking.length" class="vazio">
      Nenhum dado. Execute o TOPSIS Fuzzy primeiro.
    </div>

    <ul v-else class="lista">
      <li
        v-for="area in ranking"
        :key="area.id"
        class="item"
        @click="$emit('focar-area', area)"
      >
        <div class="item-rank">#{{ area.ranking }}</div>

        <div class="item-info">
          <p class="item-nome">{{ area.nome }}</p>
          <p class="item-sub">{{ area.bioma }} · {{ area.total_focos }} focos</p>
        </div>

        <div class="item-direita">
          <span :class="['badge', `badge-${area.nivel_risco.toLowerCase()}`]">
            {{ area.nivel_risco_display }}
          </span>
          <span class="item-score">{{ area.score_topsis.toFixed(3) }}</span>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useQueimadasStore } from "@/stores/queimadas";

defineEmits(["focar-area"]);

const store = useQueimadasStore();
const ranking = computed(() => store.rankingTop10);
</script>

<style scoped>
.ranking-painel {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #e5e7eb;
  padding: 20px 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.titulo {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 16px;
  margin: 0 0 14px;
}

.vazio {
  padding: 16px;
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
}

.lista {
  list-style: none;
  margin: 0;
  padding: 0;
}

.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.1s;
  border-bottom: 1px solid #f3f4f6;
}
.item:hover { background: #f9fafb; }

.item-rank {
  font-size: 16px;
  font-weight: 700;
  color: #d1d5db;
  min-width: 30px;
  text-align: center;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-nome {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0 0 2px;
}

.item-sub {
  font-size: 11px;
  color: #9ca3af;
  margin: 0;
}

.item-direita {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge-critico { background: #fef2f2; color: #b91c1c; }
.badge-alto    { background: #fff7ed; color: #c2410c; }
.badge-medio   { background: #fefce8; color: #92400e; }
.badge-baixo   { background: #f0fdf4; color: #15803d; }

.item-score {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}
</style>

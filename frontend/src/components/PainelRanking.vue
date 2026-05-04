<template>
  <section class="ranking-painel">
    <h2 class="titulo">Top áreas prioritárias</h2>

    <!-- Carregando -->
    <div v-if="store.carregando && !store.rankingItems.length" class="vazio">
      Carregando...
    </div>

    <!-- Vazio -->
    <div v-else-if="!store.rankingItems.length" class="vazio">
      Nenhum dado. Execute o TOPSIS Fuzzy primeiro.
    </div>

    <!-- Lista -->
    <ul v-else class="lista">
      <li
        v-for="area in store.rankingItems"
        :key="area.id"
        class="item"
        @click="$emit('focar-area', area)"
      >
        <div class="item-rank">#{{ area.ranking }}</div>

        <div class="item-info">
          <p class="item-nome" :title="area.nome">{{ area.nome }}</p>
          <p class="item-sub">{{ area.bioma }} · {{ area.total_focos }} focos</p>
        </div>

        <div class="item-direita">
          <span :class="['badge', `badge-${area.nivel_risco.toLowerCase()}`]">
            {{ area.nivel_risco_display || area.nivel_risco }}
          </span>
          <span class="item-score">{{ Number(area.score_topsis).toFixed(4) }}</span>
        </div>
      </li>
    </ul>

    <!-- Paginação -->
    <div v-if="store.rankingTotalPags > 1" class="paginacao">
      <button
        class="btn-pag"
        :disabled="store.rankingPagina <= 1 || store.carregando"
        @click="paginaAnterior"
      >
        ← Anterior
      </button>

      <div class="pag-info">
        <span class="pag-atual">{{ store.rankingPagina }}</span>
        <span class="pag-sep">/</span>
        <span class="pag-total">{{ store.rankingTotalPags }}</span>
      </div>

      <button
        class="btn-pag"
        :disabled="store.rankingPagina >= store.rankingTotalPags || store.carregando"
        @click="proximaPagina"
      >
        Próxima →
      </button>
    </div>

    <!-- Total -->
    <p v-if="store.rankingTotal > 0" class="total-info">
      {{ store.rankingTotal.toLocaleString("pt-BR") }} áreas ranqueadas
    </p>
  </section>
</template>

<script setup>
import { useQueimadasStore } from "@/stores/queimadas";

defineEmits(["focar-area"]);

const store = useQueimadasStore();

function paginaAnterior() {
  if (store.rankingPagina > 1) {
    store.carregarRanking(store.rankingPagina - 1);
  }
}

function proximaPagina() {
  if (store.rankingPagina < store.rankingTotalPags) {
    store.carregarRanking(store.rankingPagina + 1);
  }
}
</script>

<style scoped>
.ranking-painel {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #e5e7eb;
  padding: 20px 0 8px;
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
  flex: 1;
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

.item-info { flex: 1; min-width: 0; }

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

/* ── Paginação ── */
.paginacao {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-top: 1px solid #f3f4f6;
  gap: 8px;
}

.btn-pag {
  font-size: 11px;
  font-weight: 500;
  color: #374151;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
  white-space: nowrap;
}
.btn-pag:hover:not(:disabled) {
  background: #1d4ed8;
  color: #fff;
  border-color: #1d4ed8;
}
.btn-pag:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.pag-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
}
.pag-atual { font-weight: 700; color: #1d4ed8; }
.pag-sep   { color: #d1d5db; }
.pag-total { color: #9ca3af; }

.total-info {
  font-size: 11px;
  color: #9ca3af;
  text-align: center;
  padding: 6px 16px 4px;
  margin: 0;
}
</style>
<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="header-esquerda">
        <div class="logo-icon"></div>
        <div>
          <h1 class="header-titulo">Monitor de Queimadas</h1>
          <p class="header-sub">INPE · Análise Multicritério TOPSIS Fuzzy · PostGIS</p>
        </div>
      </div>
      <div class="header-direita">
        <span class="badge-status" :class="{ ativo: !store.carregando }">
          {{ store.carregando ? "Atualizando..." : "Dados ativos" }}
        </span>
      </div>
    </header>

    <!-- Stats Bar -->
    <StatsBar />

    <!-- Corpo principal -->
    <div class="corpo">
      <FiltrosPainel />

      <main class="mapa-area">
        <MapaQueimadas />
      </main>

      <PainelRanking @focar-area="focarArea" />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useQueimadasStore } from "@/stores/queimadas";
import MapaQueimadas from "@/components/MapaQueimadas.vue";
import FiltrosPainel from "@/components/FiltrosPainel.vue";
import PainelRanking from "@/components/PainelRanking.vue";
import StatsBar from "@/components/StatsBar.vue";

const store = useQueimadasStore();

onMounted(() => {
  store.inicializar();
});

function focarArea(area) {
  // Futuro: emitir evento para o mapa centralizar na área clicada
  console.log("Focar área:", area.nome);
}
</script>

<style>
/* Reset global */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f3f4f6;
  color: #1f2937;
  height: 100vh;
  overflow: hidden;
}

#app { height: 100vh; }
</style>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #1d4ed8;
  color: white;
  flex-shrink: 0;
}

.header-esquerda {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: rgba(255,255,255,0.2);
  border-radius: 8px;
  position: relative;
}

.logo-icon::before {
  content: "";
  position: absolute;
  inset: 8px;
  background: #fb923c;
  border-radius: 50%;
}

.header-titulo {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.header-sub {
  font-size: 11px;
  opacity: 0.75;
  margin-top: 2px;
}

.badge-status {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.8);
}

.badge-status.ativo {
  background: rgba(16, 185, 129, 0.25);
  color: #6ee7b7;
}

.corpo {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.mapa-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>

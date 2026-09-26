<template>
  <div class="app">

    <!-- ── Header ── -->
    <header class="header">
      <div class="header-esquerda">
        <div class="logo-icon"></div>
        <div>
          <h1 class="header-titulo">Monitor de Queimadas</h1>
          <p class="header-sub">INPE · Análise Multicritério TOPSIS Fuzzy · PostGIS</p>
        </div>
      </div>

      <!-- ── Navegação ── -->
      <nav class="nav">
        <button
          class="nav-btn"
          :class="{ ativo: paginaAtual === 'monitor' }"
          @click="paginaAtual = 'monitor'"
        >
          🗺️ Monitor
        </button>
        <button
          class="nav-btn"
          :class="{ ativo: paginaAtual === 'graficos' }"
          @click="paginaAtual = 'graficos'"
        >
          📊 Resultados
        </button>
        <button
          class="nav-btn"
          :class="{ ativo: paginaAtual === 'avancado' }"
          @click="paginaAtual = 'avancado'"
        >
          🔬 Avançado
        </button>
      </nav>

      <div class="header-direita">
        <span class="badge-status" :class="{ ativo: !store.carregando }">
          {{ store.carregando ? "Atualizando..." : "Dados ativos" }}
        </span>
      </div>
    </header>

    <!-- ── Stats Bar (sempre visível) ── -->
    <StatsBar />

    <!-- ── Página: Monitor ── -->
    <div v-if="paginaAtual === 'monitor'" class="corpo">
      <FiltrosPainel />
      <main class="mapa-area">
        <MapaQueimadas />
      </main>
      <PainelRanking @focar-area="focarArea" />
    </div>

    <!-- ── Página: Gráficos ── -->
    <div v-else-if="paginaAtual === 'graficos'" class="corpo-graficos">
      <GraficosView />
    </div>

    <!-- ── Página: Avançado ── -->
    <div v-else-if="paginaAtual === 'avancado'" class="corpo-graficos">
      <AvancadoView />
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useQueimadasStore } from "@/stores/queimadas";
import MapaQueimadas  from "@/components/MapaQueimadas.vue";
import FiltrosPainel  from "@/components/FiltrosPainel.vue";
import PainelRanking  from "@/components/PainelRanking.vue";
import StatsBar       from "@/components/StatsBar.vue";
import GraficosView   from "@/components/GraficosView.vue";
import AvancadoView   from "@/components/AvancadoView.vue";

const store       = useQueimadasStore();
const paginaAtual = ref("monitor");

onMounted(() => store.inicializar());

function focarArea(area) {
  console.log("Focar área:", area.nome);
}
</script>

<style>
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
.app { display: flex; flex-direction: column; height: 100vh; }
.header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; background: #1d4ed8; color: white; flex-shrink: 0; gap: 16px;
}
.header-esquerda { display: flex; align-items: center; gap: 14px; }
.logo-icon {
  width: 36px; height: 36px; background: rgba(255,255,255,0.2);
  border-radius: 8px; position: relative; flex-shrink: 0;
}
.logo-icon::before {
  content: ""; position: absolute; inset: 8px;
  background: #fb923c; border-radius: 50%;
}
.header-titulo { font-size: 16px; font-weight: 700; letter-spacing: -0.01em; }
.header-sub    { font-size: 11px; opacity: 0.75; margin-top: 2px; }
.nav {
  display: flex; gap: 4px; background: rgba(255,255,255,0.1);
  padding: 4px; border-radius: 10px;
}
.nav-btn {
  padding: 6px 16px; border: none; border-radius: 7px; font-size: 13px;
  font-weight: 500; color: rgba(255,255,255,0.75); background: transparent;
  cursor: pointer; transition: background 0.15s, color 0.15s; white-space: nowrap;
}
.nav-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }
.nav-btn.ativo { background: #fff; color: #1d4ed8; }
.header-direita { flex-shrink: 0; }
.badge-status {
  font-size: 12px; padding: 4px 12px; border-radius: 999px;
  background: rgba(255,255,255,0.15); color: rgba(255,255,255,0.8);
}
.badge-status.ativo { background: rgba(16,185,129,0.25); color: #6ee7b7; }
.corpo { display: flex; flex: 1; overflow: hidden; }
.mapa-area { flex: 1; overflow: hidden; position: relative; }
.corpo-graficos { flex: 1; overflow-y: auto; background: #f3f4f6; }
</style>
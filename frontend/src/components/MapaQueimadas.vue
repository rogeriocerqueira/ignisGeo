<template>
  <div class="mapa-container">
    <div ref="mapaRef" class="mapa"></div>

    <div class="legenda">
      <p class="legenda-titulo">Nível de risco</p>
      <div v-for="item in legendaItens" :key="item.label" class="legenda-item">
        <span class="legenda-cor" :style="{ background: item.cor }"></span>
        <span>{{ item.label }}</span>
      </div>
      <hr class="legenda-hr" />
      <div class="legenda-item">
        <span class="legenda-ponto"></span>
        <span>Foco ativo</span>
      </div>
    </div>

    <div class="controles-camada">
      <button :class="['btn-camada', { ativo: camadaAtiva === 'focos' }]"   @click="alternarCamada('focos')">Focos</button>
      <button :class="['btn-camada', { ativo: camadaAtiva === 'heatmap' }]" @click="alternarCamada('heatmap')">Heatmap</button>
      <button :class="['btn-camada', { ativo: camadaAtiva === 'areas' }]"   @click="alternarCamada('areas')">Áreas de risco</button>
    </div>

    <div v-if="store.carregando" class="mapa-loading">
      <div class="spinner"></div>
      <span>Carregando dados...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useQueimadasStore } from "@/stores/queimadas";

import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, shadowUrl: markerShadow });

const store = useQueimadasStore();
const mapaRef = ref(null);

let mapa = null;
let camadaFocos   = null;
let camadaHeatmap = null;
let camadaAreas   = null;

const camadaAtiva = ref("focos");

const legendaItens = [
  { cor: "#b91c1c", label: "Crítico (≥ 0.75)" },
  { cor: "#ea580c", label: "Alto (0.55 – 0.75)" },
  { cor: "#ca8a04", label: "Médio (0.35 – 0.55)" },
  { cor: "#16a34a", label: "Baixo (< 0.35)" },
];

const corPorNivel = {
  CRITICO: "#b91c1c",
  ALTO:    "#ea580c",
  MEDIO:   "#ca8a04",
  BAIXO:   "#16a34a",
};

function corFoco(frp) {
  if (frp >= 200) return "#7c2d12";
  if (frp >= 100) return "#b91c1c";
  if (frp >= 50)  return "#ea580c";
  return "#f97316";
}

function fitFocos() {
  if (!camadaFocos) return;
  const bounds = camadaFocos.getBounds();
  if (bounds.isValid()) mapa.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
}                   
// ---- Inicializa o mapa ----
onMounted(async () => {
  mapa = L.map(mapaRef.value, {
    center: [-14.235, -51.925],
    zoom: 5,
    zoomControl: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(mapa);

  // Aguarda o mapa renderizar antes de plotar os dados
  await nextTick();

  if (store.focosGeoJSON?.features?.length) renderizarFocos();
  if (store.areasGeoJSON?.features?.length) renderizarAreas();
});

onUnmounted(() => {
  if (mapa) mapa.remove();
});

// ---- Watchers — dispara só quando há dados válidos ----
watch(() => store.focosGeoJSON, (geojson) => {
  if (geojson?.features?.length && mapa) renderizarFocos();
});

watch(() => store.areasGeoJSON, (geojson) => {
  if (geojson?.features?.length && mapa) renderizarAreas();
});

// ---- Renderização dos focos ----
function renderizarFocos() {
  if (!store.focosGeoJSON?.features?.length) return;

  if (camadaFocos)   mapa.removeLayer(camadaFocos);
  if (camadaHeatmap) mapa.removeLayer(camadaHeatmap);

  const features = store.focosGeoJSON.features;

  camadaFocos = L.geoJSON(store.focosGeoJSON, {
    pointToLayer(feature, latlng) {
      const frp = feature.properties.frp ?? 0;
      return L.circleMarker(latlng, {
        radius: Math.max(4, Math.min(12, frp / 30)),
        fillColor: corFoco(frp),
        color: "#fff",
        weight: 0.8,
        opacity: 0.9,
        fillOpacity: 0.75,
      });
    },
    onEachFeature(feature, layer) {
      const p = feature.properties;
      layer.bindPopup(`
        <div class="popup-foco">
          <strong>${p.municipio} / ${p.estado}</strong><br/>
          Bioma: ${p.bioma}<br/>
          FRP: <strong>${(p.frp ?? 0).toFixed(1)} MW</strong><br/>
          Data: ${new Date(p.data_hora).toLocaleDateString("pt-BR")}<br/>
          Satélite: ${p.satelite ?? "—"}
        </div>
      `);
    },
  });

  // Heatmap ponderado pelo FRP
  const pontos = features.map((f) => {
    const [lon, lat] = f.geometry.coordinates;
    return [lat, lon, Math.min(1, (f.properties.frp ?? 1) / 500)];
  });

  import("leaflet.heat").then(() => {
    camadaHeatmap = L.heatLayer(pontos, {
      radius: 25,
      blur: 20,
      maxZoom: 10,
      max: 1.0,
      gradient: { 0.1: "#16a34a", 0.4: "#ca8a04", 0.7: "#ea580c", 1.0: "#7c2d12" },
    });
    if (camadaAtiva.value === "heatmap") camadaHeatmap.addTo(mapa);
  });

  if (camadaAtiva.value === "focos") {
    camadaFocos.addTo(mapa);
    fitFocos();
  }
}

// ---- Renderização das áreas de risco ----
function renderizarAreas() {
  if (!store.areasGeoJSON?.features?.length) return;

  if (camadaAreas) mapa.removeLayer(camadaAreas);

  // Filtra features sem geometria (áreas calculadas sem shapefile de municípios)
  const geojsonValido = {
    ...store.areasGeoJSON,
    features: store.areasGeoJSON.features.filter(
      (f) => f.geometry !== null && f.geometry !== undefined
    ),
  };

  if (!geojsonValido.features.length) return;

  camadaAreas = L.geoJSON(geojsonValido, {
    style(feature) {
      const cor = corPorNivel[feature.properties.nivel_risco] ?? "#888";
      return {
        fillColor: cor,
        fillOpacity: 0.45,
        color: cor,
        weight: 1.5,
        opacity: 0.85,
      };
    },
    onEachFeature(feature, layer) {
      const p = feature.properties;
      layer.bindPopup(`
        <div class="popup-area">
          <strong>${p.nome}</strong><br/>
          Bioma: ${p.bioma}<br/>
          Score TOPSIS: <strong>${(p.score_topsis ?? 0).toFixed(3)}</strong><br/>
          Nível: <strong style="color:${corPorNivel[p.nivel_risco]}">${p.nivel_risco_display}</strong><br/>
          Focos: ${p.total_focos}<br/>
          FRP médio: ${(p.frp_media ?? 0).toFixed(1)} MW<br/>
          Ranking: #${p.ranking}
        </div>
      `);
      layer.on("mouseover", () => layer.setStyle({ fillOpacity: 0.7 }));
      layer.on("mouseout",  () => layer.setStyle({ fillOpacity: 0.45 }));
    },
  });

  if (camadaAtiva.value === "areas") camadaAreas.addTo(mapa);
}

// ---- Alterna camadas ----
function alternarCamada(nova) {
  camadaAtiva.value = nova;

  [camadaFocos, camadaHeatmap, camadaAreas].forEach((c) => {
    if (c && mapa.hasLayer(c)) mapa.removeLayer(c);
  });

  if (nova === "focos" && camadaFocos) {
    camadaFocos.addTo(mapa);
    fitFocos();
  }
  if (nova === "heatmap" && camadaHeatmap) camadaHeatmap.addTo(mapa);
  if (nova === "areas"   && camadaAreas)   camadaAreas.addTo(mapa);
}
</script>

<style scoped>
.mapa-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.mapa {
  width: 100%;
  height: 100%;
  z-index: 0;
}

.legenda {
  position: absolute;
  bottom: 32px;
  right: 12px;
  background: white;
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 1000;
  font-size: 13px;
  min-width: 160px;
}

.legenda-titulo {
  font-weight: 600;
  margin: 0 0 8px;
  font-size: 12px;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.legenda-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
  color: #333;
}

.legenda-cor {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legenda-ponto {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #f97316;
  flex-shrink: 0;
}

.legenda-hr {
  border: none;
  border-top: 1px solid #eee;
  margin: 8px 0;
}

.controles-camada {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  background: white;
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 1000;
}

.btn-camada {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #555;
  transition: all 0.15s;
}

.btn-camada:hover { background: #f3f4f6; }
.btn-camada.ativo { background: #1d4ed8; color: white; }

.mapa-loading {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 2000;
  font-size: 14px;
  color: #333;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #1d4ed8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

:global(.popup-foco), :global(.popup-area) {
  font-size: 13px;
  line-height: 1.6;
  min-width: 180px;
}
</style>
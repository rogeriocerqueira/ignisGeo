import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

export const focosApi = {
  /** Retorna FeatureCollection GeoJSON dos focos para o Leaflet */
  getGeoJSON(params = {}) {
    return api.get("/focos/geojson/", { params });
  },

  /** Lista simplificada para tabelas */
  getLista(params = {}) {
    return api.get("/focos/", { params });
  },
};

export const areasApi = {
  /** Retorna FeatureCollection GeoJSON das áreas de risco */
  getGeoJSON(params = {}) {
    return api.get("/areas-risco/geojson/", { params });
  },

  /** Ranking sem geometria (mais leve) */
  getRanking(params = {}) {
    return api.get("/ranking/", { params });
  },
};

export const analiseApi = {
  /** Dispara o cálculo TOPSIS Fuzzy no servidor */
  calcularTopsis(dataInicio, dataFim) {
    return api.post("/calcular-topsis/", {
      data_inicio: dataInicio,
      data_fim: dataFim,
    });
  },

  /** Dispara importação de CSV do INPE via Celery */
  importarCSV(caminho) {
    return api.post("/importar-csv/", { caminho });
  },

  /** Estatísticas gerais para o dashboard */
  getEstatisticas() {
    return api.get("/estatisticas/");
  },
};

export default api;

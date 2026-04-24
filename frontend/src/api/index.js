import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

export const focosApi = {
  async getGeoJSON(params = {}) {
    const { data } = await api.get("/focos/geojson/", { params });
    // API retorna { count, results: FeatureCollection } com paginação
    return { data: data.results ?? data };
  },

  /** Lista simplificada para tabelas */
  getLista(params = {}) {
    return api.get("/focos/", { params });
  },
};

export const areasApi = {
  async getGeoJSON(params = {}) {
    const { data } = await api.get("/areas-risco/geojson/", { params });
    return { data: data.results ?? data };
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

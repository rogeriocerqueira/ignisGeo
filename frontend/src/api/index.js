import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

export const focosApi = {
  async getGeoJSON(params = {}) {
    const { data } = await api.get("/focos/geojson/", { params });
    return { data: data.results ?? data };
  },
  getLista(params = {}) {
    return api.get("/focos/", { params });
  },
};

export const areasApi = {
  async getGeoJSON(params = {}) {
    const { data } = await api.get("/areas-risco/geojson/", { params });
    return { data: data.results ?? data };
  },
  getRanking(params = {}) {
    return api.get("/ranking/", { params });
  },
};

export const analiseApi = {
  /**
   * Dispara o cálculo TOPSIS Fuzzy com os filtros ativos.
   * payload pode conter: data_inicio, data_fim, estado, bioma (todos opcionais)
   */
  calcularTopsis(payload = {}) {
    return api.post("/calcular-topsis/", payload);
  },

  importarCSV(caminho) {
    return api.post("/importar-csv/", { caminho });
  },

  getEstatisticas() {
    return api.get("/estatisticas/");
  },
};

export default api;

import axios from "axios";

// Em produção (Vercel) defina VITE_API_URL com a URL do backend no Render,
// ex.: https://ignisgeo-api.onrender.com. Em desenvolvimento é ignorada e o
// proxy do Vite encaminha /api para o Django (no docker-compose VITE_API_URL
// aponta para http://backend:8000, que só existe dentro da rede do Docker).
const API_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "")
  : "";

const api = axios.create({
  baseURL: `${API_URL}/api`,
  // 60s: no plano grátis o Render "dorme" e a primeira requisição demora
  timeout: 60000,
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
  calcularTopsis(payload = {}) {
    return api.post("/calcular-topsis/", payload);
  },

  importarCSV(caminho) {
    return api.post("/importar-csv/", { caminho });
  },

  // Envia um CSV do INPE a partir do navegador (funciona em produção)
  enviarCSV(arquivo) {
    const form = new FormData();
    form.append("arquivo", arquivo);
    return api.post("/importar-csv/", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 0,
    });
  },

  getEstatisticas(params = {}) {
    return api.get("/estatisticas/", { params });
  },

  /**
   * Agrega AreaRisco por bioma — alimenta o GraficoTopsis3D.
   * Filtros opcionais: estado, nivel_risco, data_inicio, data_fim
   */
  getGraficoBioma(params = {}) {
    return api.get("/grafico-bioma/", { params });
  },
};

export default api;
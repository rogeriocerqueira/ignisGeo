import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { focosApi, areasApi, analiseApi } from "@/api";

export const useQueimadasStore = defineStore("queimadas", () => {
  // --- Estado ---
  const focosGeoJSON = ref(null);
  const areasGeoJSON = ref(null);
  const ranking = ref([]);
  const estatisticas = ref(null);

  const carregando = ref(false);
  const erro = ref(null);

  // Filtros ativos
  const filtros = ref({
    bioma: "",
    estado: "",
    dataInicio: "",
    dataFim: "",
    nivelRisco: "",
  });

  // --- Getters ---
  const totalFocos = computed(() => estatisticas.value?.total_focos ?? 0);
  const areasCriticas = computed(() => estatisticas.value?.areas_criticas ?? 0);
  const porBioma = computed(() => estatisticas.value?.por_bioma ?? []);

  const rankingTop10 = computed(() => ranking.value.slice(0, 10));

  // --- Actions ---
  async function carregarFocosGeoJSON() {
    carregando.value = true;
    erro.value = null;
    try {
      const params = filtrosAtivos();
      const { data } = await focosApi.getGeoJSON(params);
      focosGeoJSON.value = data;
    } catch (e) {
      erro.value = "Erro ao carregar focos de queimada.";
    } finally {
      carregando.value = false;
    }
  }

  async function carregarAreasRisco() {
    carregando.value = true;
    erro.value = null;
    try {
      const params = filtrosAtivos();
      const { data } = await areasApi.getGeoJSON(params);
      areasGeoJSON.value = data;
    } catch (e) {
      erro.value = "Erro ao carregar áreas de risco.";
    } finally {
      carregando.value = false;
    }
  }

  async function carregarRanking() {
    try {
      const { data } = await areasApi.getRanking();
      ranking.value = data.results ?? data;
    } catch (e) {
      erro.value = "Erro ao carregar ranking.";
    }
  }

  async function carregarEstatisticas() {
    try {
      const { data } = await analiseApi.getEstatisticas();
      estatisticas.value = data;
    } catch (e) {
      console.error("Erro ao carregar estatísticas:", e);
    }
  }

  async function executarTopsis(dataInicio, dataFim) {
    carregando.value = true;
    erro.value = null;
    try {
      const { data } = await analiseApi.calcularTopsis(dataInicio, dataFim);
      // Recarrega as áreas após o cálculo
      await carregarAreasRisco();
      await carregarRanking();
      return data;
    } catch (e) {
      erro.value = "Erro ao calcular TOPSIS Fuzzy.";
      throw e;
    } finally {
      carregando.value = false;
    }
  }

  function aplicarFiltros(novosFiltros) {
    filtros.value = { ...filtros.value, ...novosFiltros };
    carregarFocosGeoJSON();
    carregarAreasRisco();
  }

  function limparFiltros() {
    filtros.value = { bioma: "", estado: "", dataInicio: "", dataFim: "", nivelRisco: "" };
    carregarFocosGeoJSON();
    carregarAreasRisco();
  }

  // Monta objeto de params apenas com valores preenchidos
function filtrosAtivos() {
    const mapa = {
        bioma:      "bioma",
        estado:     "estado",
        dataInicio: "data_inicio",
        dataFim:    "data_fim",
        nivelRisco: "nivel_risco",
    };
    return Object.fromEntries(
        Object.entries(filtros.value)
            .filter(([, v]) => v !== "")
            .map(([k, v]) => [mapa[k] || k, v])
    );
}

  // Carrega tudo na inicialização
  async function inicializar() {
    await Promise.all([
      carregarEstatisticas(),
      carregarFocosGeoJSON(),
      carregarAreasRisco(),
      carregarRanking(),
    ]);
  }

  return {
    focosGeoJSON, areasGeoJSON, ranking, estatisticas,
    carregando, erro, filtros,
    totalFocos, areasCriticas, porBioma, rankingTop10,
    carregarFocosGeoJSON, carregarAreasRisco,
    carregarRanking, carregarEstatisticas,
    executarTopsis, aplicarFiltros, limparFiltros, inicializar,
  };
});

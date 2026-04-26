import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { focosApi, areasApi, analiseApi } from "@/api";

export const useQueimadasStore = defineStore("queimadas", () => {
  const focosGeoJSON  = ref(null);
  const areasGeoJSON  = ref(null);
  const ranking       = ref([]);
  const estatisticas  = ref(null);

  const _carregandoCount = ref(0);
  const carregando = computed(() => _carregandoCount.value > 0);

  const erros = ref({ focos: null, areas: null, ranking: null, topsis: null });
  const erro  = computed(() =>
    erros.value.topsis ?? erros.value.focos ?? erros.value.areas ?? erros.value.ranking ?? null
  );

  const filtros = ref({
    bioma:      "",
    estado:     "",
    dataInicio: "",
    dataFim:    "",
    nivelRisco: "",
  });

  const totalFocos    = computed(() => estatisticas.value?.total_focos    ?? 0);
  const areasCriticas = computed(() => estatisticas.value?.areas_criticas ?? 0);
  const porBioma      = computed(() => estatisticas.value?.por_bioma      ?? []);
  const rankingTop10  = computed(() => ranking.value.slice(0, 10));

  function _inc() { _carregandoCount.value++; }
  function _dec() { _carregandoCount.value = Math.max(0, _carregandoCount.value - 1); }

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
        .map(([k, v]) => [mapa[k] ?? k, v])
    );
  }

  async function carregarFocosGeoJSON() {
    _inc();
    erros.value.focos = null;
    try {
      const { data } = await focosApi.getGeoJSON(filtrosAtivos());
      focosGeoJSON.value = data;
    } catch {
      erros.value.focos = "Erro ao carregar focos de queimada.";
    } finally {
      _dec();
    }
  }

  async function carregarAreasRisco() {
    _inc();
    erros.value.areas = null;
    try {
      const { data } = await areasApi.getGeoJSON(filtrosAtivos());
      areasGeoJSON.value = data;
    } catch {
      erros.value.areas = "Erro ao carregar áreas de risco.";
    } finally {
      _dec();
    }
  }

  async function carregarRanking() {
    _inc();
    erros.value.ranking = null;
    try {
      const { data } = await areasApi.getRanking();
      ranking.value = data.results ?? data;
    } catch {
      erros.value.ranking = "Erro ao carregar ranking.";
    } finally {
      _dec();
    }
  }

  async function carregarEstatisticas() {
    _inc();
    try {
      const { data } = await analiseApi.getEstatisticas();
      estatisticas.value = data;
    } catch (e) {
      console.error("Erro ao carregar estatísticas:", e);
    } finally {
      _dec();
    }
  }

async function executarTopsis(dataInicio = null, dataFim = null, estado = null, bioma = null) {
  _inc();
  erros.value.topsis = null;
  try {
    const payload = {};
    if (dataInicio) payload.data_inicio = dataInicio;
    if (dataFim)    payload.data_fim    = dataFim;
    if (estado)     payload.estado      = estado;
    if (bioma)      payload.bioma       = bioma;

    const { data } = await analiseApi.calcularTopsis(payload);
    // Recarrega tudo incluindo estatísticas
    await Promise.all([
      carregarAreasRisco(),
      carregarRanking(),
      carregarEstatisticas(),  // ← adicione esta linha
    ]);
    return data;
  } catch (e) {
    erros.value.topsis = "Erro ao calcular TOPSIS Fuzzy.";
    throw e;
  } finally {
    _dec();
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
    carregando, erro, erros, filtros,
    totalFocos, areasCriticas, porBioma, rankingTop10,
    carregarFocosGeoJSON, carregarAreasRisco,
    carregarRanking, carregarEstatisticas,
    executarTopsis, aplicarFiltros, limparFiltros, inicializar,
  };
});

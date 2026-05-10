import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { focosApi, areasApi, analiseApi } from "@/api";

export const useQueimadasStore = defineStore("queimadas", () => {
  const focosGeoJSON  = ref(null);
  const areasGeoJSON  = ref(null);
  const estatisticas  = ref(null);

  // ── Ranking com paginação ──
  const rankingItems      = ref([]);
  const rankingTotal      = ref(0);
  const rankingPagina     = ref(1);
  const rankingTotalPags  = ref(1);
  const RANKING_PAGE_SIZE = 10;

  // Incrementado após cada TOPSIS para notificar PainelRanking
  const rankingAtualizado = ref(0);

  // ── Dados agregados por bioma (GraficoTopsis3D) ──────────────────────────
  const dadosBioma = ref([]);

  const _carregandoCount = ref(0);
  const carregando = computed(() => _carregandoCount.value > 0);

  const erros = ref({ focos: null, areas: null, ranking: null, topsis: null, bioma: null });
  const erro  = computed(() =>
    erros.value.topsis ?? erros.value.focos ??
    erros.value.areas  ?? erros.value.ranking ?? null
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

  // Compatibilidade com componentes que ainda usam rankingTop10
  const rankingTop10 = computed(() => rankingItems.value.slice(0, 10));

  function _inc() { _carregandoCount.value++; }
  function _dec() { _carregandoCount.value = Math.max(0, _carregandoCount.value - 1); }

  /**
   * Converte chaves camelCase dos filtros para snake_case da API.
   */
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

  async function carregarRanking(pagina = 1) {
    _inc();
    erros.value.ranking = null;
    try {
      const params = {
        ...filtrosAtivos(),
        page:      pagina,
        page_size: RANKING_PAGE_SIZE,
      };
      const { data } = await areasApi.getRanking(params);
      if (data && data.results !== undefined) {
        rankingItems.value     = data.results;
        rankingTotal.value     = data.count ?? 0;
        rankingTotalPags.value = Math.ceil((data.count ?? 0) / RANKING_PAGE_SIZE);
      } else {
        const lista = Array.isArray(data) ? data : [];
        rankingItems.value     = lista;
        rankingTotal.value     = lista.length;
        rankingTotalPags.value = 1;
      }
      rankingPagina.value = pagina;
    } catch {
      erros.value.ranking = "Erro ao carregar ranking.";
      rankingItems.value  = [];
    } finally {
      _dec();
    }
  }

  async function carregarEstatisticas() {
    _inc();
    try {
      const { data } = await analiseApi.getEstatisticas(filtrosAtivos());
      estatisticas.value = data;
    } catch (e) {
      console.error("Erro ao carregar estatísticas:", e);
    } finally {
      _dec();
    }
  }

  /**
   * Carrega dados agregados por bioma para o GraficoTopsis3D.
   * Popula `dadosBioma` com a resposta de /api/grafico-bioma/.
   * Não bloqueia o restante da inicialização.
   */
  async function carregarDadosBioma() {
    _inc();
    erros.value.bioma = null;
    try {
      // Omite filtro de bioma individual (o gráfico mostra todos os biomas)
      const { estado, data_inicio, data_fim } = filtrosAtivos();
      const params = {};
      if (estado)      params.estado      = estado;
      if (data_inicio) params.data_inicio = data_inicio;
      if (data_fim)    params.data_fim    = data_fim;

      const { data } = await analiseApi.getGraficoBioma(params);
      dadosBioma.value = Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Erro ao carregar dados por bioma:", e);
      erros.value.bioma = "Erro ao carregar dados por bioma.";
      dadosBioma.value  = [];     // GraficoTopsis3D usará o fallback sintético
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

      await Promise.all([
        carregarAreasRisco(),
        carregarRanking(1),
        carregarEstatisticas(),
        carregarDadosBioma(),   // ← recarrega bioma após novo TOPSIS
      ]);

      rankingAtualizado.value++;
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
    carregarRanking(1);
    carregarEstatisticas();
    carregarDadosBioma();   // ← atualiza gráfico 3D ao mudar filtros
  }

  function limparFiltros() {
    filtros.value = { bioma: "", estado: "", dataInicio: "", dataFim: "", nivelRisco: "" };
    carregarFocosGeoJSON();
    carregarAreasRisco();
    carregarRanking(1);
    carregarEstatisticas();
    carregarDadosBioma();
  }

  async function inicializar() {
    await Promise.all([
      carregarEstatisticas(),
      carregarFocosGeoJSON(),
      carregarAreasRisco(),
      carregarRanking(1),
      carregarDadosBioma(),   // ← carrega na inicialização junto com o resto
    ]);
  }

  return {
    // Estado reativo
    focosGeoJSON, areasGeoJSON, estatisticas, dadosBioma,
    rankingItems, rankingTotal, rankingPagina, rankingTotalPags,
    rankingAtualizado, carregando, erro, erros, filtros,

    // Computed
    totalFocos, areasCriticas, porBioma, rankingTop10,

    // Ações
    carregarFocosGeoJSON, carregarAreasRisco,
    carregarRanking, carregarEstatisticas, carregarDadosBioma,
    executarTopsis, aplicarFiltros, limparFiltros, inicializar,
    filtrosAtivos,
  };
});
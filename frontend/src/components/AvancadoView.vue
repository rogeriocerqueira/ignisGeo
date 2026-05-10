<template>
  <div class="avancado-page">

    <!-- ── Cabeçalho ── -->
    <div class="page-header">
      <div>
        <h2 class="page-titulo">Análise Avançada</h2>
        <p class="page-sub">
          IgnisGeo · Visualização 3D Fuzzy TOPSIS · Relatório em breve
        </p>
      </div>
      <div class="header-badges">
        <span class="badge azul">TOPSIS Fuzzy — Chen (2000)</span>
        <span class="badge verde">INPE BDQueimadas</span>
        <span v-if="store.carregando" class="badge cinza">⟳ Carregando...</span>
      </div>
    </div>

    <!-- ── Grid principal: 3D | Relatório ── -->
    <div class="grid-principal">

      <!-- ══ Coluna esquerda: Gráfico 3D ══ -->
      <section class="coluna">
        <div class="card">
          <div class="card-header">
            <div class="card-header-esq">
              <span class="card-icone">📊</span>
              <div>
                <span class="card-titulo">Superfície de Risco 3D</span>
                <span class="card-sub">Fuzzy TOPSIS · CCᵢ ∈ [0,1]</span>
              </div>
            </div>
            <span class="card-badge">Plotly 3D</span>
          </div>

          <div class="grafico-area">
            <GraficoTopsis3D :altura="alturaGrafico" />
          </div>

          <p class="card-nota">
            Superfície gerada por interpolação gaussiana dos scores Ci ·
            Picos = maior risco · Eixo Z = índice de proximidade ao ideal positivo ·
            Chen (2000)
          </p>
        </div>
      </section>

      <!-- ══ Coluna direita: Relatório (futuro) ══ -->
      <section class="coluna">
        <div class="card">
          <div class="card-header">
            <div class="card-header-esq">
              <span class="card-icone">📄</span>
              <div>
                <span class="card-titulo">Relatório Técnico</span>
                <span class="card-sub">Exportação · PDF · em breve</span>
              </div>
            </div>
            <span class="badge-em-breve">Em breve</span>
          </div>

          <!-- Placeholder: documento simulado + overlay -->
          <div class="relatorio-placeholder">
            <div class="placeholder-folha">

              <!-- Documento mockado -->
              <div class="ph-header">
                <div class="ph-logo"></div>
                <div class="ph-header-txt">
                  <div class="ph-linha ph-linha-titulo"></div>
                  <div class="ph-linha ph-linha-sub"></div>
                </div>
              </div>
              <div class="ph-divisor"></div>

              <div class="ph-secao">
                <div class="ph-secao-titulo"></div>
                <div class="ph-linha ph-g"></div>
                <div class="ph-linha ph-m"></div>
                <div class="ph-linha ph-p"></div>
              </div>

              <div class="ph-chart-area">
                <div class="ph-bar" style="height:60%;"></div>
                <div class="ph-bar" style="height:85%;"></div>
                <div class="ph-bar" style="height:45%;"></div>
                <div class="ph-bar ph-bar-critico"></div>
                <div class="ph-bar" style="height:72%;"></div>
                <div class="ph-bar" style="height:38%;"></div>
              </div>

              <div class="ph-secao">
                <div class="ph-secao-titulo"></div>
                <div class="ph-tabela">
                  <div class="ph-tr ph-tr-header">
                    <div class="ph-td ph-td-nome"></div>
                    <div class="ph-td ph-td-valor"></div>
                    <div class="ph-td ph-td-valor"></div>
                  </div>
                  <div class="ph-tr">
                    <div class="ph-td ph-td-nome"></div>
                    <div class="ph-td ph-td-valor ph-td-critico"></div>
                    <div class="ph-td ph-td-valor"></div>
                  </div>
                  <div class="ph-tr">
                    <div class="ph-td ph-td-nome"></div>
                    <div class="ph-td ph-td-valor ph-td-alto"></div>
                    <div class="ph-td ph-td-valor"></div>
                  </div>
                  <div class="ph-tr">
                    <div class="ph-td ph-td-nome"></div>
                    <div class="ph-td ph-td-valor ph-td-baixo"></div>
                    <div class="ph-td ph-td-valor"></div>
                  </div>
                </div>
              </div>

              <div class="ph-secao">
                <div class="ph-linha ph-g"></div>
                <div class="ph-linha ph-m"></div>
              </div>

              <!-- Overlay -->
              <div class="ph-overlay">
                <div class="ph-overlay-card">
                  <span class="ph-overlay-icone">🚧</span>
                  <p class="ph-overlay-titulo">Funcionalidade em desenvolvimento</p>
                  <p class="ph-overlay-desc">
                    O relatório técnico exportará os resultados do TOPSIS Fuzzy em PDF,
                    com gráficos, ranking completo e análise de correlação.
                  </p>
                  <div class="ph-features">
                    <div class="ph-feature">
                      <span class="ph-feature-icone">📈</span>
                      <span>Gráficos de ranking e distribuição</span>
                    </div>
                    <div class="ph-feature">
                      <span class="ph-feature-icone">🏆</span>
                      <span>Top municípios por nível de risco</span>
                    </div>
                    <div class="ph-feature">
                      <span class="ph-feature-icone">🔢</span>
                      <span>Matriz de correlação dos critérios</span>
                    </div>
                    <div class="ph-feature">
                      <span class="ph-feature-icone">📋</span>
                      <span>Metodologia e referências — Chen (2000)</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useQueimadasStore } from '@/stores/queimadas'
import GraficoTopsis3D from '@/components/GraficoTopsis3D.vue'

const store = useQueimadasStore()

const alturaGrafico = computed(() => {
  if (window.innerHeight > 900) return 520
  if (window.innerHeight > 700) return 440
  return 380
})
</script>

<style scoped>
/* ── Página ── */
.avancado-page {
  padding: 20px 24px;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ── Cabeçalho ── */
.page-header {
  display: flex; align-items: flex-start;
  justify-content: space-between; flex-wrap: wrap;
  gap: 12px; margin-bottom: 20px; flex-shrink: 0;
}
.page-titulo { font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 3px; }
.page-sub    { font-size: 12px; color: #4B5563; }

.header-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.badge { font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 500; }
.badge.azul  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge.verde { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.badge.cinza { background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB; }

/* ── Grid ── */
.grid-principal {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
  padding-bottom: 24px;
}

.coluna { display: flex; flex-direction: column; }

/* ── Card ── */
.card {
  flex: 1;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #E5E7EB;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.card-header {
  display: flex; align-items: center;
  justify-content: space-between;
  margin-bottom: 14px; gap: 8px; flex-shrink: 0;
}
.card-header-esq { display: flex; align-items: center; gap: 10px; }
.card-icone  { font-size: 18px; }
.card-titulo { display: block; font-size: 13px; font-weight: 600; color: #111827; }
.card-sub    { display: block; font-size: 10px; color: #6B7280; margin-top: 1px; }
.card-badge  {
  font-size: 10px; padding: 2px 8px;
  background: #F3F4F6; color: #4B5563;
  border-radius: 999px; white-space: nowrap;
}
.card-nota {
  font-size: 10px; color: #4B5563;
  margin-top: 10px; font-style: italic; line-height: 1.5; flex-shrink: 0;
}

.badge-em-breve {
  font-size: 10px; font-weight: 600;
  padding: 3px 10px; border-radius: 999px;
  background: #FFF7ED; color: #C2410C;
  border: 1px solid #FED7AA;
}

/* ── Área do gráfico ── */
.grafico-area {
  flex: 1;
  min-height: 0;
  border-radius: 6px;
  overflow: hidden;
}

/* ── Placeholder relatório ── */
.relatorio-placeholder {
  flex: 1;
  min-height: 0;
  display: flex;
}

.placeholder-folha {
  flex: 1;
  border: 1px dashed #D1D5DB;
  border-radius: 8px;
  padding: 16px;
  background: #FAFAFA;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  overflow: hidden;
  min-height: 360px;
}

/* ── Mockup do documento ── */
.ph-header { display: flex; gap: 10px; align-items: center; }
.ph-logo   {
  width: 28px; height: 28px; border-radius: 6px;
  background: #DBEAFE; flex-shrink: 0;
}
.ph-header-txt { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.ph-linha      { height: 6px; background: #E5E7EB; border-radius: 3px; }
.ph-linha-titulo { width: 60%; background: #BFDBFE; }
.ph-linha-sub    { width: 40%; }
.ph-g { width: 90%; }
.ph-m { width: 70%; }
.ph-p { width: 50%; }

.ph-divisor { height: 1px; background: #E5E7EB; flex-shrink: 0; }

.ph-secao { display: flex; flex-direction: column; gap: 5px; }
.ph-secao-titulo {
  height: 7px; width: 30%;
  background: #93C5FD; border-radius: 3px;
}

.ph-chart-area {
  display: flex; align-items: flex-end;
  gap: 4px; height: 56px; flex-shrink: 0;
}
.ph-bar {
  flex: 1; border-radius: 3px 3px 0 0;
  background: #BFDBFE;
}
.ph-bar-critico { height: 100%; background: #FCA5A5; }

.ph-tabela { display: flex; flex-direction: column; gap: 0; }
.ph-tr { display: flex; gap: 6px; padding: 4px 0; border-bottom: 1px solid #F3F4F6; }
.ph-tr-header .ph-td { background: #E5E7EB; }
.ph-td { height: 6px; border-radius: 2px; background: #E5E7EB; margin-top: 4px; }
.ph-td-nome      { flex: 2; }
.ph-td-valor     { flex: 1; }
.ph-td-critico   { background: #FCA5A5; }
.ph-td-alto      { background: #FCD34D; }
.ph-td-baixo     { background: #6EE7B7; }

/* ── Overlay ── */
.ph-overlay {
  position: absolute; inset: 0;
  background: rgba(249, 250, 251, 0.88);
  backdrop-filter: blur(3px);
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px; padding: 20px;
}

.ph-overlay-card {
  text-align: center; max-width: 280px;
  display: flex; flex-direction: column;
  align-items: center; gap: 10px;
}
.ph-overlay-icone  { font-size: 30px; }
.ph-overlay-titulo { font-size: 13px; font-weight: 600; color: #111827; margin: 0; }
.ph-overlay-desc   { font-size: 11px; color: #4B5563; line-height: 1.6; margin: 0; }

.ph-features { display: flex; flex-direction: column; gap: 6px; align-self: stretch; }
.ph-feature {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; color: #374151; text-align: left;
  background: #F9FAFB; border: 1px solid #E5E7EB;
  border-radius: 6px; padding: 6px 10px;
}
.ph-feature-icone { font-size: 13px; flex-shrink: 0; }

/* ── Responsivo ── */
@media (max-width: 900px) {
  .grid-principal { grid-template-columns: 1fr; }
}
</style>

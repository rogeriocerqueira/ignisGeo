# Padrões de Commits — IgnisGeo

Convenção baseada no Conventional Commits (conventionalcommits.org),
adaptada ao fluxo real de desenvolvimento do projeto.

---

## Estrutura do commit

```
<tipo>(<escopo>): <descrição curta no imperativo>

[corpo opcional — o que e por que, não como]

[rodapé opcional — breaking changes, closes #issue]
```

### Regras gerais

- Primeira linha: máximo 72 caracteres
- Descrição em português, no imperativo ("adiciona", "corrige", "remove")
- Sem ponto final na primeira linha
- Corpo separado da primeira linha por uma linha em branco
- Uma mudança lógica por commit

---

## Tipos

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade para o usuário |
| `fix` | Correção de bug |
| `refactor` | Mudança de código sem alterar comportamento externo |
| `style` | Alterações visuais/CSS sem impacto funcional |
| `perf` | Melhoria de desempenho |
| `docs` | Documentação, comentários, READMEs |
| `test` | Adição ou correção de testes |
| `chore` | Configuração, dependências, scripts, Docker |
| `data` | Importação, migração ou atualização de dados |

---

## Escopos do projeto

| Escopo | Área |
|---|---|
| `topsis` | Algoritmo TOPSIS Fuzzy e pipeline de cálculo |
| `ranking` | Endpoint, paginação e serializer do ranking |
| `graficos` | Página de resultados e gráficos (G1–G8) |
| `mapa` | Componente Leaflet e camadas do mapa |
| `filtros` | Painel de filtros e store de filtros |
| `store` | Pinia store (queimadas.js) |
| `api` | Endpoints DRF, views.py, urls.py |
| `serializer` | Serializers do DRF |
| `models` | Models Django e migrações |
| `auth` | Autenticação e permissões |
| `docker` | Docker Compose e configuração de containers |
| `dados` | Importação de CSVs do INPE e processamento |
| `latex` | Documentação do TCC em LaTeX |
| `ci` | GitHub Actions e pipelines |

---

## Exemplos reais do projeto

### feat — nova funcionalidade

```
feat(graficos): adiciona histograma de densidade com curva Normal

Substitui histograma de frequência absoluta por densidade normalizada
(count / N × binWidth), permitindo que a curva Normal compartilhe a
mesma escala Y sem achatamento visual.

Inclui toggle para exibir N(μ, σ) e destaque da região crítica.
```

```
feat(graficos): adiciona matriz de correlação Pearson e Spearman

Implementa endpoint /api/correlacao/ com calculo de r e rho (5x5)
e p-valores via teste t bilateral (metodo de Lentz, 50 iteracoes).
Frontend renderiza heatmap divergente azul-branco-vermelho com
stars de significancia e toggle entre os dois tipos de correlacao.
```

```
feat(api): adiciona endpoints serie-temporal e graficos-dados

serie-temporal agrega focos por mes via TruncMonth.
graficos-dados consolida dados dos 7 graficos em uma unica chamada,
reduzindo de 7 para 1 requisicao HTTP na tela de Resultados.
```

```
feat(ranking): adiciona paginacao de 10 registros por pagina

Cria RankingPagination com page_size=10 e max_page_size=100.
Expoe page_size como query param para flexibilidade nos clientes.
```

```
feat(mapa): calcula centroide geografico via PostGIS no TOPSIS

Usa Centroid(Union(localizacao)) para gerar geometria Point de cada
municipio sem depender de shapefile externo do IBGE.
Camada de areas de risco agora renderiza circulos no Leaflet.
```

```
feat(graficos): adiciona boxplot manual com whiskers 1.5xIQR

Calcula Q1, Q2, Q3, IQR e outliers diretamente nos scores reais
retornados pelo endpoint graficos-dados. Exibe mediana numerica
abaixo de cada caixa e label do nivel no eixo X.
```

```
feat(graficos): adiciona paginacao na tabela de resultados

Pagina de 5 em 5 com botoes Anterior, numericos e Proxima.
Computed top10Paginado deriva slice da lista completa sem nova
requisicao ao backend.
```

---

### fix — correção de bug

```
fix(topsis): corrige typo dias_sem_chuva_meio para dias_sem_chuva_medio

O nome incorreto causava IntegrityError no bulk_create pois o campo
do model e dias_sem_chuva_medio. TOPSIS retornava 500 para qualquer
execucao com dados reais.
```

```
fix(ranking): corrige filtro nivel_risco ignorado no PainelRanking

PainelRanking fazia axios proprio sem converter camelCase para
snake_case, ignorando nivel_risco enviado pela store. Solucao:
remove axios do componente e centraliza todo fetch na store.
```

```
fix(ranking): adiciona pagination_class ausente na RankingView

Sem RankingPagination a view retornava todos os registros de uma vez,
ignorando os parametros page e page_size da query string.
```

```
fix(mapa): define corPorNivel ausente no MapaQueimadas

ReferenceError em producao: corPorNivel era usado em renderizarAreas
mas nunca declarado no script. Adiciona mapeamento completo
CRITICO/ALTO/MEDIO/BAIXO com as mesmas cores da legenda.
```

```
fix(mapa): substitui style() por pointToLayer para geometria Point

style() so funciona para Polygon e LineString no Leaflet GeoJSON.
Areas de risco sao agora Point (centroide PostGIS), exigindo
pointToLayer com circleMarker. Raio proporcional ao score TOPSIS.
```

```
fix(graficos): corrige escala incompativel entre histograma e curva Gauss

Histograma usava frequencia absoluta (ate 40) enquanto curva Normal
retornava densidade de probabilidade (cerca de 0.001), resultando
em curva achatada no rodape. Ambos agora usam densidade normalizada.
```

---

### refactor — sem mudança de comportamento

```
refactor(store): centraliza carregarRanking na store queimadas

Elimina duplicacao de logica de paginacao entre PainelRanking e store.
Store expoe rankingItems, rankingPagina e rankingTotalPags como state;
componente apenas chama store.carregarRanking(pagina).
```

```
refactor(api): consolida filtros com conversao camelCase para snake_case

filtrosAtivos() na store agora mapeia dataInicio/dataFim/nivelRisco
para data_inicio/data_fim/nivel_risco antes de enviar ao DRF,
evitando que cada componente faca a conversao manualmente.
```

```
refactor(topsis): extrai calculo de centroide em query separada

Separa Union/Centroid em geo_qs antes do bulk_create para deixar
a logica do pipeline legivel. geo_map indexado por (municipio, estado,
bioma) para lookup O(1) na criacao de cada AreaRisco.
```

---

### style — visual, sem comportamento

```
style(graficos): escurece textos secundarios de #9CA3AF para #4B5563

Melhora legibilidade em escala de cinza: card-nota, tabela-ref,
rank-cell, card-badge, tipo-btn e interp-desc. Textos de apoio
permanecem em #374151 para hierarquia visual adequada.
```

```
style(graficos): adiciona rotulos dos eixos X e Y na serie temporal

Eixo Y "No de Focos" rotacionado 90 graus; eixo X "Mes" centralizado.
Aumenta PL de 52 para 68 e PB de 28 para 44 para acomodar rotulos.
Padrao obrigatorio em graficos de artigos cientificos (ABNT/ISO).
```

```
style(graficos): reescreve layout do Top 10 com colunas fixas e clipping

Substitui textAlign:right com posicoes implicitas por tres colunas
fixas: COL_RANK (32px), COL_NOME (195px) e area de barras.
ctx.clip() impede que nomes longos vazem para a coluna de barras.
Municipio em negrito na linha superior, UF/Bioma em cinza abaixo.
```

---

### perf — desempenho

```
perf(api): reduz requisicoes da tela de Resultados de 7 para 1

graficos-dados agrega por_bioma, serie_temporal, top10, top5_radar,
scores_por_nivel e scatter em uma unica query set ao banco.
Amostras limitadas a 500 scores por nivel para evitar payloads grandes.
```

---

### docs — documentação

```
docs(latex): adiciona secao de endpoints REST com tabela sintetica

Tabela Tabela 2 com colunas Endpoint, Metodo e Descricao usando
booktabs, tabularx e colortbl. Badges GET/POST coloridos com
\colorbox. Compilado sem erros no Overleaf (pdflatex, duas passagens).
```

```
docs(readme): atualiza instrucoes de deploy com novos endpoints

Documenta /api/correlacao/, /api/serie-temporal/ e /api/graficos-dados/
com parametros aceitos e formato de resposta.
```

---

### data — dados

```
data(inpe): importa focos de queimada jan/2025 a abr/2026

Total de 3.876.956 focos distribuidos em 27 estados.
Arquivo CSV processado via tarefa Celery importar_csv_inpe.
```

```
data(topsis): executa ranking com dados completos jan/2025-abr/2026

6.195 areas ranqueadas: 620 Critico, 934 Alto, 1545 Medio, 3096 Baixo.
Top 1: BARRA/BA/CERRADO com CC=0.5209.
```

---

### chore — infraestrutura

```
chore(docker): atualiza docker-compose com container PostGIS 3.4

Substitui postgres:15 por postgis/postgis:16-3.4. Adiciona variavel
POSTGRES_DB e monta volume para persistencia entre restarts.
```

---

## Nomenclatura de branches

```
<tipo>/<descricao-curta-com-hifens>
```

| Exemplo | Quando usar |
|---|---|
| `feat/graficos-correlacao-heatmap` | Nova funcionalidade de graficos |
| `feat/mapa-areas-risco-centroide` | Nova funcionalidade no mapa |
| `fix/ranking-paginacao-nivel-risco` | Correcao de bug no ranking |
| `fix/topsis-typo-dias-sem-chuva` | Correcao de typo critico |
| `refactor/store-centralizar-ranking` | Refatoracao da store |
| `style/graficos-contraste-textos` | Ajustes visuais sem comportamento |
| `display-result-add-new-features` | Multiplas features na tela Resultados (*) |
| `docs/latex-endpoints-tabela` | Documentacao do TCC |
| `data/importacao-focos-2026` | Importacao de dados |

(*) Branches de feature ampla podem agregar multiplos commits
de tipos diferentes (feat, fix, style, refactor) antes do merge.

---

## Fluxo recomendado para a branch display-result-add-new-features

```bash
# 1. Commits atomicos durante o desenvolvimento
git add frontend/src/components/GraficosView.vue
git commit -m "feat(graficos): adiciona histograma de densidade com curva Normal"

git add frontend/src/components/GraficosView.vue
git commit -m "fix(graficos): corrige escala incompativel histograma e curva Gauss"

git add frontend/src/components/GraficosView.vue
git commit -m "style(graficos): escurece textos secundarios de #9CA3AF para #4B5563"

git add backend/queimadas/views.py backend/queimadas/urls.py
git commit -m "feat(api): adiciona endpoints serie-temporal e graficos-dados"

git add backend/queimadas/views.py
git commit -m "feat(graficos): adiciona matriz de correlacao Pearson e Spearman"

git add frontend/src/components/GraficosView.vue
git commit -m "feat(graficos): adiciona heatmap de correlacao com toggle Pearson-Spearman"

git add frontend/src/components/GraficosView.vue
git commit -m "feat(graficos): adiciona paginacao na tabela de resultados"

git add frontend/src/components/GraficosView.vue
git commit -m "style(graficos): adiciona rotulos dos eixos X e Y na serie temporal"

git add frontend/src/components/GraficosView.vue
git commit -m "style(graficos): reescreve layout do Top 10 com colunas fixas e clipping"

# 2. Push e PR
git push origin display-result-add-new-features

# 3. Merge na main com mensagem de merge descritiva
# "feat(graficos): tela de Resultados com 8 graficos dinamicos e correlacao"
```

---

## Commit de fechamento da branch atual (sugestao)

```
feat(graficos): implementa tela de Resultados com 8 graficos e correlacao

Graficos dinamicos via Canvas 2D com dados reais do banco:
- G1 focos por bioma (barras horizontais)
- G2 serie temporal mensal com eixos rotulados
- G3 top 10 ranking com colunas fixas e clipping de nomes
- G4 radar multicritério top 5 normalizado
- G5 scatter score x focos por nivel (escala log)
- G6 histograma de densidade com curva Normal unica (μ, σ)
- G7 boxplot por nivel com whiskers 1.5xIQR
- G8 heatmap de correlacao Pearson/Spearman com p-valores

Backend: endpoints /api/graficos-dados/, /api/serie-temporal/
e /api/correlacao/ (Python puro, sem NumPy).

Textos secundarios escurecidos de #9CA3AF para #4B5563.
Tabela de resultados com paginacao de 5 em 5.
```

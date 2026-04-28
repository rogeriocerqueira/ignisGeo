# Roda só os testes do TOPSIS com output detalhado
docker compose exec backend python manage.py test \
  queimadas.tests.TopsisTest \
  queimadas.tests.NumeroFuzzyTest \
  queimadas.tests.NormalizarFuzzyTest \
  -v 2

# Para inspecionar valores intermediários, abra o shell
docker compose exec backend python manage.py shell -c "
from queimadas.topsis_fuzzy import *

# Teste manual
a = NumeroFuzzy(0.0, 0.0, 0.0)
b = NumeroFuzzy(0.1, 0.2, 0.3)
print('Distância:', a.distancia(b))

# Normalização
nf = normalizar_fuzzy(50.0, 0.0, 100.0)
print('TFN:', nf.a, nf.b, nf.c)

# TOPSIS completo com 2 alternativas
alts = [
    {'nome':'Baixo','municipio':'Baixo','estado':'AL','bioma':'CAATINGA',
     'total_focos':10,'frp_media':5.0,'risco_historico_medio':0.1,
     'vento_medio':1.0,'ndvi_medio':0.8},
    {'nome':'Alto','municipio':'Alto','estado':'AL','bioma':'CAATINGA',
     'total_focos':500,'frp_media':200.0,'risco_historico_medio':0.9,
     'vento_medio':8.0,'ndvi_medio':0.1},
]
resultado = calcular_topsis_fuzzy(alts)
for r in resultado:
    print(r['nome'], r['score_topsis'], r['nivel_risco'], r['ranking'])
"
# Deploy do IgnisGeo

| Parte | Onde | Custo |
|---|---|---|
| API Django + GeoDjango (Docker) | Render — Web Service | grátis (dorme após 15 min sem acesso) |
| PostgreSQL + PostGIS | Render — Postgres | grátis por 30 dias |
| Frontend Vue (Vite) | Vercel | grátis |

No plano grátis não há worker do Celery nem Redis: com `CELERY_TASK_ALWAYS_EAGER=True`
as tarefas rodam dentro do próprio processo web. O `docker-compose` local continua igual.

---

## 1. Backend no Render

1. Faça o commit destes arquivos e dê push para o GitHub.
2. No [Render](https://dashboard.render.com): **New + → Blueprint** → conecte o GitHub → escolha `ignisGeo`.
3. O Render lê o `render.yaml` e cria `ignisgeo-db` (Postgres) e `ignisgeo-api` (Docker).
   Ele vai pedir o valor de `CORS_ALLOWED_ORIGINS`: deixe em branco por enquanto.
4. Aguarde o build (o primeiro leva ~5–10 min por causa do GDAL).
   O `start.sh` roda `migrate` (que ativa a extensão PostGIS), `collectstatic` e sobe o Gunicorn.
5. Teste: `https://ignisgeo-api.onrender.com/api/estatisticas/` deve responder um JSON.

> A URL real aparece no topo da página do serviço. Se o nome `ignisgeo-api` já estiver em uso, o Render acrescenta um sufixo.

## 2. Frontend no Vercel

1. No [Vercel](https://vercel.com/new): **Add New → Project** → importe `ignisGeo`.
2. **Root Directory:** `frontend` (o preset Vite é detectado sozinho).
3. **Environment Variables:** `VITE_API_URL` = URL do backend, sem barra no final
   (ex.: `https://ignisgeo-api.onrender.com`).
4. **Deploy.**

## 3. Liberar o CORS

No Render → `ignisgeo-api` → **Environment**:

- `CORS_ALLOWED_ORIGINS` = URL do Vercel (ex.: `https://ignisgeo.vercel.app`). Para mais de uma, separe por vírgulas.
- `CORS_ALLOWED_ORIGIN_REGEXES` já libera os previews `https://ignisgeo*.vercel.app`. Ajuste se o projeto no Vercel tiver outro nome.

Salve (o Render reinicia sozinho) e abra o site no Vercel.

## 4. Carregar os dados do INPE

O servidor não tem a pasta `data/`, então há duas formas:

**Enviando o CSV pela API** (arquivos de até algumas dezenas de MB):

```bash
curl -X POST https://ignisgeo-api.onrender.com/api/importar-csv/ \
  -F "arquivo=@data/focos_br_ref_2024.csv"

curl -X POST https://ignisgeo-api.onrender.com/api/calcular-topsis/ \
  -H "Content-Type: application/json" \
  -d '{"data_inicio": "2024-01-01", "data_fim": "2024-01-31"}'
```

**Da sua máquina direto no banco do Render** (melhor para arquivos grandes):

Copie a **External Database URL** em Render → `ignisgeo-db` → **Connect**, e rode:

```bash
docker compose run --rm -e DATABASE_URL="<External Database URL>" \
  backend python manage.py importar_csv /app/data/focos_br_ref_2024.csv
```

Depois chame o `calcular-topsis` como acima.

> A importação não evita duplicatas: importar o mesmo CSV duas vezes duplica os focos.

## Avisos do plano grátis

- **O banco do Render expira em 30 dias.** Antes disso, passe para um plano pago (Basic, a partir de ~US$ 6/mês)
  ou migre para um Postgres grátis com PostGIS (ex.: Neon ou Supabase) e troque só a variável `DATABASE_URL`.
- **O backend dorme** após 15 min sem acesso; a primeira requisição depois disso leva ~1 min.
  O frontend já espera até 60 s.
- 512 MB de RAM: o TOPSIS com muitos municípios ou CSVs enormes pela API podem estourar. Nesse caso, use o comando local.

## Variáveis de ambiente do backend

| Variável | Uso |
|---|---|
| `DATABASE_URL` | Postgres/PostGIS (o Render preenche) |
| `SECRET_KEY` | gerada pelo Render |
| `DEBUG` | `False` em produção |
| `ALLOWED_HOSTS` | `.onrender.com` (+ domínio próprio, se houver) |
| `CORS_ALLOWED_ORIGINS` | URLs do frontend, separadas por vírgula |
| `CORS_ALLOWED_ORIGIN_REGEXES` | regex para previews do Vercel |
| `CSRF_TRUSTED_ORIGINS` | opcional, para usar o `/admin` a partir de outro domínio |
| `CELERY_TASK_ALWAYS_EAGER` | `True` sem worker/Redis |
| `REDIS_URL` | só se você adicionar Redis + worker (planos pagos) |

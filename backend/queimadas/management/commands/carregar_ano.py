"""
Carrega focos do CSV do INPE para o banco, filtrando por ano, usando COPY.

Muito mais rápido que o bulk_create do Django: indicado para enviar
milhões de linhas da sua máquina para o banco do Render.

Exemplos (dentro do docker-compose, com DATABASE_URL apontando para o Render):
    python manage.py carregar_ano /app/data/focos.csv --ano 2024 --contar
    python manage.py carregar_ano /app/data/focos.csv --ano 2024
    python manage.py carregar_ano /app/data/focos.csv --ano 2024 --substituir
"""
import csv
import io
import time
from datetime import timezone

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from queimadas.models import FocoQueimada
from queimadas.tasks import parse_linha

COLUNAS = (
    "localizacao", "data_hora", "municipio", "estado", "bioma", "satelite",
    "frp", "risco_historico", "dias_sem_chuva", "precipitacao", "criado_em",
)


def _num(valor):
    return "" if valor is None else repr(float(valor))


class Command(BaseCommand):
    help = "Importa os focos de um ano do CSV do INPE via COPY (rápido)."

    def add_arguments(self, parser):
        parser.add_argument("caminho", help="Caminho do CSV do INPE")
        parser.add_argument("--ano", type=int, required=True, help="Ano a importar, ex.: 2024")
        parser.add_argument("--lote", type=int, default=50_000, help="Linhas por envio (padrão 50 mil)")
        parser.add_argument("--contar", action="store_true",
                            help="Só conta quantas linhas do ano existem no CSV, sem gravar nada")
        parser.add_argument("--substituir", action="store_true",
                            help="Apaga os focos desse ano no banco antes de importar (evita duplicar)")

    def handle(self, *args, caminho, ano, lote, contar, substituir, **options):
        tabela = FocoQueimada._meta.db_table
        agora = time.strftime("%Y-%m-%d %H:%M:%S+00", time.gmtime())

        try:
            arquivo = open(caminho, encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            raise CommandError(f"Arquivo não encontrado: {caminho}")

        if not contar:
            with connection.cursor() as cur:
                cur.execute(f"SELECT count(*) FROM {tabela} WHERE date_part('year', data_hora) = %s", [ano])
                existentes = cur.fetchone()[0]
            if existentes and not substituir:
                raise CommandError(
                    f"Já existem {existentes:,} focos de {ano} no banco. "
                    "Use --substituir para apagar e importar de novo."
                )
            if existentes and substituir:
                with connection.cursor() as cur:
                    cur.execute(f"DELETE FROM {tabela} WHERE date_part('year', data_hora) = %s", [ano])
                self.stdout.write(f"Apagados {existentes:,} focos de {ano}.")

        lidas = do_ano = invalidas = enviadas = 0
        buffer = io.StringIO()
        escritor = csv.writer(buffer, lineterminator="\n")
        inicio = time.time()

        def enviar():
            nonlocal buffer, escritor, enviadas
            if buffer.tell() == 0:
                return
            buffer.seek(0)
            with transaction.atomic(), connection.cursor() as cur:
                cur.copy_expert(
                    f"COPY {tabela} ({', '.join(COLUNAS)}) FROM STDIN WITH (FORMAT csv)",
                    buffer,
                )
            enviadas = do_ano
            self.stdout.write(f"  enviadas {enviadas:,} linhas ({time.time() - inicio:.0f}s)")
            buffer = io.StringIO()
            escritor = csv.writer(buffer, lineterminator="\n")

        with arquivo:
            for linha in csv.DictReader(arquivo):
                lidas += 1
                dados = parse_linha(linha)
                if dados is None:
                    invalidas += 1
                    continue
                if dados["data_hora"].year != ano:
                    continue
                do_ano += 1
                if contar:
                    continue

                ponto = dados["localizacao"]
                data_hora = dados["data_hora"].replace(tzinfo=timezone.utc)  # INPE usa GMT
                escritor.writerow([
                    f"SRID=4326;POINT({ponto.x!r} {ponto.y!r})",
                    data_hora.isoformat(),
                    dados["municipio"][:100],
                    dados["estado"][:2],
                    dados["bioma"],
                    dados["satelite"][:50],
                    _num(dados["frp"]),
                    _num(dados["risco_historico"]),
                    _num(dados["dias_sem_chuva"]),
                    _num(dados["precipitacao"]),
                    agora,
                ])
                if do_ano % lote == 0:
                    enviar()

        if contar:
            mb = do_ano * 300 / 1_000_000  # ~300 bytes por foco com índices
            self.stdout.write(self.style.SUCCESS(
                f"{do_ano:,} focos de {ano} no CSV (de {lidas:,} linhas; {invalidas:,} inválidas). "
                f"Espaço estimado no banco: ~{mb:,.0f} MB."
            ))
            return

        enviar()
        with connection.cursor() as cur:
            cur.execute(f"ANALYZE {tabela}")
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            tamanho = cur.fetchone()[0]
        self.stdout.write(self.style.SUCCESS(
            f"Ano {ano}: {do_ano:,} focos importados em {time.time() - inicio:.0f}s "
            f"({invalidas:,} linhas inválidas no CSV). Tamanho do banco agora: {tamanho}."
        ))

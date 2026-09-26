from django.core.management.base import BaseCommand, CommandError

from queimadas.tasks import processar_csv


class Command(BaseCommand):
    help = (
        "Importa um CSV do INPE BDQueimadas direto no banco configurado em "
        "DATABASE_URL (útil para carregar o banco de produção a partir da sua máquina)."
    )

    def add_arguments(self, parser):
        parser.add_argument("caminho", help="Caminho do arquivo CSV do INPE")

    def handle(self, *args, **options):
        caminho = options["caminho"]
        try:
            resultado = processar_csv(caminho)
        except FileNotFoundError:
            raise CommandError(f"Arquivo não encontrado: {caminho}")
        self.stdout.write(self.style.SUCCESS(
            f"Importação concluída: {resultado['importados']} focos, "
            f"{resultado['erros']} linhas ignoradas."
        ))

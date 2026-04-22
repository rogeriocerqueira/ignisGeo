import csv
import logging
from datetime import datetime

from celery import shared_task
from django.contrib.gis.geos import Point

from .models import FocoQueimada

logger = logging.getLogger(__name__)

# Mapeamento de biomas do CSV do INPE para os choices do model
MAPA_BIOMAS = {
    "amazônia":       "AMAZONIA",
    "amazonia":       "AMAZONIA",
    "cerrado":        "CERRADO",
    "caatinga":       "CAATINGA",
    "mata atlântica": "MATA_ATLANTICA",
    "mata atlantica": "MATA_ATLANTICA",
    "pantanal":       "PANTANAL",
    "pampa":          "PAMPA",
}

def normalizar_bioma(valor: str) -> str:
    return MAPA_BIOMAS.get(valor.strip().lower(), "CERRADO")


def parse_linha(linha: dict) -> dict | None:
    """
    Converte uma linha do CSV do INPE BDQueimadas para o formato do model.

    Colunas esperadas:
      DataHora, Satelite, Pais, Estado, Municipio, Bioma,
      DiaSemChuva, Precipitacao, RiscoFogo, FRP, Latitude, Longitude
    """
    try:
        lat = float(linha.get("Latitude") or linha.get("lat") or 0)
        lon = float(linha.get("Longitude") or linha.get("lon") or 0)

        # Formatos de data aceitos pelo INPE
        data_raw = (
            linha.get("DataHora")
            or linha.get("data_hora_gmt")
            or linha.get("data_hora", "")
        ).strip()

        data_hora = None
        for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
            try:
                data_hora = datetime.strptime(data_raw, fmt)
                break
            except ValueError:
                continue

        if data_hora is None:
            return None

        frp_raw = linha.get("FRP") or linha.get("frp") or "0"
        frp = float(str(frp_raw).strip() or "0")

        risco_raw = linha.get("RiscoFogo") or linha.get("risco_historico") or "0"
        risco = float(str(risco_raw).strip() or "0")
        if risco < 0:
            risco = 0.0

        return {
            "localizacao": Point(lon, lat, srid=4326),
            "data_hora":   data_hora,
            "municipio":   (linha.get("Municipio") or linha.get("municipio") or "").strip(),
            "estado":      (linha.get("Estado")    or linha.get("estado")    or "")[:2].upper(),
            "bioma":       normalizar_bioma(linha.get("Bioma") or linha.get("bioma") or ""),
            "frp":              frp,
            "risco_historico":  round(risco, 4),
            "satelite":    (linha.get("Satelite") or linha.get("satelite") or "").strip(),
            "vento_ms":    None,
            "ndvi":        None,
        }

    except (ValueError, TypeError):
        return None


@shared_task(bind=True, max_retries=3)
def importar_csv_inpe(self, caminho_csv: str):
    """
    Importa CSV do INPE BDQueimadas para o banco PostGIS.
    Aceita o formato padrão do BDQueimadas:
      DataHora,Satelite,Pais,Estado,Municipio,Bioma,
      DiaSemChuva,Precipitacao,RiscoFogo,FRP,Latitude,Longitude
    """
    importados = 0
    erros = 0

    try:
        with open(caminho_csv, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            lote = []

            for linha in reader:
                dados = parse_linha(linha)
                if dados is None:
                    erros += 1
                    continue

                lote.append(FocoQueimada(**dados))

                if len(lote) >= 500:
                    FocoQueimada.objects.bulk_create(lote, ignore_conflicts=True)
                    importados += len(lote)
                    logger.info(f"Importados {importados} focos...")
                    lote = []

            if lote:
                FocoQueimada.objects.bulk_create(lote, ignore_conflicts=True)
                importados += len(lote)

    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {caminho_csv}")
        raise self.retry(countdown=60)
    except Exception as exc:
        logger.error(f"Erro ao importar CSV: {exc}")
        raise self.retry(exc=exc, countdown=120)

    logger.info(f"Importação concluída: {importados} focos, {erros} erros.")
    return {"importados": importados, "erros": erros}
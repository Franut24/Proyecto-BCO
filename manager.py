from typing import Dict, List, Optional, Callable
from models import Promocion, SyncLog
from database import DatabaseManager
from config import logger
from .santander import SantanderScraper
from .hipotecario import HipotecarioScraper
from .supervielle import SupervielleScraper

class ScraperManager:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.scrapers = {
            "Santander": SantanderScraper(),
            "Banco Hipotecario": HipotecarioScraper(),
            "Supervielle": SupervielleScraper()
        }

    def run_sync_single(self, banco_key: str, progress_callback: Optional[Callable[[str, str], None]] = None) -> SyncLog:
        """Ejecuta el scraping para un único banco y guarda solo los supermercados de Córdoba."""
        scraper = self.scrapers.get(banco_key)
        if not scraper:
            err = f"Scraper no encontrado para el banco '{banco_key}'"
            return self.db.record_sync_error(banco_key, err)

        if progress_callback:
            progress_callback(banco_key, "Consultando...")

        try:
            logger.info(f"--- Sincronizando promociones de Córdoba para {banco_key} ---")
            promos = scraper.scrape()

            # Filtrado exclusivo para la Ciudad de Córdoba
            promos_cordoba = []
            for p in promos:
                if scraper.es_supermercado_cordoba(p.supermercado, p.condiciones):
                    promos_cordoba.append(p)
                else:
                    logger.debug(f"Descartado por no operar en Ciudad de Córdoba: {p.supermercado}")

            if progress_callback:
                progress_callback(banco_key, f"Procesando {len(promos_cordoba)} promociones de Córdoba...")

            sync_log = self.db.save_sync_results(scraper.banco, promos_cordoba)

            if progress_callback:
                progress_callback(banco_key, f"Actualizado ({len(promos_cordoba)} vigentes en Córdoba)")

            return sync_log

        except Exception as e:
            err_msg = f"Fallo al conectar o extraer datos: {str(e)}"
            logger.exception(f"Error durante el scraping de {banco_key}: {e}")
            if progress_callback:
                progress_callback(banco_key, f"Error: {str(e)[:40]}")
            return self.db.record_sync_error(scraper.banco, err_msg)

    def run_sync_all(self, progress_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, SyncLog]:
        """Ejecuta el scraping de todos los bancos."""
        results = {}
        for banco_key in self.scrapers.keys():
            results[banco_key] = self.run_sync_single(banco_key, progress_callback)
        return results

import threading
import time
from typing import Optional, Callable
from config import DEFAULT_UPDATE_INTERVAL_HOURS, logger
from scrapers.manager import ScraperManager

class BackgroundUpdateService:
    def __init__(self, scraper_manager: ScraperManager, interval_hours: float = DEFAULT_UPDATE_INTERVAL_HOURS):
        self.scraper_manager = scraper_manager
        self.interval_seconds = interval_hours * 3600
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_updating = False
        self._lock = threading.Lock()
        self.on_sync_finished: Optional[Callable[[], None]] = None
        self.on_sync_progress: Optional[Callable[[str, str], None]] = None

    def start(self, run_initial_if_empty: bool = True):
        """Inicia el servicio de sincronización automática en segundo plano."""
        if self._thread and self._thread.is_alive():
            logger.warning("El servicio de actualización ya está en ejecución.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="BackgroundSyncWorker", daemon=True)
        self._thread.start()
        logger.info(f"Servicio de actualización en segundo plano iniciado (intervalo: {self.interval_seconds / 3600} horas).")

    def stop(self):
        """Detiene el servicio en segundo plano limpiamente."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("Servicio de actualización en segundo plano detenido.")

    def trigger_manual_update(self, callback_on_finish: Optional[Callable[[], None]] = None):
        """Ejecuta una actualización inmediata en un hilo separado para no bloquear la interfaz gráfica."""
        with self._lock:
            if self._is_updating:
                logger.info("Ya hay una sincronización en curso. Se omite solicitud duplicada.")
                return False
            self._is_updating = True

        def _worker():
            try:
                logger.info("Iniciando actualización manual...")
                self.scraper_manager.run_sync_all(progress_callback=self._notify_progress)
                if self.on_sync_finished:
                    self.on_sync_finished()
                if callback_on_finish:
                    callback_on_finish()
            finally:
                with self._lock:
                    self._is_updating = False

        t = threading.Thread(target=_worker, name="ManualSyncWorker", daemon=True)
        t.start()
        return True

    def is_updating(self) -> bool:
        return self._is_updating

    def _notify_progress(self, banco: str, mensaje: str):
        if self.on_sync_progress:
            try:
                self.on_sync_progress(banco, mensaje)
            except Exception as e:
                logger.debug(f"Error al notificar progreso a la UI: {e}")

    def _run_loop(self):
        """Ciclo continuo que espera el intervalo establecido o señal de parada."""
        while not self._stop_event.is_set():
            # Dormir en lapsos pequeños de 1 segundo para responder de inmediato si se cierra la app
            elapsed = 0
            while elapsed < self.interval_seconds and not self._stop_event.is_set():
                time.sleep(1)
                elapsed += 1

            if self._stop_event.is_set():
                break

            # Ejecutar ciclo periódico de actualización
            with self._lock:
                if self._is_updating:
                    continue
                self._is_updating = True

            try:
                logger.info("Iniciando ciclo periódico de actualización (cada 6 horas)...")
                self.scraper_manager.run_sync_all(progress_callback=self._notify_progress)
                if self.on_sync_finished:
                    self.on_sync_finished()
            except Exception as e:
                logger.exception(f"Error en ciclo periódico de actualización: {e}")
            finally:
                with self._lock:
                    self._is_updating = False

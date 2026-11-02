import sys
import os
import argparse
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import logger
from database import DatabaseManager
from scrapers.manager import ScraperManager
from scheduler import BackgroundUpdateService

def run_gui():
    print("\n" + "=" * 65)
    print("  INICIANDO APLICACIÓN DE ESCRITORIO (CIUDAD DE CÓRDOBA)")
    print("  La ventana visual se abrirá en tu pantalla.")
    print("=" * 65 + "\n")

    from ui.app import MainApplication
    db = DatabaseManager()
    scraper_mgr = ScraperManager(db)
    scheduler = BackgroundUpdateService(scraper_mgr)

    app = MainApplication(db=db, scheduler=scheduler)
    app.mainloop()

def run_web():
    from web_app import app
    from config import WEB_HOST, WEB_PORT
    host = os.environ.get("HOST", WEB_HOST)
    port = int(os.environ.get("PORT", WEB_PORT))

    print("\n" + "=" * 65)
    print(f"  🌐 SERVIDOR WEB INICIADO EN {host}:{port}")
    print(f"  Accede en tu navegador: http://localhost:{port} o desde la red.")
    print("  (Cerrar la pestaña web NO cierra el servidor).")
    print("  Para detener el servidor, presiona Ctrl + C en esta terminal.")
    print("=" * 65 + "\n")

    app.run(host=host, port=port, debug=False)

def run_sync_cli():
    print("=====================================================")
    print("  SINCRONIZACIÓN EXCLUSIVA PARA CIUDAD DE CÓRDOBA")
    print("=====================================================")
    db = DatabaseManager()
    mgr = ScraperManager(db)

    def print_progress(banco, msg):
        print(f"[{banco}] {msg}")

    results = mgr.run_sync_all(progress_callback=print_progress)

    print("\n--- RESUMEN DE SINCRONIZACIÓN (CÓRDOBA) ---")
    for banco, log in results.items():
        print(f"Banco: {banco}")
        print(f"  Estado: {log.estado}")
        print(f"  Promociones en Córdoba: {log.promociones_encontradas}")
        print(f"  Nuevas: {log.promociones_nuevas} | Actualizadas: {log.promociones_actualizadas} | Vencidas: {log.promociones_vencidas}")
        print("-" * 40)

def run_list_cli(banco_filter=None):
    db = DatabaseManager()
    promos = db.get_active_promotions(banco=banco_filter)
    print(f"\nTotal de promociones vigentes en Ciudad de Córdoba: {len(promos)}")
    for p in promos:
        print(f"[{p.banco}] {p.supermercado} -> {p.descuento} | Días: {p.dias} | Tope: {p.tope_reintegro} | Pago: {p.medio_pago}")
        print(f"    Enlace: {p.enlace_original}")
        print("-" * 70)

def main():
    parser = argparse.ArgumentParser(description="Promociones de Supermercados en Ciudad de Córdoba")
    parser.add_argument("--sync", action="store_true", help="Ejecutar sincronización completa por consola")
    parser.add_argument("--list", action="store_true", help="Listar promociones vigentes por consola")
    parser.add_argument("--banco", type=str, help="Filtrar por banco")
    parser.add_argument("--web", action="store_true", help="Abrir en el navegador web local (http://127.0.0.1:5000)")

    args = parser.parse_args()

    if args.sync:
        run_sync_cli()
    elif args.list:
        run_list_cli(args.banco)
    elif args.web:
        run_web()
    else:
        run_gui()

if __name__ == "__main__":
    main()

import os
import sys
import logging
from pathlib import Path

# Directorios base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Base de datos SQLite
DATABASE_PATH = str(DATA_DIR / "promociones_bancarias.db")

# Intervalo de actualización automática por defecto (en horas)
DEFAULT_UPDATE_INTERVAL_HOURS = 6

# URLs oficiales requeridas
URLS = {
    "SANTANDER": "https://www.santander.com.ar/",
    "HIPOTECARIO": "https://www.hipotecario.com.ar/",
    "SUPERVIELLE": "https://www.supervielle.com.ar/",
}

# Configuración del servidor Web
WEB_HOST = os.environ.get("HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("PORT", 5000))

# Configuración de Logging
LOG_FILE = DATA_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PromosBancarias")

# Cadenas de supermercados con presencia física o entrega verificada en la CIUDAD DE CÓRDOBA
CORDOBA_SUPERMARKETS = [
    "disco",
    "vea",
    "jumbo",
    "changomas",
    "chango más",
    "hiperchangomas",
    "almacor",
    "supermercados de córdoba",
    "supermercados de cordoba",
    "makro",
    "diarco",
    "pedidosya market",
    "pedidos ya market",
    "cordiez",
    "mariano max",
    "buenos días",
    "buenos dias",
    "carrefour"
]

# Supermercados que NO tienen presencia en la Ciudad de Córdoba (para descarte estricto)
EXCLUDED_FROM_CORDOBA = [
    "coto",
    "la anónima",
    "la anonima",
    "la gallega",
    "cooperativa obrera",
    "alvear",
    "josimar",
    "aiello",
    "atomo",
    "átomo",
    "oscar david",
    "mayorista sogo",
    "supermercado europa",
    "jujuy",
    "mendoza",
    "santa fe",
    "rosario"
]

# Rubros generales descartados
EXCLUDED_KEYWORDS = [
    "restaurante", "combustible", "ypf", "shell", "axion", "indumentaria",
    "electrodomestico", "electrodoméstico", "entretenimiento", "turismo",
    "hotel", "vuelo", "pasajes", "teatro", "cine", "farmacia", "perfumeria"
]

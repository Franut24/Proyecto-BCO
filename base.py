import re
from abc import ABC, abstractmethod
from typing import List, Optional
from bs4 import BeautifulSoup
from models import Promocion
from config import CORDOBA_SUPERMARKETS, EXCLUDED_FROM_CORDOBA, EXCLUDED_KEYWORDS, logger

class BaseScraper(ABC):
    def __init__(self, banco: str):
        self.banco = banco

    @abstractmethod
    def scrape(self) -> List[Promocion]:
        """Realiza la extracción de promociones para el banco correspondiente."""
        pass

    def es_supermercado_cordoba(self, nombre: str, condiciones: str = "") -> bool:
        """
        Verifica estrictamente que la promoción corresponda a un supermercado
        con presencia real en la Ciudad de Córdoba, Argentina.
        """
        texto_analizar = f"{nombre} {condiciones}".lower()

        # 1. Descartar si pertenece a una cadena que NO está en Ciudad de Córdoba
        for excl in EXCLUDED_FROM_CORDOBA:
            if re.search(r'\b' + re.escape(excl) + r'\b', texto_analizar):
                return False

        # 2. Descartar rubros que no sean supermercados (combustible, restaurantes, etc.)
        for excl in EXCLUDED_KEYWORDS:
            if re.search(r'\b' + re.escape(excl) + r'\b', texto_analizar):
                return False

        # 3. Comprobar presencia explícita en Córdoba
        for sm in CORDOBA_SUPERMARKETS:
            if re.search(r'\b' + re.escape(sm) + r'\b', nombre.lower()):
                return True

        return False

    def limpiar_texto(self, texto: Optional[str]) -> str:
        """Elimina etiquetas HTML y espacios en blanco redundantes."""
        if not texto:
            return "No especificado"
        if "<" in texto and ">" in texto:
            texto = BeautifulSoup(texto, "html.parser").get_text()
        limpio = re.sub(r'\s+', ' ', texto).strip()
        return limpio if limpio else "No especificado"

    def normalizar_dias(self, dias: List[str] | str) -> str:
        """Normaliza una lista de días a un formato legible y ordenado."""
        if isinstance(dias, str):
            if not dias or dias.strip().lower() in ["", "no especificado", "none", "null"]:
                return "No especificado"
            return dias.strip().capitalize()

        if not dias:
            return "No especificado"

        dias_orden = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"]
        dias_limpios = [d.strip().lower() for d in dias if d and d.strip()]

        if len(dias_limpios) >= 7 or "todos los dias" in " ".join(dias_limpios) or "todos los días" in " ".join(dias_limpios):
            return "Todos los días"

        def orden_key(d):
            for i, o in enumerate(dias_orden):
                if o in d:
                    return i
            return 99

        dias_limpios.sort(key=orden_key)
        return ", ".join([d.capitalize() for d in dias_limpios])

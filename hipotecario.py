import re
from typing import List
import requests
from bs4 import BeautifulSoup
from models import Promocion
from config import logger
from .base import BaseScraper

class HipotecarioScraper(BaseScraper):
    def __init__(self):
        super().__init__("Banco Hipotecario")
        self.base_url = "https://www.hipotecario.com.ar"
        self.beneficios_url = "https://www.hipotecario.com.ar/beneficios/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8"
        }

    def scrape(self) -> List[Promocion]:
        promociones: List[Promocion] = []
        try:
            logger.info(f"Consultando beneficios Banco Hipotecario: {self.beneficios_url}")
            r = requests.get(self.beneficios_url, headers=self.headers, timeout=15)
            if r.status_code != 200:
                logger.warning(f"Error HTTP {r.status_code} al consultar Hipotecario")
                return promociones

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.find_all("a", href=lambda h: h and "/alianzas-bh/" in h)
            logger.info(f"Hipotecario: {len(cards)} tarjetas de alianzas encontradas.")

            seen_urls = set()

            for card in cards:
                href = card.get("href")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                card_text = " ".join(card.stripped_strings)

                # Verificar si pertenece a supermercados
                es_super = (
                    "supermercado" in card_text.lower() or
                    any(s in card_text.lower() for s in ["changomas", "jumbo", "disco", "vea", "la anonima", "la anónima", "cooperativa obrera", "coto"])
                )

                # Descartar si pertenece explícitamente a rubros no supermercado (combustible, veterinaria, farmacia, etc.)
                if any(x in card_text.lower() for x in ["combustible", "veterinaria", "farmacia", "librera", "librería", "hogar", "corralon"]):
                    if not any(s in card_text.lower() for s in ["changomas", "jumbo", "disco", "vea", "coto", "la anonima"]):
                        continue

                if not es_super:
                    continue

                full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                try:
                    promos_card = self._parse_alliance_detail(full_url, card_text)
                    promociones.extend(promos_card)
                except Exception as e:
                    logger.debug(f"Error parseando alianza Hipotecario {full_url}: {e}")

        except Exception as e:
            logger.error(f"Error general en HipotecarioScraper: {e}")
            raise e

        return promociones

    def _parse_alliance_detail(self, url: str, card_summary: str) -> List[Promocion]:
        r = requests.get(url, headers=self.headers, timeout=12)
        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        # 1. Título y Descuento
        h3 = soup.find("h3")
        titulo_alianza = self.limpiar_texto(h3.get_text() if h3 else "")

        # Descuento
        m_desc = re.search(r'(\d+%\s*(?:OFF|de ahorro|descuento)?)', card_summary + " " + titulo_alianza, re.IGNORECASE)
        descuento = m_desc.group(1).upper() if m_desc else "25% OFF"

        # 2. Párrafo de legales
        legales_text = ""
        for p in soup.find_all("p"):
            txt = p.get_text().strip()
            if "PUBLICIDAD" in txt or "PROMOCI" in txt:
                legales_text = txt
                break

        # 3. Identificar supermercados a los que aplica
        supermercados = []
        lower_context = (titulo_alianza + " " + legales_text + " " + card_summary).lower()

        if "jumbo" in lower_context or "disco" in lower_context or "vea" in lower_context:
            if "jumbo" in lower_context: supermercados.append("Jumbo")
            if "disco" in lower_context: supermercados.append("Disco")
            if "vea" in lower_context: supermercados.append("Vea")
        elif "changomas" in lower_context or "chango más" in lower_context or "hiperchangomas" in lower_context:
            supermercados.append("ChangoMás")
        elif "la anonima" in lower_context or "la anónima" in lower_context:
            supermercados.append("La Anónima")
        elif "cooperativa obrera" in lower_context:
            supermercados.append("Cooperativa Obrera")
        elif "coto" in lower_context:
            supermercados.append("Coto")
        else:
            # Fallback al título limpio de la alianza
            clean_name = re.sub(r'(con modo|sin contacto|\d+%?\s*off)', '', titulo_alianza, flags=re.IGNORECASE).strip()
            supermercados.append(clean_name if clean_name else "Supermercado")

        # 4. Días de la semana
        dias_detectados = []
        dias_nombres = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"]
        for dia in dias_nombres:
            if re.search(r'\b(los\s+)?' + dia + r'\b', legales_text.lower()):
                dias_detectados.append(dia.capitalize())

        dias_str = self.normalizar_dias(dias_detectados) if dias_detectados else "Martes"

        # 5. Tope de reintegro
        tope_str = "No especificado"
        if "sin tope" in legales_text.lower():
            tope_str = "Sin tope de reintegro"
        else:
            m_topes = re.findall(r'(\$[\d\.\,]+(?:\s*mensual|\s*por mes)?)', legales_text, re.IGNORECASE)
            if m_topes:
                # Tomar los topes mencionados
                if len(m_topes) >= 2:
                    tope_str = f"General: {m_topes[0]} | Segmentos Búho: {m_topes[1]}"
                else:
                    tope_str = m_topes[0]
            elif "tope" in legales_text.lower():
                m_tope_gen = re.search(r'tope[^\.\;]{1,60}', legales_text, re.IGNORECASE)
                tope_str = self.limpiar_texto(m_tope_gen.group(0)) if m_tope_gen else "Ver condiciones"

        # 6. Medio de pago
        if "nfc" in legales_text.lower() or "sin contacto" in lower_context:
            medio_pago = "Tarjeta de Débito Visa Sin Contacto (NFC / Apple Pay / Google Pay / MODO)"
        elif "modo" in lower_context or "qr" in legales_text.lower():
            medio_pago = "Tarjeta de Débito Visa mediante QR MODO (App BH o App MODO)"
        elif "crédito" in legales_text.lower():
            medio_pago = "Tarjetas de Crédito y Débito Banco Hipotecario"
        else:
            medio_pago = "Tarjeta de Débito Visa Banco Hipotecario"

        # 7. Fechas de vigencia
        m_fechas = re.search(r'desde el\s+(\d{1,2}/\d{1,2}/\d{4})\s+hasta el\s+(\d{1,2}/\d{1,2}/\d{4})', legales_text, re.IGNORECASE)
        if m_fechas:
            fecha_inicio = m_fechas.group(1)
            fecha_fin = m_fechas.group(2)
        else:
            fecha_inicio = "No especificado"
            fecha_fin = "No especificado"

        condiciones = self.limpiar_texto(legales_text) if legales_text else f"Promoción oficial Banco Hipotecario en {titulo_alianza}."

        # Generar una entrada por cada supermercado si la alianza agrupa varios (ej. Jumbo, Disco, Vea)
        res = []
        for sm in supermercados:
            res.append(Promocion(
                banco="Banco Hipotecario",
                supermercado=sm,
                descuento=descuento,
                dias=dias_str,
                tope_reintegro=tope_str,
                medio_pago=medio_pago,
                condiciones=condiciones,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                enlace_original=url
            ))

        return res

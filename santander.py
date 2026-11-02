import re
from datetime import datetime
from urllib.parse import quote_plus
from typing import List
from models import Promocion
from config import logger
from .base import BaseScraper

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import requests as cffi_requests

class SantanderScraper(BaseScraper):
    def __init__(self):
        super().__init__("Santander")
        self.base_url = "https://www.santander.com.ar"
        self.api_url = "https://www.santander.com.ar/bff-benefits"

    def _get_session(self):
        if HAS_CURL_CFFI:
            return cffi_requests.Session(impersonate="chrome120")
        session = cffi_requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-AR,es;q=0.9",
        })
        return session

    def scrape(self) -> List[Promocion]:
        promociones: List[Promocion] = []
        session = self._get_session()

        try:
            url_brands = f"{self.api_url}/brands?categories=SUP&limit=100"
            logger.info(f"Consultando marcas de supermercados Santander: {url_brands}")
            resp = session.get(url_brands, timeout=15)

            if resp.status_code != 200:
                logger.warning(f"Respuesta no exitosa de Santander brands API: {resp.status_code}")
                return promociones

            data = resp.json()
            brands = data.get("items", [])
            logger.info(f"Santander: {len(brands)} marcas de supermercados obtenidas.")

            for brand in brands:
                brand_id = brand.get("id")
                brand_name = self.limpiar_texto(brand.get("name", ""))

                if not brand_name or brand_name == "No especificado":
                    continue

                # Consultar publicaciones detalladas para esta marca
                try:
                    brand_detail_url = f"{self.api_url}/brands/{brand_id}"
                    r_detail = session.get(brand_detail_url, timeout=10)
                    if r_detail.status_code == 200:
                        detail_data = r_detail.json()
                        pub_items = detail_data.get("items", [])

                        for pub in pub_items:
                            promo = self._parse_publication(brand_id, brand_name, brand, pub)
                            if promo:
                                promociones.append(promo)

                    # Si no tiene publicaciones detalladas, crear una a partir del resumen de la marca
                    if not pub_items and brand.get("benefitDescription"):
                        promo_summary = self._create_summary_promo(brand_id, brand_name, brand)
                        if promo_summary:
                            promociones.append(promo_summary)

                except Exception as e:
                    logger.debug(f"Error procesando detalle de marca Santander {brand_name} (ID: {brand_id}): {e}")
                    # En caso de error en detalle, usar resumen de marca
                    if brand.get("benefitDescription"):
                        promo_summary = self._create_summary_promo(brand_id, brand_name, brand)
                        if promo_summary:
                            promociones.append(promo_summary)

        except Exception as e:
            logger.error(f"Error general en SantanderScraper: {e}")
            raise e

        return promociones

    def _parse_publication(self, brand_id: int, brand_name: str, brand: dict, pub: dict) -> Promocion:
        # 1. Descuento
        discount_val = pub.get("customerDiscount")
        if discount_val:
            descuento = f"{discount_val}%"
        elif pub.get("texts", {}).get("discount"):
            descuento = f"{pub['texts']['discount']}%"
        elif pub.get("texts", {}).get("title"):
            descuento = pub["texts"]["title"]
        elif brand.get("benefitDescription"):
            descuento = brand["benefitDescription"]
        else:
            descuento = "No especificado"

        # 2. Días de la semana
        dias_list = []
        dias_keys = [
            ("monday", "Lunes"),
            ("tuesday", "Martes"),
            ("wednesday", "Miércoles"),
            ("thursday", "Jueves"),
            ("friday", "Viernes"),
            ("saturday", "Sábado"),
            ("sunday", "Domingo")
        ]
        if pub.get("fullWeek"):
            dias_str = "Todos los días"
        else:
            for k, nombre_dia in dias_keys:
                if pub.get(k):
                    dias_list.append(nombre_dia)
            dias_str = ", ".join(dias_list) if dias_list else "No especificado"

        # 3. Tope de reintegro
        top_amount = pub.get("topAmount")
        texts_desc = pub.get("texts", {}).get("description", "")
        if top_amount is not None:
            tope = f"${top_amount:,.0f}".replace(",", ".")
        elif texts_desc and "tope" in texts_desc.lower():
            tope = self.limpiar_texto(texts_desc)
        elif pub.get("legal") and "tope" in pub.get("legal", "").lower():
            m_tope = re.search(r'tope\s*(?:mensual|diario|de reintegro)?\s*(?:de)?\s*(\$[\s\d\.\,]+)', pub["legal"], re.IGNORECASE)
            tope = m_tope.group(1).strip() if m_tope else "Ver condiciones"
        else:
            tope = "No especificado"

        # 4. Medio de pago
        payment_type = pub.get("paymentType", {}).get("description") if isinstance(pub.get("paymentType"), dict) else None
        payment_method = pub.get("paymentMethod", {}).get("description") if isinstance(pub.get("paymentMethod"), dict) else None
        medio_partes = []
        if payment_type:
            medio_partes.append(payment_type)
        if payment_method:
            medio_partes.append(payment_method)

        add_text = self.limpiar_texto(pub.get("additionalText", ""))
        if "nfc" in add_text.lower() or "apple pay" in add_text.lower() or "google pay" in add_text.lower():
            medio_partes.append("NFC (Apple Pay / Google Pay / MODO)")

        medio_pago = " - ".join(medio_partes) if medio_partes else "Tarjetas Santander"

        # 5. Condiciones particulares
        condiciones_raw = f"{add_text}\n\n{self.limpiar_texto(pub.get('legal', ''))}".strip()
        condiciones = self.limpiar_texto(condiciones_raw) if condiciones_raw else "No especificado"

        # 6. Fechas de vigencia
        fecha_inicio = self._format_date(pub.get("startDatePublication"))
        fecha_fin = self._format_date(pub.get("endDatePublication"))

        # 7. Enlace directo oficial
        slug = quote_plus(brand_name.lower())
        enlace = f"https://www.santander.com.ar/personas/beneficios#/results?keyWord={slug}&brandId={brand_id}"

        return Promocion(
            banco="Santander",
            supermercado=brand_name,
            descuento=descuento,
            dias=dias_str,
            tope_reintegro=tope,
            medio_pago=medio_pago,
            condiciones=condiciones,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            enlace_original=enlace
        )

    def _create_summary_promo(self, brand_id: int, brand_name: str, brand: dict) -> Promocion:
        descuento = brand.get("benefitDescription", "No especificado")
        slug = quote_plus(brand_name.lower())
        enlace = f"https://www.santander.com.ar/personas/beneficios#/results?keyWord={slug}&brandId={brand_id}"

        return Promocion(
            banco="Santander",
            supermercado=brand_name,
            descuento=descuento,
            dias="No especificado",
            tope_reintegro="No especificado",
            medio_pago="Tarjetas Santander",
            condiciones=f"Beneficio oficial vigente para {brand_name} en Banco Santander.",
            fecha_inicio="No especificado",
            fecha_fin="No especificado",
            enlace_original=enlace
        )

    def _format_date(self, date_str: str) -> str:
        if not date_str:
            return "No especificado"
        try:
            # Parse ISO e.g. 2026-10-22T00:00:00
            clean = date_str.split("T")[0]
            dt = datetime.strptime(clean, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return date_str

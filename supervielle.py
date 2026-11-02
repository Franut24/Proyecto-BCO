import json
import re
from datetime import datetime
from typing import List
import requests
from models import Promocion
from config import logger
from .base import BaseScraper

class SupervielleScraper(BaseScraper):
    def __init__(self):
        super().__init__("Banco Supervielle")
        self.url = "https://www.supervielle.com.ar/personas/beneficios/descuentos/supermercados"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8"
        }

    def scrape(self) -> List[Promocion]:
        promociones: List[Promocion] = []
        try:
            logger.info(f"Consultando promociones de supermercados en Supervielle: {self.url}")
            r = requests.get(self.url, headers=self.headers, timeout=15)
            if r.status_code != 200:
                logger.warning(f"Error HTTP {r.status_code} al consultar Supervielle")
                return promociones

            # Extraer __NEXT_DATA__
            idx = r.text.find("__NEXT_DATA__")
            if idx == -1:
                logger.warning("No se encontró __NEXT_DATA__ en la página de Supervielle")
                return promociones

            sub = r.text[idx:]
            brace_idx = sub.find("{")
            if brace_idx == -1:
                return promociones

            decoder = json.JSONDecoder()
            data, _ = decoder.raw_decode(sub[brace_idx:])
            beneficios = data.get("props", {}).get("pageProps", {}).get("beneficios", [])

            logger.info(f"Supervielle: {len(beneficios)} promociones obtenidas del buscador oficial.")

            for item in beneficios:
                # Verificar rubro
                rubro = item.get("rubro", "")
                if rubro and rubro.lower() != "supermercados":
                    continue

                promo = self._parse_benefit(item)
                if promo:
                    promociones.append(promo)

        except Exception as e:
            logger.error(f"Error general en SupervielleScraper: {e}")
            raise e

        return promociones

    def _parse_benefit(self, item: dict) -> Promocion:
        raw_marca = item.get("marca", "").strip()

        # Determinar medio de pago y variantes de cliente
        medio_partes = []
        is_modo = "modo" in raw_marca.lower()
        is_sueldo = "sueldo" in raw_marca.lower()
        is_identite = item.get("esIdentite", False) or "identite" in raw_marca.lower()

        if item.get("esTarjetaDebito") and item.get("esTarjetaCredito"):
            medio_partes.append("Tarjetas de Débito y Crédito Supervielle")
        elif item.get("esTarjetaDebito"):
            medio_partes.append("Tarjeta de Débito Supervielle")
        elif item.get("esTarjetaCredito"):
            medio_partes.append("Tarjeta de Crédito Supervielle")
        else:
            medio_partes.append("Tarjetas Supervielle")

        if is_modo:
            medio_partes.append("vía QR MODO (App Supervielle o App MODO)")

        if is_sueldo:
            medio_partes.append("Exclusivo Plan Sueldo")

        if is_identite:
            medio_partes.append("Segmento Identité")

        medio_pago = " - ".join(medio_partes)

        # Limpiar nombre del supermercado
        sm_name = raw_marca
        for remove_word in ["con MODO Plan Sueldo", "con MODO", "Plan Sueldo", "Identité", "Identite"]:
            sm_name = re.sub(re.escape(remove_word), "", sm_name, flags=re.IGNORECASE).strip()

        if not sm_name:
            sm_name = raw_marca

        # Descuento
        descuento_val = item.get("descuento")
        cuotas_val = item.get("cuotas")
        if descuento_val:
            descuento = descuento_val.strip()
        elif cuotas_val:
            descuento = f"Hasta {cuotas_val[0]} cuotas sin interés"
        else:
            descuento = "Beneficio especial"

        # Días
        dias_raw = item.get("dias", [])
        dias = self.normalizar_dias(dias_raw)

        # Tope de reintegro
        tope_raw = item.get("tope")
        if tope_raw is not None and tope_raw != "":
            try:
                tope_num = float(tope_raw)
                tope_str = f"${tope_num:,.0f}".replace(",", ".")
            except ValueError:
                tope_str = str(tope_raw)
        else:
            tope_str = "No especificado"

        # Fechas
        fecha_inicio = self._format_date(item.get("fechaVigenciaDesde"))
        fecha_fin = self._format_date(item.get("fechaVigenciaHasta"))

        # Condiciones particulares
        desc_tarjetas = self.limpiar_texto(item.get("descripcionTarjetas", ""))
        zonas = item.get("zonas", "")
        condiciones_partes = []
        if is_sueldo:
            condiciones_partes.append("Beneficio diferencial exclusivo para clientes que cobran sus haberes en Banco Supervielle.")
        if is_identite:
            condiciones_partes.append("Promoción exclusiva para clientes pertenecientes al segmento Supervielle Identité.")
        if is_modo:
            condiciones_partes.append("Aplica pagando a través de la billetera virtual MODO con QR desde App Supervielle.")
        if desc_tarjetas and desc_tarjetas != "No especificado":
            condiciones_partes.append(desc_tarjetas)
        if zonas:
            condiciones_partes.append(f"Zonas aplicables: {zonas}")

        condiciones = " ".join(condiciones_partes) if condiciones_partes else f"Promoción oficial vigente en {sm_name} para clientes Banco Supervielle."

        return Promocion(
            banco="Supervielle",
            supermercado=sm_name,
            descuento=descuento,
            dias=dias,
            tope_reintegro=tope_str,
            medio_pago=medio_pago,
            condiciones=condiciones,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            enlace_original=self.url
        )

    def _format_date(self, date_str: str) -> str:
        if not date_str:
            return "No especificado"
        try:
            clean = date_str.split("T")[0]
            dt = datetime.strptime(clean, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return date_str

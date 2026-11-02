import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Promocion:
    banco: str
    supermercado: str
    descuento: str
    dias: str
    tope_reintegro: str = "No especificado"
    medio_pago: str = "No especificado"
    condiciones: str = "No especificado"
    fecha_inicio: str = "No especificado"
    fecha_fin: str = "No especificado"
    enlace_original: str = "No especificado"
    ultima_consulta: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    activa: int = 1
    id: Optional[int] = None
    hash_promocion: str = ""
    creada_el: Optional[str] = None
    actualizada_el: Optional[str] = None

    def __post_init__(self):
        if not self.hash_promocion:
            self.hash_promocion = self.generar_hash()

    def generar_hash(self) -> str:
        """Genera un hash único basado en los datos clave de la promoción para comparar cambios."""
        raw = f"{self.banco}|{self.supermercado}|{self.descuento}|{self.dias}|{self.tope_reintegro}|{self.medio_pago}|{self.fecha_fin}".lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "banco": self.banco,
            "supermercado": self.supermercado,
            "descuento": self.descuento,
            "dias": self.dias,
            "tope_reintegro": self.tope_reintegro,
            "medio_pago": self.medio_pago,
            "condiciones": self.condiciones,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "enlace_original": self.enlace_original,
            "ultima_consulta": self.ultima_consulta,
            "activa": self.activa,
            "hash_promocion": self.hash_promocion,
            "creada_el": self.creada_el,
            "actualizada_el": self.actualizada_el
        }

@dataclass
class SyncLog:
    banco: str
    fecha_sincronizacion: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    estado: str = "EXITOSO"  # EXITOSO o ERROR
    promociones_encontradas: int = 0
    promociones_nuevas: int = 0
    promociones_actualizadas: int = 0
    promociones_vencidas: int = 0
    mensaje_error: str = ""
    id: Optional[int] = None

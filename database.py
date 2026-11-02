import sqlite3
import threading
from datetime import datetime
from typing import List, Optional, Dict
from config import DATABASE_PATH, logger
from models import Promocion, SyncLog

class DatabaseManager:
    _lock = threading.Lock()

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Crea las tablas de promociones y registro de sincronización si no existen."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS promociones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        banco TEXT NOT NULL,
                        supermercado TEXT NOT NULL,
                        descuento TEXT NOT NULL,
                        dias TEXT NOT NULL,
                        tope_reintegro TEXT NOT NULL,
                        medio_pago TEXT NOT NULL,
                        condiciones TEXT NOT NULL,
                        fecha_inicio TEXT NOT NULL,
                        fecha_fin TEXT NOT NULL,
                        enlace_original TEXT NOT NULL,
                        ultima_consulta TEXT NOT NULL,
                        activa INTEGER NOT NULL DEFAULT 1,
                        hash_promocion TEXT NOT NULL,
                        creada_el TEXT NOT NULL,
                        actualizada_el TEXT NOT NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        banco TEXT NOT NULL,
                        fecha_sincronizacion TEXT NOT NULL,
                        estado TEXT NOT NULL,
                        promociones_encontradas INTEGER NOT NULL,
                        promociones_nuevas INTEGER NOT NULL,
                        promociones_actualizadas INTEGER NOT NULL,
                        promociones_vencidas INTEGER NOT NULL,
                        mensaje_error TEXT
                    )
                """)

                # Índices para mejorar rendimiento de búsquedas y filtros
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_promos_banco_activa ON promociones(banco, activa)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_promos_supermercado ON promociones(supermercado)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_banco ON sync_logs(banco, fecha_sincronizacion)")
                conn.commit()

    def save_sync_results(self, banco: str, promos: List[Promocion]) -> SyncLog:
        """
        Guarda los resultados del scraping:
        - Detecta promociones nuevas.
        - Detecta promociones modificadas.
        - Marca como no vigentes (activa=0) las promociones que ya no están publicadas.
        - Conserva el registro histórico.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevas = 0
        actualizadas = 0
        vencidas = 0

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Obtener promociones actualmente activas del banco
                cursor.execute("SELECT * FROM promociones WHERE banco = ? AND activa = 1", (banco,))
                active_rows = cursor.fetchall()

                # Mapear activas por (supermercado normalizado, dias normalizados)
                active_map = {}
                for row in active_rows:
                    key = (row["supermercado"].strip().lower(), row["dias"].strip().lower(), row["descuento"].strip().lower())
                    active_map[key] = dict(row)

                seen_active_ids = set()

                for p in promos:
                    p.ultima_consulta = now
                    p.hash_promocion = p.generar_hash()
                    key = (p.supermercado.strip().lower(), p.dias.strip().lower(), p.descuento.strip().lower())

                    if key in active_map:
                        existing = active_map[key]
                        seen_active_ids.add(existing["id"])

                        # Verificar si cambiaron detalles
                        if existing["hash_promocion"] != p.hash_promocion:
                            cursor.execute("""
                                UPDATE promociones SET
                                    descuento = ?,
                                    tope_reintegro = ?,
                                    medio_pago = ?,
                                    condiciones = ?,
                                    fecha_inicio = ?,
                                    fecha_fin = ?,
                                    enlace_original = ?,
                                    ultima_consulta = ?,
                                    hash_promocion = ?,
                                    actualizada_el = ?
                                WHERE id = ?
                            """, (
                                p.descuento,
                                p.tope_reintegro,
                                p.medio_pago,
                                p.condiciones,
                                p.fecha_inicio,
                                p.fecha_fin,
                                p.enlace_original,
                                p.ultima_consulta,
                                p.hash_promocion,
                                now,
                                existing["id"]
                            ))
                            actualizadas += 1
                        else:
                            # Sigue igual, solo actualizar timestamp de última consulta
                            cursor.execute("UPDATE promociones SET ultima_consulta = ? WHERE id = ?", (now, existing["id"]))
                    else:
                        # Nueva promoción
                        cursor.execute("""
                            INSERT INTO promociones (
                                banco, supermercado, descuento, dias, tope_reintegro,
                                medio_pago, condiciones, fecha_inicio, fecha_fin,
                                enlace_original, ultima_consulta, activa, hash_promocion,
                                creada_el, actualizada_el
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                        """, (
                            p.banco,
                            p.supermercado,
                            p.descuento,
                            p.dias,
                            p.tope_reintegro,
                            p.medio_pago,
                            p.condiciones,
                            p.fecha_inicio,
                            p.fecha_fin,
                            p.enlace_original,
                            p.ultima_consulta,
                            p.hash_promocion,
                            now,
                            now
                        ))
                        nuevas += 1

                # Las promociones que estaban activas pero ya no aparecen se marcan como no vigentes (activa=0)
                for existing in active_rows:
                    if existing["id"] not in seen_active_ids:
                        cursor.execute("UPDATE promociones SET activa = 0, actualizada_el = ? WHERE id = ?", (now, existing["id"]))
                        vencidas += 1

                # Registrar log de sincronización
                cursor.execute("""
                    INSERT INTO sync_logs (
                        banco, fecha_sincronizacion, estado, promociones_encontradas,
                        promociones_nuevas, promociones_actualizadas, promociones_vencidas, mensaje_error
                    ) VALUES (?, ?, 'EXITOSO', ?, ?, ?, ?, '')
                """, (banco, now, len(promos), nuevas, actualizadas, vencidas))

                conn.commit()

        log = SyncLog(
            banco=banco,
            fecha_sincronizacion=now,
            estado="EXITOSO",
            promociones_encontradas=len(promos),
            promociones_nuevas=nuevas,
            promociones_actualizadas=actualizadas,
            promociones_vencidas=vencidas
        )
        logger.info(f"[{banco}] Sincronización exitosa: {len(promos)} encontradas, {nuevas} nuevas, {actualizadas} actualizadas, {vencidas} vencidas.")
        return log

    def record_sync_error(self, banco: str, error_msg: str) -> SyncLog:
        """Registra un fallo en la sincronización conservando los datos anteriores intactos."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_logs (
                        banco, fecha_sincronizacion, estado, promociones_encontradas,
                        promociones_nuevas, promociones_actualizadas, promociones_vencidas, mensaje_error
                    ) VALUES (?, ?, 'ERROR', 0, 0, 0, 0, ?)
                """, (banco, now, error_msg))
                conn.commit()

        logger.error(f"[{banco}] Error de sincronización: {error_msg}")
        return SyncLog(
            banco=banco,
            fecha_sincronizacion=now,
            estado="ERROR",
            mensaje_error=error_msg
        )

    def get_active_promotions(self, banco: Optional[str] = None, supermarket: Optional[str] = None, day: Optional[str] = None, query: Optional[str] = None) -> List[Promocion]:
        """Obtiene todas las promociones vigentes (activa=1), con filtros opcionales."""
        sql = "SELECT * FROM promociones WHERE activa = 1"
        params = []

        if banco and banco.strip():
            sql += " AND UPPER(banco) = UPPER(?)"
            params.append(banco.strip())

        if supermarket and supermarket.strip():
            sql += " AND LOWER(supermercado) LIKE ?"
            params.append(f"%{supermarket.strip().lower()}%")

        if day and day.strip():
            sql += " AND LOWER(dias) LIKE ?"
            params.append(f"%{day.strip().lower()}%")

        if query and query.strip():
            q = f"%{query.strip().lower()}%"
            sql += " AND (LOWER(supermercado) LIKE ? OR LOWER(condiciones) LIKE ? OR LOWER(medio_pago) LIKE ? OR LOWER(descuento) LIKE ?)"
            params.extend([q, q, q, q])

        sql += " ORDER BY banco ASC, supermercado ASC, descuento DESC"

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()

        promos = []
        for r in rows:
            promos.append(Promocion(
                id=r["id"],
                banco=r["banco"],
                supermercado=r["supermercado"],
                descuento=r["descuento"],
                dias=r["dias"],
                tope_reintegro=r["tope_reintegro"],
                medio_pago=r["medio_pago"],
                condiciones=r["condiciones"],
                fecha_inicio=r["fecha_inicio"],
                fecha_fin=r["fecha_fin"],
                enlace_original=r["enlace_original"],
                ultima_consulta=r["ultima_consulta"],
                activa=r["activa"],
                hash_promocion=r["hash_promocion"],
                creada_el=r["creada_el"],
                actualizada_el=r["actualizada_el"]
            ))
        return promos

    def get_last_successful_sync(self, banco: str) -> Optional[Dict]:
        """Obtiene la fecha y detalles de la última sincronización exitosa de un banco."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sync_logs
                    WHERE banco = ? AND estado = 'EXITOSO'
                    ORDER BY id DESC LIMIT 1
                """, (banco,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
        return None

    def get_last_sync_any(self, banco: str) -> Optional[Dict]:
        """Obtiene el último intento de sincronización (sea exitoso o error)."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sync_logs
                    WHERE banco = ?
                    ORDER BY id DESC LIMIT 1
                """, (banco,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
        return None

    def get_all_supermarkets(self, banco: Optional[str] = None) -> List[str]:
        """Obtiene los nombres únicos de supermercados con promociones vigentes."""
        sql = "SELECT DISTINCT supermercado FROM promociones WHERE activa = 1"
        params = []
        if banco:
            sql += " AND UPPER(banco) = UPPER(?)"
            params.append(banco.strip())
        sql += " ORDER BY supermercado ASC"

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [r["supermercado"] for r in rows]

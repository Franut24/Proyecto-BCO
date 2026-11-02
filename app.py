import threading
import tkinter as tk
from typing import Optional, List
import customtkinter as ctk
from database import DatabaseManager
from scheduler import BackgroundUpdateService
from scrapers.manager import ScraperManager
from ui.components import PromotionCard
from ui.theme import COLORS

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainApplication(ctk.CTk):
    def __init__(self, db: Optional[DatabaseManager] = None, scheduler: Optional[BackgroundUpdateService] = None):
        super().__init__()
        self.db = db or DatabaseManager()
        self.scraper_manager = ScraperManager(self.db)
        self.scheduler = scheduler or BackgroundUpdateService(self.scraper_manager)

        # Configuración de ventana principal
        self.title("Promociones de Supermercados en Ciudad de Córdoba (Santander, Hipotecario, Supervielle)")
        self.geometry("1120x800")
        self.minsize(900, 650)

        # Forzar visualización explícita y traer al frente
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after(300, lambda: self.attributes('-topmost', False))
        self.focus_force()

        # Variables de estado y filtros
        self.search_var = tk.StringVar()
        self.day_filter_var = tk.StringVar(value="Todos")
        self.status_var = tk.StringVar(value="Listo")

        # Conectar callbacks del scheduler
        self.scheduler.on_sync_finished = self._on_sync_finished_threadsafe
        self.scheduler.on_sync_progress = self._on_sync_progress_threadsafe

        # Inicializar vistas
        self._build_header()
        self._build_status_bar()
        self._build_filters()
        self._build_bank_sections()

        # Iniciar servicio en segundo plano
        self.scheduler.start()

        # Cargar datos iniciales
        self.refresh_all_views()

        # Protocolo de cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(16, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        # Título y Subtítulo
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title_inner = ctk.CTkFrame(title_box, fg_color="transparent")
        title_inner.pack(anchor="w")

        title = ctk.CTkLabel(
            title_inner,
            text="🛒 Promociones en Supermercados",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        )
        title.pack(side="left")

        # Badge de ubicación
        loc_badge = ctk.CTkLabel(
            title_inner,
            text=" 📍 Ciudad de Córdoba ",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1d4ed8",
            text_color="#ffffff",
            corner_radius=6
        )
        loc_badge.pack(side="left", padx=(10, 0))

        subtitle = ctk.CTkLabel(
            title_box,
            text="Exclusivo supermercados con presencia en Córdoba Capital (Santander, Hipotecario y Supervielle)",
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8")
        )
        subtitle.pack(anchor="w", pady=(3, 0))

        # Botón de actualización manual
        self.btn_update = ctk.CTkButton(
            header_frame,
            text="🔄 Actualizar Ahora",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=38,
            corner_radius=8,
            command=self._on_manual_update_click
        )
        self.btn_update.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def _build_status_bar(self):
        """Barra informativa del estado de actualización de cada uno de los 3 bancos."""
        self.status_container = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#171922"), corner_radius=10, height=42)
        self.status_container.pack(fill="x", padx=24, pady=(4, 10))

        self.lbl_santander_status = ctk.CTkLabel(
            self.status_container,
            text="🔴 Santander: Verificando...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8"
        )
        self.lbl_santander_status.pack(side="left", padx=14, pady=8)

        self.lbl_hipotecario_status = ctk.CTkLabel(
            self.status_container,
            text="🔵 Hipotecario: Verificando...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8"
        )
        self.lbl_hipotecario_status.pack(side="left", padx=14, pady=8)

        self.lbl_supervielle_status = ctk.CTkLabel(
            self.status_container,
            text="🟣 Supervielle: Verificando...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8"
        )
        self.lbl_supervielle_status.pack(side="left", padx=14, pady=8)

        self.lbl_global_status = ctk.CTkLabel(
            self.status_container,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=11),
            text_color="#38bdf8"
        )
        self.lbl_global_status.pack(side="right", padx=14, pady=8)

    def _build_filters(self):
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=24, pady=(0, 10))
        filter_frame.grid_columnconfigure(0, weight=1)

        # Buscador por supermercado de Córdoba
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="🔍 Buscar en Córdoba (ej: Disco, Jumbo, Vea, Almacor, Makro, Diarco)...",
            textvariable=self.search_var,
            height=36,
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_all_views())

        # Filtro por día de la semana
        days = ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        self.day_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=days,
            variable=self.day_filter_var,
            height=36,
            corner_radius=8,
            command=lambda choice: self.refresh_all_views()
        )
        self.day_menu.grid(row=0, column=1, sticky="e", padx=(0, 8))

        # Botón para limpiar filtros
        btn_clear = ctk.CTkButton(
            filter_frame,
            text="Limpiar",
            width=80,
            height=36,
            fg_color=("#e2e8f0", "#334155"),
            hover_color=("#cbd5e1", "#475569"),
            text_color=("#1e293b", "#f8fafc"),
            corner_radius=8,
            command=self._clear_filters
        )
        btn_clear.grid(row=0, column=2, sticky="e")

    def _build_bank_sections(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Pestañas para cada banco
        self.tab_santander = self.tabview.add("🔴 Santander")
        self.tab_hipotecario = self.tabview.add("🔵 Banco Hipotecario")
        self.tab_supervielle = self.tabview.add("🟣 Supervielle")
        self.tab_todos = self.tabview.add("🌐 Todas las Entidades")

        # Scrollable frames para cada sección
        self.scroll_santander = ctk.CTkScrollableFrame(self.tab_santander, fg_color="transparent")
        self.scroll_santander.pack(fill="both", expand=True, padx=4, pady=4)

        self.scroll_hipotecario = ctk.CTkScrollableFrame(self.tab_hipotecario, fg_color="transparent")
        self.scroll_hipotecario.pack(fill="both", expand=True, padx=4, pady=4)

        self.scroll_supervielle = ctk.CTkScrollableFrame(self.tab_supervielle, fg_color="transparent")
        self.scroll_supervielle.pack(fill="both", expand=True, padx=4, pady=4)

        self.scroll_todos = ctk.CTkScrollableFrame(self.tab_todos, fg_color="transparent")
        self.scroll_todos.pack(fill="both", expand=True, padx=4, pady=4)

    def _clear_filters(self):
        self.search_var.set("")
        self.day_filter_var.set("Todos")
        self.refresh_all_views()

    def _on_manual_update_click(self):
        self.btn_update.configure(state="disabled", text="⏳ Actualizando...")
        self.status_var.set("Sincronizando bancos para Córdoba...")

        success = self.scheduler.trigger_manual_update(
            callback_on_finish=lambda: self.after(0, self._on_manual_update_done)
        )
        if not success:
            self.btn_update.configure(state="normal", text="🔄 Actualizar Ahora")

    def _on_manual_update_done(self):
        self.btn_update.configure(state="normal", text="🔄 Actualizar Ahora")
        self.status_var.set("Sincronización finalizada")
        self.refresh_all_views()

    def _on_sync_finished_threadsafe(self):
        self.after(0, self.refresh_all_views)

    def _on_sync_progress_threadsafe(self, banco: str, mensaje: str):
        self.after(0, lambda: self.status_var.set(f"[{banco}] {mensaje}"))

    def refresh_all_views(self):
        """Recarga todas las secciones con las promociones vigentes de Córdoba."""
        query = self.search_var.get().strip()
        day = self.day_filter_var.get().strip()
        day_param = None if day == "Todos" else day

        # Cargar promociones por sección
        self._populate_section(self.scroll_santander, "Santander", query, day_param)
        self._populate_section(self.scroll_hipotecario, "Banco Hipotecario", query, day_param)
        self._populate_section(self.scroll_supervielle, "Banco Supervielle", query, day_param)
        self._populate_section(self.scroll_todos, None, query, day_param)

        # Actualizar indicadores de sincronización de cada banco
        self._update_bank_sync_indicators()

    def _populate_section(self, parent_frame: ctk.CTkScrollableFrame, banco: Optional[str], query: str, day: Optional[str]):
        for child in parent_frame.winfo_children():
            child.destroy()

        promos = self.db.get_active_promotions(banco=banco, query=query, day=day)

        if not promos:
            empty_box = ctk.CTkFrame(parent_frame, fg_color="transparent")
            empty_box.pack(fill="both", expand=True, pady=40)

            empty_lbl = ctk.CTkLabel(
                empty_box,
                text="No se encontraron promociones vigentes en Córdoba con los filtros seleccionados.",
                font=ctk.CTkFont(size=14),
                text_color="#94a3b8"
            )
            empty_lbl.pack()
            return

        count_lbl = ctk.CTkLabel(
            parent_frame,
            text=f"Mostrando {len(promos)} promoción{'es' if len(promos) != 1 else ''} vigente{'s' if len(promos) != 1 else ''} en Ciudad de Córdoba",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64748b",
            anchor="w"
        )
        count_lbl.pack(fill="x", padx=6, pady=(2, 8))

        for p in promos:
            card = PromotionCard(parent_frame, promo=p)
            card.pack(fill="x", padx=4, pady=6)

    def _update_bank_sync_indicators(self):
        """Muestra el estado de la última sincronización y si se conservan datos anteriores."""
        bancos = [
            ("Santander", self.lbl_santander_status, "🔴 Santander"),
            ("Banco Hipotecario", self.lbl_hipotecario_status, "🔵 Hipotecario"),
            ("Banco Supervielle", self.lbl_supervielle_status, "🟣 Supervielle"),
        ]

        for banco_name, label_widget, prefix in bancos:
            last_succ = self.db.get_last_successful_sync(banco_name)
            last_any = self.db.get_last_sync_any(banco_name)
            count = len(self.db.get_active_promotions(banco=banco_name))

            if last_succ:
                fecha = last_succ["fecha_sincronizacion"]
                if last_any and last_any["estado"] == "ERROR":
                    label_widget.configure(
                        text=f"{prefix}: ⚠️ Datos del {fecha} ({count} en Cba)",
                        text_color="#f59e0b"
                    )
                else:
                    label_widget.configure(
                        text=f"{prefix}: {fecha} ({count} en Córdoba)",
                        text_color="#10b981"
                    )
            else:
                label_widget.configure(
                    text=f"{prefix}: Pendiente de sincronizar",
                    text_color="#94a3b8"
                )

    def _on_closing(self):
        self.scheduler.stop()
        self.destroy()

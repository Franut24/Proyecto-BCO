import webbrowser
import customtkinter as ctk
from models import Promocion
from ui.theme import COLORS

class PromotionCard(ctk.CTkFrame):
    def __init__(self, master, promo: Promocion, **kwargs):
        super().__init__(master, corner_radius=12, fg_color=("#f8f9fa", "#1a1c23"), border_width=1, border_color=("#e2e8f0", "#2d3748"), **kwargs)
        self.promo = promo
        self._build_ui()

    def _get_bank_colors(self):
        banco_norm = self.promo.banco.lower()
        if "santander" in banco_norm:
            return COLORS["santander"]
        elif "hipotecario" in banco_norm:
            return COLORS["hipotecario"]
        elif "supervielle" in banco_norm:
            return COLORS["supervielle"]
        return {"primary": "#4f46e5", "primary_hover": "#4338ca", "badge_bg": "#1e1b4b", "badge_text": "#a5b4fc"}

    def _build_ui(self):
        bank_style = self._get_bank_colors()

        # Configurar grid del frame
        self.grid_columnconfigure(0, weight=1)

        # Fila 1: Cabecera con Supermercado y Descuento
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        header_frame.grid_columnconfigure(0, weight=1)

        # Nombre del Supermercado
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.promo.supermercado,
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Badge de Descuento destacado
        discount_badge = ctk.CTkLabel(
            header_frame,
            text=f"  {self.promo.descuento}  ",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#059669",
            text_color="#ffffff",
            corner_radius=8
        )
        discount_badge.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Fila 2: Chips / Badges de Metadatos (Banco, Día, Tope de reintegro)
        chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        chips_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=4)

        # Chip del Banco
        bank_badge = ctk.CTkLabel(
            chips_frame,
            text=f"🏛️ {self.promo.banco}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=bank_style["badge_bg"],
            text_color=bank_style["badge_text"],
            corner_radius=6,
            padx=8,
            pady=3
        )
        bank_badge.pack(side="left", padx=(0, 6))

        # Chip del Día
        day_badge = ctk.CTkLabel(
            chips_frame,
            text=f"📅 {self.promo.dias}",
            font=ctk.CTkFont(size=12),
            fg_color=("#edf2f7", "#2d3748"),
            text_color=("#2d3748", "#e2e8f0"),
            corner_radius=6,
            padx=8,
            pady=3
        )
        day_badge.pack(side="left", padx=(0, 6))

        # Chip del Tope de Reintegro
        tope_badge = ctk.CTkLabel(
            chips_frame,
            text=f"💰 Tope: {self.promo.tope_reintegro}",
            font=ctk.CTkFont(size=12),
            fg_color=("#edf2f7", "#2d3748"),
            text_color=("#2d3748", "#e2e8f0"),
            corner_radius=6,
            padx=8,
            pady=3
        )
        tope_badge.pack(side="left", padx=(0, 6))

        # Fila 3: Medio de pago requerido
        if self.promo.medio_pago and self.promo.medio_pago != "No especificado":
            payment_frame = ctk.CTkFrame(self, fg_color="transparent")
            payment_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 2))
            payment_label = ctk.CTkLabel(
                payment_frame,
                text=f"💳 Medio de pago: {self.promo.medio_pago}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("#4a5568", "#cbd5e1"),
                anchor="w",
                justify="left"
            )
            payment_label.pack(side="left", fill="x")

        # Fila 4: Vigencia (si está disponible)
        if (self.promo.fecha_inicio != "No especificado" or self.promo.fecha_fin != "No especificado"):
            vigencia_frame = ctk.CTkFrame(self, fg_color="transparent")
            vigencia_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(2, 4))
            vigencia_str = f"⏳ Vigencia: {self.promo.fecha_inicio} al {self.promo.fecha_fin}"
            vigencia_label = ctk.CTkLabel(
                vigencia_frame,
                text=vigencia_str,
                font=ctk.CTkFont(size=11),
                text_color=("#718096", "#a0aec0"),
                anchor="w"
            )
            vigencia_label.pack(side="left")

        # Fila 5: Condiciones particulares (con texto truncado y expandible)
        cond_frame = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#13151b"), corner_radius=8)
        cond_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=6)
        cond_frame.grid_columnconfigure(0, weight=1)

        cond_text = self.promo.condiciones
        short_text = cond_text[:220] + ("..." if len(cond_text) > 220 else "")

        self.cond_label = ctk.CTkLabel(
            cond_frame,
            text=f"Condiciones: {short_text}",
            font=ctk.CTkFont(size=11),
            text_color=("#475569", "#94a3b8"),
            wraplength=760,
            justify="left",
            anchor="w"
        )
        self.cond_label.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        # Fila 6: Botón de acción hacia la fuente oficial y última consulta
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(4, 14))
        footer_frame.grid_columnconfigure(0, weight=1)

        # Label de última consulta
        consulta_label = ctk.CTkLabel(
            footer_frame,
            text=f"Última verificación: {self.promo.ultima_consulta}",
            font=ctk.CTkFont(size=11),
            text_color=("#94a3b8", "#64748b"),
            anchor="w"
        )
        consulta_label.grid(row=0, column=0, sticky="w")

        # Botón para abrir la página oficial
        if self.promo.enlace_original and self.promo.enlace_original.startswith("http"):
            btn_ver = ctk.CTkButton(
                footer_frame,
                text="🔗 Ver en Sitio Oficial",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=bank_style["primary"],
                hover_color=bank_style["primary_hover"],
                height=30,
                width=160,
                corner_radius=8,
                command=self._open_url
            )
            btn_ver.grid(row=0, column=1, sticky="e")

    def _open_url(self):
        if self.promo.enlace_original:
            webbrowser.open_new_tab(self.promo.enlace_original)

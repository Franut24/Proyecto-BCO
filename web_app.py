import os
import sys
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

# Agregar ruta base
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import WEB_HOST, WEB_PORT
from database import DatabaseManager
from scrapers.manager import ScraperManager

app = Flask(__name__)
db = DatabaseManager()
mgr = ScraperManager(db)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Promociones de Supermercados - Ciudad de Córdoba</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --santander: #ec0000;
      --hipotecario: #0284c7;
      --supervielle: #e11d48;
      --accent: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 24px; }
    .container { max-width: 1100px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 16px; }
    .title-box h1 { font-size: 26px; font-weight: 800; display: flex; align-items: center; gap: 10px; }
    .badge-cba { background: #2563eb; color: #fff; font-size: 13px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
    .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
    .btn-sync { background: #2563eb; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    .btn-sync:hover { background: #1d4ed8; }
    .status-bar { display: flex; gap: 12px; background: #172033; padding: 12px 18px; border-radius: 10px; border: 1px solid var(--card-border); margin-bottom: 20px; font-size: 13px; flex-wrap: wrap; }
    .status-bar span { font-weight: 600; }
    .filters { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
    .filters input, .filters select { background: var(--card-bg); border: 1px solid var(--card-border); color: var(--text); padding: 10px 14px; border-radius: 8px; font-size: 14px; outline: none; }
    .filters input { flex: 1; min-width: 250px; }
    .bank-tabs { display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap; }
    .tab-btn { background: #1e293b; color: var(--text-muted); border: 1px solid var(--card-border); padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-block; }
    .tab-btn.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; position: relative; transition: transform 0.15s ease; }
    .card:hover { border-color: #475569; }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .sm-name { font-size: 20px; font-weight: 700; color: #fff; }
    .discount { background: var(--accent); color: #fff; font-size: 15px; font-weight: 800; padding: 6px 12px; border-radius: 8px; }
    .chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .chip { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
    .chip-santander { background: #450a0a; color: #fca5a5; }
    .chip-hipotecario { background: #082f49; color: #7dd3fc; }
    .chip-supervielle { background: #4c0519; color: #fda4af; }
    .chip-meta { background: #334155; color: #e2e8f0; }
    .payment { font-size: 13px; font-weight: 600; color: #cbd5e1; margin-bottom: 8px; }
    .cond { background: #0f172a; padding: 12px; border-radius: 8px; font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-bottom: 14px; }
    .card-footer { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #64748b; flex-wrap: wrap; gap: 10px; }
    .btn-link { background: #3b82f6; color: #fff; padding: 8px 14px; border-radius: 6px; font-weight: 600; text-decoration: none; font-size: 12px; }
    .btn-link:hover { opacity: 0.9; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="title-box">
        <h1>🛒 Promociones en Supermercados <span class="badge-cba">📍 Ciudad de Córdoba</span></h1>
        <div class="subtitle">Descuentos y beneficios vigentes en Disco, Jumbo, Vea, Almacor, Makro, Diarco y PedidosYa</div>
      </div>
      <button class="btn-sync" onclick="location.href='/?refresh=1'">🔄 Actualizar Ahora</button>
    </header>

    <div class="status-bar">
      <div>🔴 Santander: <span>{{ counts['Santander'] }} vigentes</span></div>
      <div>🔵 Hipotecario: <span>{{ counts['Banco Hipotecario'] }} vigentes</span></div>
      <div>🟣 Supervielle: <span>{{ counts['Banco Supervielle'] }} vigentes</span></div>
      <div style="margin-left: auto; color: #38bdf8;">Total en Córdoba: <span>{{ promos|length }} promociones</span></div>
    </div>

    <form class="filters" method="GET" action="/">
      <input type="hidden" name="banco" value="{{ selected_banco }}">
      <input type="text" name="q" value="{{ query }}" placeholder="🔍 Filtrar supermercado (ej: Disco, Jumbo, Vea, Almacor)...">
      <select name="dia" onchange="this.form.submit()">
        <option value="">Todos los días</option>
        {% for d in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'] %}
          <option value="{{ d }}" {% if selected_dia == d %}selected{% endif %}>{{ d }}</option>
        {% endfor %}
      </select>
      <button class="btn-sync" type="submit">Buscar</button>
      {% if query or selected_dia %}
        <a href="/?banco={{ selected_banco }}" class="tab-btn">Limpiar</a>
      {% endif %}
    </form>

    <div class="bank-tabs">
      <a href="/?q={{ query }}&dia={{ selected_dia }}" class="tab-btn {% if not selected_banco %}active{% endif %}">🌐 Todas las Entidades</a>
      <a href="/?banco=Santander&q={{ query }}&dia={{ selected_dia }}" class="tab-btn {% if selected_banco == 'Santander' %}active{% endif %}">🔴 Santander</a>
      <a href="/?banco=Banco Hipotecario&q={{ query }}&dia={{ selected_dia }}" class="tab-btn {% if selected_banco == 'Banco Hipotecario' %}active{% endif %}">🔵 Banco Hipotecario</a>
      <a href="/?banco=Banco Supervielle&q={{ query }}&dia={{ selected_dia }}" class="tab-btn {% if selected_banco == 'Banco Supervielle' %}active{% endif %}">🟣 Supervielle</a>
    </div>

    <div class="grid">
      {% if not promos %}
        <div style="text-align: center; padding: 60px 20px; color: var(--text-muted); background: var(--card-bg); border-radius: 12px;">
          <h3>No se encontraron promociones con los filtros seleccionados.</h3>
        </div>
      {% endif %}
      {% for p in promos %}
        <div class="card">
          <div class="card-header">
            <div class="sm-name">{{ p.supermercado }}</div>
            <div class="discount">{{ p.descuento }}</div>
          </div>
          <div class="chips">
            {% if 'santander' in p.banco|lower %}
              <span class="chip chip-santander">🏛️ Santander</span>
            {% elif 'hipotecario' in p.banco|lower %}
              <span class="chip chip-hipotecario">🏛️ Hipotecario</span>
            {% else %}
              <span class="chip chip-supervielle">🏛️ Supervielle</span>
            {% endif %}
            <span class="chip chip-meta">📅 {{ p.dias }}</span>
            <span class="chip chip-meta">💰 Tope: {{ p.tope_reintegro }}</span>
          </div>
          {% if p.medio_pago and p.medio_pago != 'No especificado' %}
            <div class="payment">💳 {{ p.medio_pago }}</div>
          {% endif %}
          <div class="cond">{{ p.condiciones[:250] }}{% if p.condiciones|length > 250 %}...{% endif %}</div>
          <div class="card-footer">
            <span>Última verificación: {{ p.ultima_consulta }}</span>
            <a href="{{ p.enlace_original }}" target="_blank" class="btn-link">🔗 Ver en Sitio Oficial</a>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""

@app.route("/")
def index():
    refresh = request.args.get("refresh")
    if refresh:
        mgr.run_sync_all()

    banco = request.args.get("banco", "").strip() or None
    query = request.args.get("q", "").strip()
    dia = request.args.get("dia", "").strip() or None

    promos = db.get_active_promotions(banco=banco, query=query, day=dia)

    counts = {
        "Santander": len(db.get_active_promotions(banco="Santander")),
        "Banco Hipotecario": len(db.get_active_promotions(banco="Banco Hipotecario")),
        "Banco Supervielle": len(db.get_active_promotions(banco="Banco Supervielle")),
    }

    return render_template_string(
        HTML_TEMPLATE,
        promos=promos,
        selected_banco=banco or "",
        selected_dia=dia or "",
        query=query,
        counts=counts
    )

if __name__ == "__main__":
    host = os.environ.get("HOST", WEB_HOST)
    port = int(os.environ.get("PORT", WEB_PORT))
    print("\n" + "="*60)
    print(f"  SERVIDOR WEB DE PROMOCIONES DE CÓRDOBA INICIADO")
    print(f"  Escuchando en: http://{host}:{port} (o http://localhost:{port})")
    print("  Nota: Al cerrar la pestaña web, el host sigue corriendo.")
    print("  Para detenerlo, presiona Ctrl + C en esta consola.")
    print("="*60 + "\n")
    app.run(host=host, port=port, debug=False)

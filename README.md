# 🛒 Promociones Bancarias de Supermercados en Argentina

Aplicación de escritorio desarrollada en **Python** diseñada para buscar, recopilar, organizar, almacenar y presentar de manera clara y visual las promociones y beneficios vigentes exclusivamente en el rubro de **supermercados**, consultando únicamente las páginas oficiales de los tres bancos indicados:
- **Banco Santander Argentina** ([www.santander.com.ar](https://www.santander.com.ar/))
- **Banco Hipotecario** ([www.hipotecario.com.ar](https://www.hipotecario.com.ar/))
- **Banco Supervielle** ([www.supervielle.com.ar](https://www.supervielle.com.ar/))

---

## 🚀 Características Principales

1. **Extracción Exclusiva de Fuentes Oficiales**:
   - Conexión directa a los portales y endpoints oficiales de promociones de cada entidad bancaria.
   - Sin intermediarios, sin scraping de redes sociales y sin datos ficticios.
   - Filtrado estricto: Descarta automáticamente gastronomía, combustibles, indumentaria, turismo, electrodomésticos, etc.

2. **Datos Completos por Promoción**:
   - Banco emisor.
   - Nombre del supermercado (Coto, Jumbo, Disco, Vea, ChangoMás, La Anónima, Cooperativa Obrera, Diarco, Átomo, Aiello, etc.).
   - Porcentaje de descuento o beneficio de ahorro.
   - Día o días específicos de la semana en los que aplica.
   - Tope de reintegro (o indicación si es sin tope / condiciones especiales).
   - Medio de pago requerido (Tarjetas de Débito, Crédito, código QR con MODO, tecnología NFC sin contacto Apple Pay / Google Pay).
   - Condiciones y términos legales particulares.
   - Fechas de vigencia (inicio y fin).
   - Enlace directo a la promoción original para consulta en el navegador.
   - Fecha y hora de la última verificación.

3. **Base de Datos SQLite y Persistencia**:
   - Detección automática de promociones **nuevas**, **modificadas** y **vencidas**.
   - Si una promoción caduca en el portal oficial, se remueve de la vista activa y se conserva en el historial de la base de datos.
   - Si un sitio bancario presenta intermitencias temporales, se preservan los últimos datos vigentes y se informa con una alerta visual la fecha de la última sincronización exitosa.

4. **Sistema de Actualización Continua**:
   - Programación en segundo plano que ejecuta una búsqueda automática **cada 6 horas**.
   - Botón interactivo de **Actualización Manual** para consultar en tiempo real.
   - Operaciones asíncronas mediante hilos (`threading`) para garantizar que la interfaz gráfica nunca se bloquee ni congele.

5. **Interfaz Gráfica Moderna (CustomTkinter)**:
   - Dividida en 3 secciones independientes:
     - **SECCIÓN 1: BANCO SANTANDER**
     - **SECCIÓN 2: BANCO HIPOTECARIO**
     - **SECCIÓN 3: BANCO SUPERVIELLE**
     - Sección adicional con vista consolidada de todas las entidades.
   - Tarjetas informativas con etiquetas de colores, badges y botón de acceso a la web oficial.
   - Buscador rápido por nombre de supermercado y filtro por día de la semana.

---

## 📂 Estructura del Proyecto

```text
promociones_bancarias/
│
├── config.py                 # Constantes, rutas, palabras clave y configuración de logs
├── database.py               # Capa de datos SQLite (tablas promociones y sync_logs)
├── models.py                 # Dataclasses de datos (Promocion, SyncLog)
│
├── scrapers/
│   ├── __init__.py
│   ├── base.py               # BaseScraper con validación de rubro y limpieza de texto
│   ├── santander.py          # Scraper oficial de Banco Santander
│   ├── hipotecario.py        # Scraper oficial de Banco Hipotecario
│   ├── supervielle.py        # Scraper oficial de Banco Supervielle
│   └── manager.py            # Coordinador de scraping y filtros de supermercados
│
├── scheduler.py              # Servicio de actualización automática periódica (hilo demonio)
│
├── ui/
│   ├── __init__.py
│   ├── app.py                # Ventana principal, navegación por pestañas y buscador
│   ├── components.py         # Tarjetas de promociones con diseño moderno
│   └── theme.py              # Estilos visuales y paleta cromática institucional
│
├── data/
│   ├── promociones_bancarias.db  # Base de datos SQLite persistente
│   └── app.log                   # Registro de auditoría y operaciones
│
├── main.py                   # Módulo ejecutable principal
├── requirements.txt          # Lista de dependencias de Python
└── run.py                    # Acceso directo para ejecutar desde la raíz
```

---

## 🛠️ Instalación y Requisitos

### Requisitos previos
- **Python 3.10 o superior** instalado en el sistema.
- Conexión a Internet para consultar las páginas oficiales.

### Paso 1: Instalar dependencias
Abre una terminal o consola de comandos en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

Las librerías principales instaladas son:
- `requests` y `beautifulsoup4`: Consultas HTTP y parseo estructurado.
- `curl_cffi`: Conexión de alta fidelidad para salvaguardar peticiones dinámicas.
- `customtkinter`: Interfaz gráfica moderna con soporte nativo de modo oscuro/claro.

---

## 💻 Instrucciones de Uso

### 1. Iniciar la aplicación de escritorio
Para abrir la interfaz gráfica, ejecuta:

```bash
python run.py
```
*(o también: `python promociones_bancarias/main.py`)*

Al abrirse, la aplicación mostrará las promociones vigentes organizadas por banco. Podrás:
- Navegar entre las secciones **Santander**, **Banco Hipotecario** y **Supervielle**.
- Buscar un supermercado específico escribiendo en la barra superior (ej: `Coto`, `Jumbo`, `Día`).
- Filtrar por día de la semana desde el menú desplegable.
- Presionar el botón **🔗 Ver en Sitio Oficial** en cualquier tarjeta para abrir la promoción en tu navegador web.
- Hacer clic en **🔄 Actualizar Ahora** para forzar una consulta inmediata a los portales oficiales.

---

### 2. Comandos por Consola (CLI) y Modo Web

- **Servidor Web (Host `0.0.0.0` y puerto dinámico `PORT`):**
  ```bash
  python run.py --web
  ```
  *Por defecto escuchará en `0.0.0.0:5000`. Si configuras la variable de entorno `PORT` (ej: `PORT=8080`), tomará automáticamente dicho puerto.*

- **Sincronizar las promociones desde la consola:**
  ```bash
  python run.py --sync
  ```

- **Listar todas las promociones vigentes:**
  ```bash
  python run.py --list
  ```

- **Listar promociones de un banco específico:**
  ```bash
  python run.py --list --banco "Banco Hipotecario"
  python run.py --list --banco "Santander"
  python run.py --list --banco "Supervielle"
  ```

---

## 🔒 Cumplimiento de Políticas y Restricciones
- La aplicación **no** solicita credenciales bancarias.
- **No** interactúa con cuentas de usuario, saldos ni pasarelas de pago.
- Solo consume y procesa información pública sobre descuentos comerciales vigentes en supermercados.
- Respeta los términos de uso y las políticas de los sitios web oficiales consultados.

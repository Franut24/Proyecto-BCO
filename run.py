import sys
from pathlib import Path

# Agregar promociones_bancarias al path
app_dir = Path(__file__).resolve().parent / "promociones_bancarias"
sys.path.insert(0, str(app_dir))

from promociones_bancarias.main import main

if __name__ == "__main__":
    main()

# Carpeta donde guardar la documentación
DOCS_DIR = docs

# Paquete o ruta del código a documentar
PACKAGE = src/printtool

# listado de dependencias para apt (igual que en instalar.md)
APTPKGS = python3-dev libcairo2-dev libgirepository1.0-dev pkg-config python3-tk


test:
	@pytest

install:
	@echo "Instalando Paquete..."
	pipx install . --force
	@command -v printtool >/dev/null 2>&1 && printtool --help >/dev/null 2>&1 \
		&& echo "✓ printtool instalado y disponible en el PATH" \
		|| (echo "✗ printtool no quedó funcional en el PATH" >&2; exit 1)

# acción de clic derecho en Nemo (Cinnamon); se fija la ruta absoluta porque Nemo no hereda el PATH de la terminal
NEMO_DIR = $(HOME)/.local/share/nemo/actions

.PHONY: nemo
nemo:
	@PT=$$(command -v printtool) || { echo "✗ printtool no está en el PATH, ejecuta antes 'make install'" >&2; exit 1; }; \
	mkdir -p $(NEMO_DIR) && sed "s|@PRINTTOOL@|$$PT|" nemo/printtool.nemo_action > $(NEMO_DIR)/printtool.nemo_action \
		&& echo "✓ Acción de Nemo instalada usando $$PT (reinicia Nemo con: nemo -q)"

# entorno de desarrollo: venv local con el paquete editable y las dependencias de test
VENV = venv

installdev:
	@echo "Preparando entorno de desarrollo en $(VENV)/ ..."
	git submodule update --init
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"
	@echo "✓ Listo. Activa con: source $(VENV)/bin/activate"

# preparar el entorno de sistema (paquetes apt necesarios)
dependencias:
	@echo "Instalando dependencias de sistema..."
	sudo apt update && \
	sudo apt install -y python3-dev libcairo2-dev libgirepository1.0-dev pkg-config python3-tk


# Generar documentación
docs:
	@echo "Generando documentación con pdoc..."
	pdoc $(PACKAGE) -o $(DOCS_DIR) --docformat google

# Servir documentación localmente
serve-docs:
	@echo "Sirviendo documentación en http://localhost:1234 ..."
	pdoc $(PACKAGE) -p 1234 --docformat google

# Limpiar carpeta de documentación
clean-docs:
	@echo "Eliminando carpeta de documentación..."
	rm -rf $(DOCS_DIR)
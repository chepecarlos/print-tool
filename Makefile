# Carpeta donde guardar la documentación
DOCS_DIR = docs

# Paquete o ruta del código a documentar
PACKAGE = src/printtool

# listado de dependencias para apt (igual que en instalar.md)
APTPKGS = python3-dev libcairo2-dev libgirepository1.0-dev pkg-config python3-tk


install:
	@echo "Instalando Paquete..."
	pipx install . --force

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
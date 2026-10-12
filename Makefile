CARPETA_GRAMATICA = grammar
GRAMATICA         = Cocosette.g4

# Misma carpeta de salida (src/parser), vista desde dos directorios de
# trabajo distintos: "generar" se ejecuta desde dentro de grammar/,
# "limpiar" y "validar" se ejecutan desde la raiz del proyecto.
SALIDA_DESDE_GRAMATICA = ../src/parser
SALIDA_DESDE_RAIZ      = src/parser

.PHONY: generar validar ejecutar probar evidencia limpiar

# Importante: nos movemos a grammar/ antes de invocar antlr4. Si se
# invoca "antlr4 -o src/parser grammar/Cocosette.g4" desde la raiz,
# ANTLR replica la ruta relativa del .g4 dentro de la salida y termina
# creando src/parser/grammar/... en vez de dejar los archivos
# directamente en src/parser/.
generar:
	cd $(CARPETA_GRAMATICA) && antlr4 -Dlanguage=Python3 -visitor -o $(SALIDA_DESDE_GRAMATICA) $(GRAMATICA)

validar:
	python3 src/validar.py ejemplos/validos/*.coco
	python3 src/validar.py ejemplos/invalidos/*.coco

# Uso: make ejecutar ARCHIVO=ejemplos/validos/04_pipeline_corte2.coco
ARCHIVO ?= ejemplos/validos/04_pipeline_corte2.coco
ejecutar:
	python3 -m src.ejecutar $(ARCHIVO)

# Pruebas automaticas (Tabla, programas completos y errores semanticos)
probar:
	python3 -m pytest tests -v

# Evidencia del Corte 2: ejecuta los programas completos, guarda la salida de
# consola en docs/evidencia/*.txt y los CSV exportados en salidas/
evidencia:
	mkdir -p docs/evidencia
	for f in ejemplos/validos/0[4-7]_*.coco; do \
		python3 -m src.ejecutar $$f > docs/evidencia/$$(basename $$f .coco).txt || exit 1; \
	done

limpiar:
	# ! -name '__init__.py': ese archivo no es generado, esta versionado
	# a mano (explica el proposito de la carpeta) y el patron *.py de
	# abajo lo borraria si no se excluye explicitamente.
	find $(SALIDA_DESDE_RAIZ) -type f ! -name '__init__.py' -delete
	rm -rf $(SALIDA_DESDE_RAIZ)/__pycache__

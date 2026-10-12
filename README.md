# COCOSETTE — DSL

Proyecto

`Cocosette` es un lenguaje de dominio específico (DSL) para describir, con sintaxis declarativa y encadenada (`|>`), flujos, preparación, análisis y visualización de datos, sin escribir directamente el código Python. 
Ese código (Cortes 2 y 3) se implementa desde cero en Python: no se usa pandas, NumPy ni Matplotlib.

**Caso de estudio elegido: Ventas.** 
De las opciones (ventas, movilidad, datos ambientales, educación, salud pública, telecomunicaciones), se seleccionó *ventas* por su complejidad.

> **NOTA**: *Cocosette* es el nombre del lenguaje (por eso el prefijo `COCO` de los tokens).


## CORTE II — Semántica y procesamiento

Se implementó el motor de ejecución:

- Gramática extendida: (`grammar/Cocosette.g4`):
    - `crear`
    - `ordenar`
    - `renombrar`
    - `eliminar_duplicados`
    - `eliminar_nulos`/`rellenar_nulos`
    - `convertir`
    - `agrupar por` + `resumir` y `guardar ... como "x.csv"`.
- **Visitor** (`src/evaluador.py`) para el árbol sintáctico.
- **Contexto / tabla de símbolos** (`src/contexto.py`).
- **Tabla** propia en Python, reemplazo de `pandas.DataFrame`
  (`src/tabla.py`).
- Errores semánticos con línea y columna: variable no declarada, columna inexistente, tipos incompatibles y operación no permitida.
- Pruebas unitarias y de integración (`tests/`) y 4 programas completos con exportación a CSV (`ejemplos/validos/04..07`), con evidencia en `docs/evidencia/`.

`graficar` es válido sintácticamente pero no genera imágenes.


## ESTRUCTURA
```
Cocosette/
├── README.md
├── requirements.txt
├── Makefile
├── .gitignore
├── grammar/
│   └── Cocosette.g4           Gramática ANTLR4 (lexer + parser)
├── docs/
│   ├── documento_alcance.md   Documento de instrucciones / alcance del DSL
│   ├── documento_corte2.md    Diseño del Corte 2 (Visitor, Tabla, errores semánticos)
│   └── conceptos_antlr.md     Guia de fundamentos de ANTLR (herencia, generacion de codigo)
├── datos/
│   └── ventas.csv             Dataset de ejemplo para el caso de estudio
├── ejemplos/
│   ├── validos/                programas .coco correctos (se ejecutan)
│   ├── invalidos/              errores léxicos/sintácticos
│   └── semanticos/             errores semánticos (variable, columna, tipos, operación)
├── tests/                      Pruebas automáticas (pytest)
├── src/
│   ├── validar.py              Valida sintaxis (Corte 1)
│   ├── ejecutar.py             Ejecuta un .coco completo (Corte 2)
│   ├── evaluador.py            Visitor: ejecuta el árbol sintáctico
│   ├── tabla.py                Tabla (reemplazo de DataFrame) y agregaciones
│   ├── contexto.py             Tabla de símbolos
│   ├── errores.py              ErrorSemantico y colector de errores sintácticos
│   └── parser/                 Destino del código generado por ANTLR (ver abajo)
└── salidas/                    Carpeta destino de resultados (Cortes 2-3)
```


## REQUISITOS

- Python 3.11 o superior
- Java (JDK 11+) y ANTLR 4.13.2, para generar el lexer/parser
- Paquete `antlr4-python3-runtime` (ver `requirements.txt`)


## EJECUCIÓN

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1. Lexer y Parser en Python

Está la gramática (`.g4`) pero no lo que ANTLR genera.
Generarlo así:

```
make generar
```
o
```
ANTLR4_TOOLS_ANTLR_VERSION=4.13.2 antlr4 -Dlanguage=Python3 -visitor -listener grammar/Cocosette.g4
```

Esto crea `CocosetteLexer.py`, `CocosetteParser.py`, `CocosetteVisitor.py` y los archivos `.tokens`/`.interp` dentro de `src/parser/`. 

> **NOTA**: Ejecutarlo desde `grammar/`, o ANTLR replica la ruta  del `.g4` dentro de la salida y crea `src/parser/grammar/...` en vez de dejar los archivos directamente en `src/parser/`.)


### 2. Validar programas de ejemplo

```
make validar
```

Esto ejecuta `src/validar.py` sobre los tres programas válidos y los tres inválidos, mostrando el árbol de análisis sintáctico o los errores léxicos/sintácticos (con línea y columna) según corresponda.


### 3. Ejecutar un programa y correr las pruebas

```
make ejecutar ARCHIVO=ejemplos/validos/04_pipeline_corte2.coco
make probar        # pruebas unitarias y de integración
make evidencia     # regenera docs/evidencia/ y los CSV de salidas/
```

Siempre desde la raíz del repositorio: las rutas de los CSV (`datos/ventas.csv`, `salidas/...`) depende de dónde se ejecuta.


## CORTE III
- **Corte 3:** generar de gráficas, interfaz de línea de comandos y caso de estudio real.

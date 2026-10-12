# Cocosette — DSL para Ciencia de Datos y Visualización

Proyecto de curso — **Lenguajes de Programación y Transducción**
Universidad Sergio Arboleda — Semestre 2026-2
Docente: Joaquín F. Sánchez

`Cocosette` es un lenguaje de dominio específico (DSL) que permite
describir, con una sintaxis declarativa y encadenada (`|>`), flujos
reproducibles de carga, preparación, análisis y visualización de datos,
sin escribir directamente el código Python subyacente. Ese código
subyacente (Cortes 2 y 3) se implementa desde cero en Python puro: el
equipo decidió no depender de pandas, NumPy ni Matplotlib aunque el
enunciado del curso las sugiere como apoyo opcional — ver la
justificación en [`docs/documento_alcance.md`](docs/documento_alcance.md#2-usuarios-entradas-salidas-y-restricciones).

**Caso de estudio elegido: Ventas.** De las opciones sugeridas en el
enunciado (ventas, movilidad, datos ambientales, educación, salud
pública, telecomunicaciones), se seleccionó *ventas* por tener la
menor complejidad léxica: solo requiere literales numéricos, cadenas
y fechas como texto, sin unidades técnicas, códigos especializados ni
estructuras geoespaciales. La justificación completa está en
[`docs/documento_alcance.md`](docs/documento_alcance.md).

> **Nota sobre el nombre:** "Cocosette" es el nombre de marca elegido
> por el equipo para el lenguaje (y se refleja en el prefijo `COCO` de
> los tokens internos de la gramática). No cambia el dominio del caso
> de estudio, que sigue siendo ventas.

## Estado del proyecto: Corte 2 — Semántica y procesamiento de datos

Ya están implementados el **front-end** (Corte 1) y el **motor de
ejecución** (Corte 2):

- Gramática ANTLR4 extendida (`grammar/Cocosette.g4`): `crear`, `ordenar`,
  `renombrar`, `eliminar_duplicados`, `eliminar_nulos`/`rellenar_nulos`,
  `convertir`, `agrupar por` + `resumir` y `guardar ... como "x.csv"`.
- Patrón **Visitor** (`src/evaluador.py`) que ejecuta el árbol sintáctico.
- **Contexto / tabla de símbolos** (`src/contexto.py`).
- **Tabla** propia en Python puro, reemplazo de `pandas.DataFrame`
  (`src/tabla.py`).
- Errores semánticos con línea y columna: variable no declarada, columna
  inexistente, tipos incompatibles y operación no permitida.
- Pruebas unitarias y de integración (`tests/`) y 4 programas completos con
  exportación a CSV (`ejemplos/validos/04..07`), con evidencia en `docs/evidencia/`.

`graficar` se **reconoce** sintácticamente pero aún no genera imagen:
eso es el Corte 3. Detalle del diseño en
[`docs/documento_corte2.md`](docs/documento_corte2.md).

## Estructura del repositorio

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

## Requisitos

- Python 3.11 o superior
- Java (JDK 11+) y ANTLR 4.13.2, para generar el lexer/parser
- Paquete `antlr4-python3-runtime` (ver `requirements.txt`)

## Puesta en marcha

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1. Generar el lexer y el parser en Python

El repositorio incluye la gramática (`.g4`) pero **no** el código que
ANTLR genera a partir de ella, porque es un artefacto reproducible.
Genéralo así:

```
make generar
# equivalente a:
# cd grammar && antlr4 -Dlanguage=Python3 -visitor -o ../src/parser Cocosette.g4
```

Esto crea `CocosetteLexer.py`, `CocosetteParser.py`, `CocosetteVisitor.py`
y los archivos `.tokens`/`.interp` dentro de `src/parser/`. (Importante:
hay que ejecutarlo desde dentro de `grammar/`, o ANTLR replica la ruta
relativa del `.g4` dentro de la salida y termina creando
`src/parser/grammar/...` en vez de dejar los archivos directamente en
`src/parser/`.)

¿Quieres entender exactamente qué genera cada clase y de dónde hereda?
Ver [`docs/conceptos_antlr.md`](docs/conceptos_antlr.md).

> Si tu entorno de calificación necesita el código ya generado dentro
> del repositorio, quita las líneas correspondientes de `.gitignore` y
> haz commit de esos archivos después de ejecutar `make generar`.

### 2. Validar los programas de ejemplo

```
make validar
```

Esto ejecuta `src/validar.py` sobre los tres programas válidos y los
tres inválidos, mostrando el árbol de análisis sintáctico o los
errores léxicos/sintácticos (con línea y columna) según corresponda.

### 3. Ejecutar un programa y correr las pruebas

```
make ejecutar ARCHIVO=ejemplos/validos/04_pipeline_corte2.coco
make probar        # pruebas unitarias y de integración
make evidencia     # regenera docs/evidencia/ y los CSV de salidas/
```

Siempre desde la raíz del repositorio: las rutas de los CSV
(`datos/ventas.csv`, `salidas/...`) son relativas a donde se ejecuta.

## Próximo corte

- **Corte 3:** generación real de gráficas (sin Matplotlib), interfaz de
  línea de comandos y caso de estudio completo con datos reales.

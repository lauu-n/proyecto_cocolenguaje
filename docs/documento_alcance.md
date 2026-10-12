# Documento de alcance — DSL `Cocosette`

> **Nota:** este documento describe el alcance y la gramática del Corte 1. Las
> instrucciones, reglas semánticas y decisiones del Corte 2 están en
> [`documento_corte2.md`](documento_corte2.md).

**Curso:** Lenguajes de Programación y Transducción
**Proyecto:** Lenguaje de Dominio Específico para Ciencia de Datos y Visualización
**Corte:** 1 — Especificación y front-end del lenguaje
**Caso de estudio:** Ventas

---

## 1. Descripción general y dominio seleccionado

`Cocosette` es un DSL declarativo, basado en encadenamiento de
operaciones (`|>`), para describir flujos reproducibles de carga,
preparación, análisis y visualización de datos.

El enunciado del proyecto sugiere seis dominios posibles para el caso
de estudio final: ventas, movilidad, datos ambientales, educación,
salud pública y telecomunicaciones. Se eligió **ventas** por tener la
**menor complejidad léxica** de las seis opciones:

| Dominio | Por qué se descartó (mayor complejidad léxica) |
|---|---|
| Movilidad | Requiere coordenadas geoespaciales y formatos de fecha/hora combinados |
| Datos ambientales | Requiere unidades científicas (ppm, °C, µg/m³) y notación con símbolos adicionales |
| Educación | Requiere escalas de calificación heterogéneas entre instituciones |
| Salud pública | Requiere codificación clínica y vocabulario sensible |
| Telecomunicaciones | Requiere unidades técnicas compuestas (Mbps, ms de latencia) |
| **Ventas (elegido)** | Solo usa literales numéricos, cadenas de texto y fechas como texto plano; sin unidades ni notación especializada |

Ventas también coincide con el ejemplo de referencia del enunciado del
proyecto, lo que facilita mantener continuidad de vocabulario entre lo
propuesto por el curso y lo implementado por el equipo.

## 2. Usuarios, entradas, salidas y restricciones

- **Usuarios:** estudiantes o analistas que quieran describir un flujo
  de análisis de datos de ventas sin escribir directamente el código
  Python que hace la carga, el filtrado, las agregaciones y las
  gráficas (código que, en este proyecto, se implementa desde cero,
  sin pandas/NumPy/Matplotlib — ver restricciones más abajo).
- **Entradas:** archivos fuente `.coco` (programas del DSL) y, a
  partir del Corte 2, archivos CSV de datos reales.
- **Salidas:**
  - En este Corte 1: árbol de análisis sintáctico y reporte de errores
    léxicos/sintácticos con línea y columna.
  - En cortes futuros (fuera de alcance aquí): tablas transformadas,
    estadísticas, archivos CSV exportados e imágenes PNG de gráficas.
- **Restricciones de diseño** (justificadas en la sección 8):
  - Los identificadores solo admiten letras ASCII, dígitos y guion
    bajo (sin tildes ni "ñ"); se recomienda escribir `anio` en vez de
    `año`.
  - `x` y `y` son palabras reservadas (usadas en `graficar`) y no
    pueden usarse como nombre de columna o variable.
  - Las cadenas de texto no admiten saltos de línea internos.
  - Cada sentencia termina explícitamente en `;`.
  - **Sin bibliotecas de terceros para datos ni graficación.** El
    enunciado del curso sugiere pandas, NumPy y Matplotlib como apoyo
    opcional (ver requisitos técnicos del enunciado). Este equipo
    decide no usarlas: el motor de ejecución de los Cortes 2 y 3
    (lectura/escritura de CSV, filtrado, agregaciones, estadísticas
    descriptivas y generación de gráficas) se implementa con código
    propio sobre Python puro. Sí se permiten módulos de la librería
    estándar de Python (por ejemplo `csv`, `math`, `statistics`),
    porque son parte del lenguaje, no bibliotecas de ciencia de datos
    ya construidas para este dominio. `antlr4-python3-runtime` queda
    fuera de esta restricción porque el uso de ANTLR4 es un requisito
    técnico obligatorio del enunciado (sección 7), no una biblioteca
    opcional de apoyo.

## 3. Alcance de esta entrega (Corte 1)

**Incluido:**

- Delimitación del dominio y casos de uso (ventas).
- Diseño de palabras reservadas, operadores, literales y sentencias.
- Gramática formal en BNF/EBNF (sección 6).
- Gramática implementada en ANTLR4 (`grammar/Cocosette.g4`).
- Instrucciones para generar el lexer y el parser en Python.
- Reconocimiento sintáctico de: asignaciones, expresiones
  aritmético-lógicas, carga de CSV, selección de columnas, filtros con
  comparaciones simples y una instrucción de visualización.
- Programas de ejemplo correctos e incorrectos (`ejemplos/`) que
  validan el lexer y el parser.

**Fuera de alcance de esta entrega** (el Corte 2 ya está implementado: ver
[`documento_corte2.md`](documento_corte2.md)):

- ~~Corte 2: patrón Visitor, tabla de símbolos, columnas calculadas,
  agrupamiento, agregaciones, tratamiento de valores faltantes,
  escritura de resultados en CSV.~~ (hecho)
- Corte 3: generación real de las gráficas y exportación a PNG,
  interfaz de línea de comandos completa, caso de estudio final con
  datos reales.

En particular, aunque la gramática ya reconoce la sintaxis completa de
`graficar` (incluyendo los cinco tipos de gráfica), **no se produce
ninguna gráfica en este corte**: solo se valida que la instrucción esté
bien escrita.

## 4. Palabras reservadas

| Palabra | Token interno | Uso |
|---|---|---|
| `cargar` | `COCOCARGAR` | Cargar un archivo CSV |
| `seleccionar` | `COCOSELECCIONAR` | Seleccionar columnas dentro de un pipeline |
| `filtrar` | `COCOFILTRAR` | Filtrar filas dentro de un pipeline |
| `donde` | `COCODONDE` | Introduce la condición de un filtro |
| `graficar` | `COCOGRAFICAR` | Inicia una instrucción de visualización |
| `titulo` | `COCOTITULO` | Título opcional de una gráfica |
| `guardar` | `COCOGUARDAR` | Introduce la ruta de exportación de una gráfica |
| `como` | `COMO` | Acompaña a `guardar` |
| `barras`, `lineas`, `histograma`, `dispersion`, `caja` | `COCOBARRAS`, `COCOLINEAS`, `COCOHISTOGRAMA`, `COCODISPERSION`, `COCOCAJA` | Tipos de gráfica |
| `x`, `y` | `EJE_X`, `EJE_Y` | Ejes de una gráfica |
| `verdadero`, `falso` | `COCOBOOLEANO` | Literales booleanos |

Son 17 palabras reservadas en total: un vocabulario deliberadamente
pequeño para mantener baja la complejidad léxica del reconocedor. El
prefijo `COCO` en el nombre interno del token es solo una convención
de branding del equipo (tema "Cocosette"); la palabra que efectivamente
se escribe en un programa `.coco` no cambia (sigue siendo `cargar`,
`seleccionar`, etc.).

## 5. Operadores, literales y tipos de datos

**Operadores aritméticos:** `+` `-` `*` `/` `%` `^`
**Operadores relacionales:** `<` `<=` `>` `>=` `==` `!=`
**Operadores lógicos:** `&&` `||` `!`
**Otros símbolos:** `=` (asignación), `|>` (pipeline), `( )` (agrupación),
`[ ]` (lista de columnas), `,` `;`

**Literales y tipos:**

| Tipo | Ejemplo | Descripción |
|---|---|---|
| Entero (`INT`) | `120` | Secuencia de dígitos |
| Decimal (`FLOAT`) | `0.15` | Dígitos, punto, dígitos |
| Cadena (`STRING`) | `"datos/ventas.csv"` | Entre comillas dobles, sin salto de línea |
| Booleano (`COCOBOOLEANO`) | `verdadero`, `falso` | Palabras reservadas |

Los identificadores (`ID`) representan nombres de variables o de
columnas: deben iniciar con una letra o guion bajo, seguidos de
letras, dígitos o guion bajo.

## 6. Sentencias soportadas en el Corte 1

```
# Asignación simple con expresión
descuento = 0.15;

# Carga de un archivo CSV
ventas = cargar "datos/ventas.csv";

# Pipeline de selección y filtrado
ventas_filtradas = ventas
    |> seleccionar [fecha, ciudad, categoria, unidades, precio]
    |> filtrar donde unidades > 0 && precio > 0;

# Reconocimiento sintáctico de una visualización (no se genera aún)
graficar barras resumen
    x ciudad
    y precio
    titulo "Precio por ciudad"
    guardar como "salidas/precio_ciudad.png";
```

## 7. Gramática formal (BNF/EBNF)

La siguiente gramática EBNF describe el alcance del Corte 1. En la
implementación ANTLR4 (`grammar/Cocosette.g4`) la jerarquía de
expresiones se escribe de forma left-recursive, que ANTLR4 reescribe
internamente de forma equivalente a la mostrada aquí.

```ebnf
programa          ::= { sentencia } ;
sentencia         ::= asignacion ";" | cocoGraficar ";" ;

asignacion        ::= IDENTIFICADOR "=" cocoFuente ;
cocoFuente        ::= cargaCSV | pipeline | expresion ;
cargaCSV          ::= "cargar" CADENA ;
pipeline          ::= IDENTIFICADOR operacion { operacion } ;   (* al menos una *)
operacion         ::= "|>" ( cocoSeleccion | cocoFiltro ) ;
cocoSeleccion     ::= "seleccionar" "[" listaCocolumnas "]" ;
cocoFiltro        ::= "filtrar" "donde" cocondicion ;
listaCocolumnas   ::= IDENTIFICADOR { "," IDENTIFICADOR } ;
cocondicion       ::= expresion ;

cocoGraficar      ::= "graficar" cocoGrafica IDENTIFICADOR
                       "x" IDENTIFICADOR
                       "y" IDENTIFICADOR
                       [ "titulo" CADENA ]
                       [ "guardar" "como" CADENA ] ;
cocoGrafica       ::= "barras" | "lineas" | "histograma"
                     | "dispersion" | "caja" ;

expresion         ::= expOr ;
expOr             ::= expAnd { "||" expAnd } ;
expAnd            ::= expIgualdad { "&&" expIgualdad } ;
expIgualdad       ::= expRelacional { ( "==" | "!=" ) expRelacional } ;
expRelacional     ::= expAditiva { ( "<" | "<=" | ">" | ">=" ) expAditiva } ;
expAditiva        ::= expMultiplicativa { ( "+" | "-" ) expMultiplicativa } ;
expMultiplicativa ::= expUnaria { ( "*" | "/" | "%" ) expUnaria } ;
expUnaria         ::= ( "-" | "!" ) expUnaria | expPotencia ;
expPotencia       ::= expPrimaria [ "^" expUnaria ] ;   (* asociativo a la derecha *)
expPrimaria       ::= literal | IDENTIFICADOR | "(" expresion ")" ;

literal           ::= ENTERO | DECIMAL | CADENA | COCOBOOLEANO ;
COCOBOOLEANO      ::= "verdadero" | "falso" ;

IDENTIFICADOR     ::= LETRA { LETRA | DIGITO | "_" } ;
LETRA             ::= "a".."z" | "A".."Z" | "_" ;
DIGITO            ::= "0".."9" ;
ENTERO            ::= DIGITO { DIGITO } ;
DECIMAL           ::= DIGITO { DIGITO } "." DIGITO { DIGITO } ;
CADENA            ::= '"' { caracter_escapado | cualquier_caracter_excepto('"', '\n') } '"' ;
COMENTARIO        ::= "#" { cualquier_caracter_excepto('\n') } ;  (* se descarta *)
```

## 8. Precedencia y asociatividad de operadores

De mayor a menor precedencia:

1. `- !` (unarios, prefijos)
2. `^` (potencia, asociativo a la derecha)
3. `* / %`
4. `+ -`
5. `< <= > >=`
6. `== !=`
7. `&&`
8. `||`

## 9. Manejo de errores (Corte 1)

El front-end distingue dos niveles de error, ambos reportados con
línea y columna mediante un `ErrorListener` propio
(`src/validar.py`):

- **Léxico:** un carácter o secuencia no reconocida por ninguna regla
  del lexer (por ejemplo, una cadena sin comilla de cierre).
- **Sintáctico:** una secuencia de tokens válidos individualmente pero
  que no respeta ninguna producción de la gramática (por ejemplo, una
  sentencia sin `;`, o el uso de `x`/`y` como identificador).

El manejo semántico (variables no declaradas, columnas inexistentes,
tipos incompatibles, operaciones no permitidas) se implementó en el
Corte 2: ver las reglas R1–R13 en [`documento_corte2.md`](documento_corte2.md).

## 10. Ejemplos de programas válidos e inválidos

Ver la carpeta [`ejemplos/`](../ejemplos):

- `ejemplos/validos/01_carga_y_pipeline.coco` — carga y pipeline de
  selección/filtrado.
- `ejemplos/validos/02_expresiones_basicas.coco` — asignaciones y
  expresiones aritmético-lógicas.
- `ejemplos/validos/03_visualizacion.coco` — reconocimiento sintáctico
  de dos instrucciones `graficar`, con y sin cláusulas opcionales.
- `ejemplos/invalidos/01_error_lexico_cadena_sin_cerrar.coco` — error
  léxico (cadena sin cerrar).
- `ejemplos/invalidos/02_error_sintactico_falta_punto_coma.coco` —
  error sintáctico (falta `;`).
- `ejemplos/invalidos/03_error_palabra_reservada_como_identificador.coco`
  — error sintáctico (uso de `x`/`y` como identificador).

## 11. Decisiones de diseño y justificación

- **`;` como terminador explícito de sentencia**, en vez de depender
  de saltos de línea significativos (como en el ejemplo ilustrativo
  del enunciado): evita construir un lexer sensible a indentación o a
  la posición del salto de línea, reduciendo la complejidad léxica del
  reconocedor sin perder legibilidad, ya que el operador `|>` sigue
  permitiendo partir un pipeline en varias líneas.
- **Operadores lógicos simbólicos (`&&`, `||`, `!`)** en vez de
  palabras como "y"/"o": evita la ambigüedad con las palabras
  reservadas `x`/`y` usadas como ejes en `graficar`, y mantiene el
  conjunto de palabras reservadas más pequeño.
- **Identificadores solo ASCII**: simplifica la regla léxica de
  identificador (no requiere tratar rangos Unicode) a cambio de pedir
  nombres de columna sin tildes, una restricción menor y documentada.
- **Reconocimiento sintáctico completo de `graficar`** (los cinco
  tipos de gráfica y sus cláusulas opcionales) aunque el corte actual
  no lo ejecute: permite reutilizar la misma gramática sin cambios
  cuando en el Corte 3 se implemente la generación real de las
  gráficas.
- **Reglas con alternativas etiquetadas** (`fuenteCarga`,
  `fuentePipeline`, `fuenteExpresion`, y las etiquetas de `expresion`):
  no aportan nada en el Corte 1, pero facilitan escribir el Visitor en
  el Corte 2 sin reestructurar la gramática.
- **Prefijo `COCO` en los tokens del lexer** (`COCOCARGAR`,
  `COCOSELECCIONAR`, `COCOGRAFICAR`, etc.) y nombres de regla con el
  mismo tema (`cocoFuente`, `cocoSeleccion`, `cocoFiltro`,
  `cocondicion`, `cocoGraficar`, `cocoGrafica`): es una convención de
  branding interna del equipo para identificar de un vistazo, dentro
  del `.g4` y del código generado, qué pertenece a este DSL. No afecta
  la sintaxis visible de un programa `.coco`: las palabras reservadas
  siguen siendo las mismas.
- **Motor de datos y graficación en Python puro, sin pandas, NumPy ni
  Matplotlib**: aunque el enunciado las ofrece como apoyo opcional, el
  equipo prefiere implementar a mano la representación de tablas, las
  agregaciones, las estadísticas descriptivas y el dibujo de las
  gráficas. No cambia el alcance funcional del DSL (las mismas
  operaciones descritas en la tabla de la sección 2 del enunciado
  siguen siendo la meta), pero sí cambia el diseño interno de los
  Cortes 2 y 3 y mantiene `requirements.txt` limitado a
  `antlr4-python3-runtime`.

## 12. Plan para los próximos cortes

- **Corte 2:** implementar el Visitor sobre el árbol ya generado,
  diseñar la tabla de símbolos, y extender la gramática (de forma
  incremental, sin romper lo ya construido) con columnas calculadas
  (`crear`), agrupamiento (`agrupar por`) y agregaciones (`resumir`).
- **Corte 3:** implementar `graficar` con código propio (sin
  Matplotlib) que dibuje directamente los cinco tipos de gráfica sobre
  los datos ya agregados y exporte el resultado a PNG, exportar
  resultados a CSV, construir la interfaz de línea de comandos y
  desarrollar el caso de estudio completo con el dataset de ventas.

## 13. Ver también

[`docs/conceptos_antlr.md`](conceptos_antlr.md) explica, con más
detalle del que cabe aquí, cómo `grammar/Cocosette.g4` se convierte
en código Python (qué genera el comando `antlr4`, de qué clases hereda
cada pieza generada) y cómo encajan entre sí `grammar/Cocosette.g4`,
`src/parser/` y `src/validar.py`. Es la referencia recomendada para
repasar los fundamentos de ANTLR usados en este corte.

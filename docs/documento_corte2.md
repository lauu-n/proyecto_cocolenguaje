# Cocosette — Documento del Corte 2: Semántica y procesamiento de datos

## 1. Qué se agregó respecto al Corte 1

```
.coco → lexer → parser → árbol sintáctico → Evaluador (Visitor) → Tabla → CSV / resultados
        (Corte 1)                           └────────── Corte 2 ──────────┘
```

| Pieza | Archivo | Responsabilidad |
|---|---|---|
| Gramática extendida | `grammar/Cocosette.g4` | Reconocer las instrucciones nuevas |
| Visitor | `src/evaluador.py` | Recorrer el árbol y ejecutar cada nodo |
| Tabla de símbolos | `src/contexto.py` | Asociar identificadores con tablas o valores |
| Motor de datos | `src/tabla.py` | Operaciones tabulares y agregaciones (Python puro) |
| Errores | `src/errores.py` | `ErrorSemantico` con línea y columna |
| Entrada | `src/ejecutar.py` | Une lexer, parser, evaluador y reporte de errores |

## 2. Instrucciones nuevas

| Instrucción | Ejemplo | Efecto |
|---|---|---|
| `crear` | `crear total = unidades * precio` | Columna calculada fila por fila |
| `ordenar por` | `ordenar por total descendiente` | Orden asc. (por defecto) o desc.; nulos al final |
| `renombrar` | `renombrar precio como precio_unitario` | Cambia el nombre de una columna |
| `eliminar_duplicados` | `eliminar_duplicados` | Elimina filas completamente iguales |
| `eliminar_nulos` | `eliminar_nulos` | Elimina filas con algún valor faltante |
| `rellenar_nulos` | `rellenar_nulos unidades con 0` | Reemplaza nulos de una columna |
| `convertir` | `convertir unidades como entero` | Tipos: `entero`, `decimal`, `texto`, `booleano` |
| `agrupar por` | `agrupar por [ciudad]` | Forma grupos (debe ir seguido de `resumir`) |
| `resumir` | `resumir ingreso = suma(total), n = contar()` | Agregaciones: `suma`, `media`, `mediana`, `minimo`, `maximo`, `desviacion_estandar`, `contar`. Después de `agrupar` da una fila por grupo; **sin `agrupar` da estadísticas descriptivas de toda la tabla (una fila)** |
| `guardar` | `guardar resumen como "salidas/r.csv"` | Exporta una tabla a CSV |

Palabras reservadas nuevas: `crear ordenar por ascendiente descendiente
renombrar eliminar_duplicados eliminar_nulos rellenar_nulos con convertir
como entero decimal texto booleano agrupar resumir suma media mediana minimo
maximo desviacion_estandar contar`. **No pueden usarse como nombre de
variable o columna** (por ejemplo, una columna llamada `texto` o `media`).

## 3. Patrón Visitor

`CocosetteVisitor` (generado por ANTLR) tiene un método `visitX` por cada
regla o etiqueta de la gramática. `EvaluadorCocosette` hereda de él y
sobreescribe esos métodos para **ejecutar** en vez de solo recorrer.

- **Pipeline** (`visitFuentePipeline`): obtiene la tabla base del Contexto y
  aplica cada operación en orden; el resultado de una es la entrada de la
  siguiente.
- **Expresiones por fila**: en `filtrar` y `crear`, `self._fila` apunta a la
  fila en curso. Un identificador se busca primero entre las columnas de esa
  fila y luego en el Contexto (variables). Por eso `filtrar donde unidades >= minimo_u`
  mezcla una columna y una variable.
- **`agrupar` → `resumir`**: `agrupar` devuelve un objeto intermedio
  `TablaAgrupada`; solo `resumir` puede consumirlo. `resumir` sin `agrupar`
  trata toda la tabla como un único grupo (estadísticas descriptivas).
- **`graficar`**: se reconoce pero no se ejecuta (Corte 3).

## 4. Tabla de símbolos

`Contexto` guarda un diccionario `identificador → objeto` (una `Tabla` o un
número, texto o booleano). `declarar` crea o reemplaza; `obtener` lanza
`ErrorSemantico` si el identificador no existe.

## 5. Reglas semánticas y errores

Toda violación lanza `ErrorSemantico` con línea y columna del nodo que la causó.
Las cuatro categorías que exige el enunciado tienen un ejemplo ejecutable en
`ejemplos/semanticos/`.

| # | Regla | Categoría |
|---|---|---|
| R1 | Todo identificador debe estar declarado antes de usarse: como variable o, dentro de `filtrar`/`crear`, como columna de la tabla en curso | Variable no declarada |
| R2 | `\|>`, `guardar` y `resumir` solo aplican sobre una tabla (no sobre un número o texto) | Operación no permitida |
| R3 | Las columnas nombradas en `seleccionar`, `ordenar`, `renombrar`, `convertir`, `rellenar_nulos`, `agrupar` y en las agregaciones deben existir en la tabla | Columna inexistente |
| R4 | `renombrar` no puede dar un nombre ya existente; los nombres de salida de `resumir` no pueden repetirse ni coincidir con una columna de agrupación | Operación no permitida |
| R5 | `- * / % ^` y `+` (salvo texto + texto) requieren números | Tipos incompatibles |
| R6 | `< <= > >=` comparan dos números o dos textos; `==`/`!=` no comparan número con texto | Tipos incompatibles |
| R7 | `&& \|\| !` requieren booleanos; la condición de `filtrar` debe ser booleana | Tipos incompatibles |
| R8 | `suma`, `media`, `mediana`, `minimo`, `maximo`, `desviacion_estandar` requieren columna numérica; solo `contar()` admite no llevar columna | Tipos incompatibles / Operación no permitida |
| R9 | `convertir` falla si algún valor no se puede convertir al tipo pedido | Tipos incompatibles |
| R10 | `ordenar` falla si la columna mezcla textos y números | Tipos incompatibles |
| R11 | `agrupar` requiere al menos una columna y debe ir seguido de `resumir`; ninguna otra operación puede usar una tabla agrupada | Operación no permitida |
| R12 | División o módulo por cero | Operación no permitida |
| R13 | `cargar` exige que el archivo exista | Operación no permitida |

| Categoría | Ejemplo ejecutable |
|---|---|
| Variable no declarada | `ejemplos/semanticos/01_variable_no_declarada.coco` |
| Columna inexistente | `ejemplos/semanticos/02_columna_inexistente.coco` |
| Tipos incompatibles | `ejemplos/semanticos/03_tipos_incompatibles.coco` |
| Operación no permitida | `ejemplos/semanticos/04_operacion_no_permitida.coco` |

## 6. Decisiones de diseño

- **Tipos al cargar el CSV**: cada columna se infiere completa (entera, decimal
  o texto). Así `unidades > 0` y `ordenar` son numéricos y no alfabéticos.
- **Nulos**: celda vacía → `None`. Comparar con nulo da falso (la fila no pasa
  el filtro); aritmética con nulo da nulo; las agregaciones ignoran nulos.
- **Inmutabilidad**: cada operación devuelve una `Tabla` nueva; `ventas` no
  cambia después de un pipeline.
- **Desviación estándar poblacional** (divide entre *n*).
- **`eliminar_duplicados`** compara la fila completa.
- **Datos reales**: al cargar, el separador se detecta solo (`,` `;` o tabulador),
  se acepta el BOM de Excel y se ignoran líneas vacías. Los **encabezados se
  normalizan** a identificadores válidos del DSL (sin tildes, minúscula, `_`):
  `Valor Total ($)` → `valor_total`. Si el resultado es una palabra reservada
  se le agrega `_col`. Los CSV exportados usan estos nombres normalizados.
- **`convertir x como tipo`** reutiliza `como` en vez de una palabra reservada
  corta (`a`), que habría impedido llamar `a` a una variable.
- **Lógica booleana con nulos**: `falso && nulo` es falso; `verdadero || nulo` es verdadero.

## 7. Programas completos y evidencia

| Programa | Qué demuestra | Salida |
|---|---|---|
| `04_pipeline_corte2.coco` | Cadena de 8 operaciones + agrupar/resumir | `salidas/resumen_ciudades.csv` |
| `05_ventas_por_ciudad.coco` | Columna calculada, agrupar, resumir, ordenar | `salidas/ventas_por_ciudad.csv` |
| `06_limpieza_y_estadisticas.coco` | Duplicados, nulos, conversión de tipos y estadísticas descriptivas sobre `datos/ventas_sucias.csv` (separador `;`, encabezados con tildes) | `salidas/ventas_limpias.csv`, `salidas/estadisticas_ventas.csv` |
| `07_ranking_categoria_ciudad.coco` | Filtro compuesto, agrupar por dos columnas, renombrar | `salidas/ingreso_categoria_ciudad.csv` |

`make evidencia` ejecuta los cuatro, guarda la salida de consola en
`docs/evidencia/*.txt` y los CSV exportados en `salidas/` (ambos se versionan).

> `datos/ventas_sucias.csv` es un conjunto **sintético** hecho para demostrar la
> limpieza. El caso de estudio final debe usar datos reales o públicos.

## 8. Pruebas

`make probar` ejecuta `tests/`:

- **Unitarias** (`test_tabla.py`): cada operación de `Tabla`, agregaciones,
  nulos, tipos, normalización de nombres y lectura de CSV con `;`/BOM.
- **Integración** (`test_programas.py`): programas `.coco` completos de punta a
  punta, los cuatro errores semánticos, y una verificación de los cálculos
  del DSL contra la librería estándar `statistics`.
- Una prueba comprueba que la lista de palabras reservadas del código coincide
  con la de `grammar/Cocosette.g4`.

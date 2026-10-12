"""
Tabla: reemplazo de pandas.DataFrame para el DSL Cocosette.

Estructura:  columnas (lista de nombres, conserva el orden)
             filas    (lista de diccionarios {columna: valor})
Alcance:     solo lo que el DSL necesita (seleccionar, filtrar, crear,
             ordenar, renombrar, duplicados, nulos, tipos, agrupar, resumir).

Convenciones:
- Un valor faltante se representa con None.
- Los valores se guardan ya convertidos (int, float o str), no como
  texto crudo del CSV. Asi `unidades > 0` y `ordenar por precio`
  funcionan numericamente y no alfabeticamente ("10" < "9").
- Ninguna operacion modifica la tabla original: todas devuelven una
  Tabla nueva (asi `ventas` sigue intacta despues de un pipeline).
- Los errores se lanzan como ErrorSemantico (sin linea/columna; el
  Evaluador se las agrega).
"""
import csv
import math
import os
import re
import unicodedata

from src.errores import ErrorSemantico


# ---------------------------------------------------------------
# Utilidades de tipos
# ---------------------------------------------------------------
def es_numero(valor):
    # bool es subclase de int en Python; aqui NO lo tratamos como numero
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def nombre_tipo(valor):
    if valor is None:
        return "nulo"
    if isinstance(valor, bool):
        return "booleano"
    if isinstance(valor, int):
        return "entero"
    if isinstance(valor, float):
        return "decimal"
    if isinstance(valor, str):
        return "texto"
    return type(valor).__name__


# ---------------------------------------------------------------
# Nombres de columna
# ---------------------------------------------------------------
# Palabras reservadas del lenguaje: no pueden ser nombre de columna.
# MANTENER SINCRONIZADA con grammar/Cocosette.g4 (hay una prueba que lo verifica).
RESERVADAS = {
    "cargar", "seleccionar", "filtrar", "donde", "graficar", "titulo", "guardar",
    "como", "barras", "lineas", "histograma", "dispersion", "caja", "x", "y",
    "verdadero", "falso", "crear", "ordenar", "por", "ascendiente", "descendiente",
    "renombrar", "eliminar_duplicados", "eliminar_nulos", "rellenar_nulos", "con",
    "convertir", "entero", "decimal", "texto", "booleano", "agrupar", "resumir",
    "suma", "media", "mediana", "minimo", "maximo", "desviacion_estandar", "contar",
}


def normalizar_nombre(nombre, usados=()):
    """Convierte el encabezado de un CSV en un identificador valido del DSL:
    sin tildes, en minuscula, con '_' en lugar de espacios/simbolos.
    'Valor Total ($)' -> 'valor_total'. Evita repetidos y palabras reservadas."""
    base = unicodedata.normalize("NFKD", nombre.strip()).encode("ascii", "ignore").decode()
    base = re.sub(r"[^0-9a-zA-Z_]+", "_", base).strip("_").lower() or "columna"
    if base[0].isdigit():
        base = "c_" + base
    if base in RESERVADAS:
        base += "_col"
    candidato, n = base, 2
    while candidato in usados:
        candidato, n = f"{base}_{n}", n + 1
    return candidato


def _inferir_columna(textos):
    """Recibe los textos crudos de una columna y devuelve los valores
    convertidos. Vacio -> None. Si TODOS los no vacios son enteros, la
    columna es entera; si todos son numericos, decimal; si no, texto."""
    no_vacios = [t for t in textos if t.strip() != ""]
    try:
        for t in no_vacios:
            int(t)
        convertir = int
    except ValueError:
        try:
            for t in no_vacios:
                float(t)
            convertir = float
        except ValueError:
            convertir = str
    return [None if t.strip() == "" else convertir(t.strip() if convertir is not str else t)
            for t in textos]


# ---------------------------------------------------------------
# Funciones de agregacion (trabajan sobre una lista de valores)
# ---------------------------------------------------------------
def _numeros(valores, funcion):
    nums = [v for v in valores if v is not None]
    for v in nums:
        if not es_numero(v):
            raise ErrorSemantico(
                f"tipos incompatibles: '{funcion}' requiere valores numericos, "
                f"pero la columna contiene {nombre_tipo(v)} ('{v}')")
    return nums


def suma(valores):
    return sum(_numeros(valores, "suma"))


def media(valores):
    nums = _numeros(valores, "media")
    return sum(nums) / len(nums) if nums else None


def mediana(valores):
    nums = sorted(_numeros(valores, "mediana"))
    n = len(nums)
    if n == 0:
        return None
    mid = n // 2
    return nums[mid] if n % 2 == 1 else (nums[mid - 1] + nums[mid]) / 2


def minimo(valores):
    nums = _numeros(valores, "minimo")
    return min(nums) if nums else None


def maximo(valores):
    nums = _numeros(valores, "maximo")
    return max(nums) if nums else None


def desviacion_estandar(valores):
    """Desviacion estandar POBLACIONAL (divide entre n)."""
    nums = _numeros(valores, "desviacion_estandar")
    n = len(nums)
    if n == 0:
        return None
    m = sum(nums) / n
    return math.sqrt(sum((x - m) ** 2 for x in nums) / n)


def contar(valores):
    """Cuenta los valores no nulos."""
    return len([v for v in valores if v is not None])


AGREGACIONES = {
    "suma": suma,
    "media": media,
    "mediana": mediana,
    "minimo": minimo,
    "maximo": maximo,
    "desviacion_estandar": desviacion_estandar,
    "contar": contar,
}


# ---------------------------------------------------------------
# Resultado intermedio de `agrupar` (solo vive dentro de un pipeline)
# ---------------------------------------------------------------
class TablaAgrupada:
    def __init__(self, tabla, columnas, grupos):
        self.tabla = tabla
        self.columnas = columnas      # columnas de agrupacion
        self.grupos = grupos          # {(valor1, valor2, ...): [filas]}


# ---------------------------------------------------------------
# Tabla
# ---------------------------------------------------------------
class Tabla:
    def __init__(self, columnas, filas):
        self.columnas = list(columnas)
        self.filas = list(filas)

    # ---- E/S ----------------------------------------------------
    @staticmethod
    def desde_csv(ruta):
        """Lee un CSV. Detecta el separador (, ; o tabulador), acepta BOM de
        Excel, ignora lineas vacias y normaliza los nombres de columna."""
        with open(ruta, mode="r", encoding="utf-8-sig", newline="") as archivo:
            primera = archivo.readline()
            archivo.seek(0)
            separador = max([",", ";", "\t"], key=primera.count)
            lector = csv.reader(archivo, delimiter=separador)
            encabezado = next(lector, [])
            crudas = [f for f in lector if any(c.strip() for c in f)]
        columnas = []
        for nombre in encabezado:
            columnas.append(normalizar_nombre(nombre, columnas))
        por_columna = {
            c: _inferir_columna([f[i] if i < len(f) else "" for f in crudas])
            for i, c in enumerate(columnas)}
        filas = [{c: por_columna[c][k] for c in columnas} for k in range(len(crudas))]
        return Tabla(columnas, filas)

    def guardar_csv(self, ruta):
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(ruta, mode="w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=self.columnas)
            escritor.writeheader()   # el encabezado se escribe aunque no haya filas
            for fila in self.filas:
                escritor.writerow({c: ("" if v is None else v) for c, v in fila.items()})

    # ---- Validacion ---------------------------------------------
    def _exigir(self, columna):
        if columna not in self.columnas:
            raise ErrorSemantico(
                f"la columna '{columna}' no existe (columnas disponibles: "
                f"{', '.join(self.columnas)})")

    # ---- Operaciones de pipeline --------------------------------
    def seleccionar(self, columnas):
        for c in columnas:
            self._exigir(c)
        return Tabla(columnas, [{c: f[c] for c in columnas} for f in self.filas])

    def filtrar(self, predicado):
        """predicado(fila) -> bool"""
        return Tabla(self.columnas, [f for f in self.filas if predicado(f)])

    def crear_columna(self, nombre, calcular):
        """calcular(fila) -> valor de la nueva columna en esa fila"""
        columnas = self.columnas if nombre in self.columnas else self.columnas + [nombre]
        filas = []
        for f in self.filas:
            nueva = dict(f)
            nueva[nombre] = calcular(f)
            filas.append(nueva)
        return Tabla(columnas, filas)

    def ordenar(self, columna, descendente=False):
        self._exigir(columna)
        con_valor = [f for f in self.filas if f[columna] is not None]
        sin_valor = [f for f in self.filas if f[columna] is None]   # nulos siempre al final
        try:
            ordenadas = sorted(con_valor, key=lambda f: f[columna], reverse=descendente)
        except TypeError:
            raise ErrorSemantico(
                f"tipos incompatibles: la columna '{columna}' mezcla textos y numeros, "
                f"no se puede ordenar")
        return Tabla(self.columnas, ordenadas + sin_valor)

    def renombrar(self, viejo, nuevo):
        self._exigir(viejo)
        if nuevo in self.columnas and nuevo != viejo:
            raise ErrorSemantico(f"no se puede renombrar a '{nuevo}': ya existe esa columna")
        columnas = [nuevo if c == viejo else c for c in self.columnas]
        filas = [{(nuevo if c == viejo else c): v for c, v in f.items()} for f in self.filas]
        return Tabla(columnas, filas)

    def eliminar_duplicados(self):
        """Elimina filas completamente iguales (conserva la primera)."""
        vistas, resultado = set(), []
        for f in self.filas:
            clave = tuple(f[c] for c in self.columnas)
            if clave not in vistas:
                vistas.add(clave)
                resultado.append(f)
        return Tabla(self.columnas, resultado)

    def eliminar_nulos(self):
        """Elimina las filas que tengan algun valor faltante."""
        return Tabla(self.columnas,
                    [f for f in self.filas if all(v is not None for v in f.values())])

    def rellenar_nulos(self, columna, valor):
        self._exigir(columna)
        filas = []
        for f in self.filas:
            nueva = dict(f)
            if nueva[columna] is None:
                nueva[columna] = valor
            filas.append(nueva)
        return Tabla(self.columnas, filas)

    def convertir_tipo(self, columna, tipo):
        """tipo: 'entero' | 'decimal' | 'texto' | 'booleano'"""
        self._exigir(columna)

        def convertir(v):
            if v is None:
                return None
            try:
                if tipo == "entero":
                    if isinstance(v, str):
                        return int(v)
                    if isinstance(v, float) and v != int(v):
                        raise ValueError
                    return int(v)
                if tipo == "decimal":
                    return float(v)
                if tipo == "texto":
                    return str(v)
                if tipo == "booleano":
                    if isinstance(v, str) and v.lower() in ("verdadero", "falso"):
                        return v.lower() == "verdadero"
                    if isinstance(v, bool):
                        return v
                    raise ValueError
            except ValueError:
                raise ErrorSemantico(
                    f"tipos incompatibles: no se puede convertir '{v}' "
                    f"({nombre_tipo(v)}) a {tipo} en la columna '{columna}'")
            raise ErrorSemantico(f"tipo desconocido: '{tipo}'")

        filas = []
        for f in self.filas:
            nueva = dict(f)
            nueva[columna] = convertir(f[columna])
            filas.append(nueva)
        return Tabla(self.columnas, filas)

    # ---- Agrupar / resumir --------------------------------------
    def agrupar(self, columnas):
        if not columnas:
            raise ErrorSemantico("operacion no permitida: agrupar requiere al menos una columna")
        for c in columnas:
            self._exigir(c)
        grupos = {}
        for f in self.filas:
            clave = tuple(f[c] for c in columnas)
            grupos.setdefault(clave, []).append(f)
        return TablaAgrupada(self, columnas, grupos)

    @staticmethod
    def resumir(agrupada, especificaciones):
        """especificaciones: lista de (nombre_salida, funcion, columna | None)"""
        origen = agrupada.tabla
        salidas = [nombre for nombre, _, _ in especificaciones]
        for nombre, funcion, columna in especificaciones:
            if funcion not in AGREGACIONES:
                raise ErrorSemantico(f"funcion de agregacion desconocida: '{funcion}'")
            if columna is None and funcion != "contar":
                raise ErrorSemantico(f"operacion no permitida: '{funcion}' requiere una columna, "
                                    f"por ejemplo {funcion}(total)")
            if columna is not None:
                origen._exigir(columna)
            if nombre in agrupada.columnas:
                raise ErrorSemantico(f"el nombre '{nombre}' ya es una columna de agrupacion")
        if len(set(salidas)) != len(salidas):
            raise ErrorSemantico("operacion no permitida: nombres repetidos en resumir")

        filas = []
        for clave, filas_grupo in agrupada.grupos.items():
            nueva = dict(zip(agrupada.columnas, clave))
            for nombre, funcion, columna in especificaciones:
                if columna is None:                        # contar()
                    nueva[nombre] = len(filas_grupo)
                else:
                    nueva[nombre] = AGREGACIONES[funcion]([f[columna] for f in filas_grupo])
            filas.append(nueva)
        return Tabla(agrupada.columnas + salidas, filas)

    # ---- Presentacion -------------------------------------------
    def __len__(self):
        return len(self.filas)

    def vista_previa(self, n=5):
        if not self.columnas:
            return "(tabla vacia)"
        texto = lambda v: "" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))
        muestra = self.filas[:n]
        anchos = [max([len(c)] + [len(texto(f[c])) for f in muestra]) for c in self.columnas]
        linea = lambda celdas: " | ".join(c.ljust(a) for c, a in zip(celdas, anchos))
        salida = [linea(self.columnas), "-+-".join("-" * a for a in anchos)]
        salida += [linea([texto(f[c]) for c in self.columnas]) for f in muestra]
        if len(self.filas) > n:
            salida.append(f"... ({len(self.filas)} filas en total)")
        return "\n".join(salida)

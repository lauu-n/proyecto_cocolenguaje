"""Pruebas de extremo a extremo: programa .coco -> Evaluador -> resultado.
Requieren haber corrido `make generar` (necesitan el parser generado)."""
import pytest

from src.ejecutar import ejecutar


def correr(tmp_path, codigo):
    archivo = tmp_path / "programa.coco"
    archivo.write_text(codigo, encoding="utf-8")
    return ejecutar(str(archivo), mostrar=False)


def test_pipeline_completo_del_corte2(tmp_path):
    salida = tmp_path / "resumen.csv"
    ctx = correr(tmp_path, f'''
        ventas = cargar "datos/ventas.csv";
        r = ventas
            |> filtrar donde unidades > 0 && precio > 0
            |> crear total = unidades * precio
            |> agrupar por [ciudad]
            |> resumir ingreso = suma(total), registros = contar();
        guardar r como "{salida.as_posix()}";
    ''')
    assert ctx is not None
    assert ctx.obtener("r").columnas == ["ciudad", "ingreso", "registros"]
    assert salida.exists()


def test_variables_y_expresiones(tmp_path):
    ctx = correr(tmp_path, 'a1 = 2 + 3 * 4; b1 = (2 + 3) * 4; c1 = 2 ^ 3 ^ 2;')
    assert ctx.obtener("a1") == 14 and ctx.obtener("b1") == 20 and ctx.obtener("c1") == 512


def test_variable_en_filtro(tmp_path):
    ctx = correr(tmp_path, '''
        minimo_u = 5;
        v = cargar "datos/ventas.csv";
        f = v |> filtrar donde unidades >= minimo_u;
    ''')
    assert all(fila["unidades"] >= 5 for fila in ctx.obtener("f").filas)


@pytest.mark.parametrize("archivo, fragmento", [
    ("01_variable_no_declarada", "no ha sido declarada"),
    ("02_columna_inexistente", "no existe"),
    ("03_tipos_incompatibles", "tipos incompatibles"),
    ("04_operacion_no_permitida", "operacion no permitida"),
])
def test_errores_semanticos(archivo, fragmento, capsys):
    assert ejecutar(f"ejemplos/semanticos/{archivo}.coco", mostrar=False) is None
    salida = capsys.readouterr().out
    assert "ERROR SEMANTICO" in salida and fragmento in salida and "linea" in salida


def test_error_sintactico_no_ejecuta(tmp_path, capsys):
    assert correr(tmp_path, 'x1 = 5') is None
    assert "ERROR SINTACTICO" in capsys.readouterr().out


# ---------- Operaciones que antes no tenian cobertura ----------
CSV_CON_NULOS = "ciudad,unidades,precio\nBogota,3,100\nCali,,50\nBogota,2,\nCali,10,70\n"


def con_csv(tmp_path, programa):
    (tmp_path / "d.csv").write_text(CSV_CON_NULOS, encoding="utf-8")
    return correr(tmp_path, f'd = cargar "{(tmp_path / "d.csv").as_posix()}";\n' + programa)


def test_eliminar_nulos(tmp_path):
    ctx = con_csv(tmp_path, "r = d |> eliminar_nulos;")
    assert len(ctx.obtener("r")) == 2


def test_rellenar_nulos(tmp_path):
    ctx = con_csv(tmp_path, "r = d |> rellenar_nulos unidades con 0;")
    assert [f["unidades"] for f in ctx.obtener("r").filas] == [3, 0, 2, 10]


def test_ordenar_descendiente_y_ascendiente(tmp_path):
    ctx = con_csv(tmp_path, "mayor_a_menor = d |> ordenar por unidades descendiente; "
                            "menor_a_mayor = d |> ordenar por unidades ascendiente;")
    assert [f["unidades"] for f in ctx.obtener("mayor_a_menor").filas] == [10, 3, 2, None]
    assert [f["unidades"] for f in ctx.obtener("menor_a_mayor").filas] == [2, 3, 10, None]


@pytest.mark.parametrize("tipo, esperado", [
    ("decimal", 3.0), ("texto", "3"), ("entero", 3)])
def test_convertir_tipos(tmp_path, tipo, esperado):
    ctx = con_csv(tmp_path, f"r = d |> convertir unidades como {tipo};")
    valor = ctx.obtener("r").filas[0]["unidades"]
    assert valor == esperado and type(valor) is type(esperado)


def test_convertir_a_booleano_es_sintacticamente_valido(tmp_path):
    ctx = con_csv(tmp_path, 'r = d |> crear t = "verdadero" |> convertir t como booleano;')
    assert ctx.obtener("r").filas[0]["t"] is True


def test_renombrar_y_duplicados(tmp_path):
    ctx = con_csv(tmp_path, "r = d |> seleccionar [ciudad] |> eliminar_duplicados "
                            "|> renombrar ciudad como c;")
    assert ctx.obtener("r").columnas == ["c"] and len(ctx.obtener("r")) == 2


def test_resumir_con_las_siete_funciones(tmp_path):
    ctx = con_csv(tmp_path, """
        r = d |> agrupar por [ciudad]
              |> resumir s = suma(precio), m = media(precio), md = mediana(precio),
                         mn = minimo(precio), mx = maximo(precio),
                         sd = desviacion_estandar(precio), n = contar();""")
    assert ctx.obtener("r").columnas == ["ciudad", "s", "m", "md", "mn", "mx", "sd", "n"]


# ---------- Programas completos del Corte 2 (>= 3) ----------
import csv
import statistics
from pathlib import Path


@pytest.mark.parametrize("programa, salidas", [
    ("04_pipeline_corte2", ["resumen_ciudades.csv"]),
    ("05_ventas_por_ciudad", ["ventas_por_ciudad.csv"]),
    ("06_limpieza_y_estadisticas", ["ventas_limpias.csv", "estadisticas_ventas.csv"]),
    ("07_ranking_categoria_ciudad", ["ingreso_categoria_ciudad.csv"]),
])
def test_programas_completos_exportan_csv(programa, salidas):
    for nombre in salidas:
        Path("salidas", nombre).unlink(missing_ok=True)
    assert ejecutar(f"ejemplos/validos/{programa}.coco", mostrar=False) is not None
    for nombre in salidas:
        contenido = Path("salidas", nombre).read_text(encoding="utf-8").strip().splitlines()
        assert len(contenido) >= 2, f"{nombre} no tiene datos"


def test_limpieza_y_estadisticas_coinciden_con_statistics():
    """Verifica los calculos del DSL contra la libreria estandar de Python."""
    ctx = ejecutar("ejemplos/validos/06_limpieza_y_estadisticas.coco", mostrar=False)
    limpias = ctx.obtener("limpias")
    totales = [f["total"] for f in limpias.filas]
    est = ctx.obtener("estadisticas").filas[0]
    assert len(limpias) == 11                       # 14 filas - 2 duplicados - 1 precio nulo
    assert est["filas"] == len(totales)
    assert est["ventas_totales"] == sum(totales)
    assert est["promedio"] == pytest.approx(statistics.mean(totales))
    assert est["mediana_total"] == pytest.approx(statistics.median(totales))
    assert est["desviacion"] == pytest.approx(statistics.pstdev(totales))
    assert est["minimo_total"] == min(totales) and est["maximo_total"] == max(totales)


def test_resumir_sin_agrupar_sobre_tabla_vacia(tmp_path):
    ctx = correr(tmp_path, '''
        v = cargar "datos/ventas.csv";
        r = v |> filtrar donde unidades > 9999 |> resumir n = contar(), m = media(precio);''')
    fila = ctx.obtener("r").filas[0]
    assert fila["n"] == 0 and fila["m"] is None


def test_agrupar_dos_columnas(tmp_path):
    ctx = correr(tmp_path, '''
        v = cargar "datos/ventas.csv";
        r = v |> agrupar por [categoria, ciudad] |> resumir n = contar();''')
    assert ctx.obtener("r").columnas == ["categoria", "ciudad", "n"]


def test_convertir_como_tipo_y_a_ya_no_es_reservada(tmp_path):
    ctx = correr(tmp_path, 'a = 5; b = a * 2;')            # 'a' ahora es un nombre valido
    assert ctx.obtener("b") == 10

import pytest

from src.errores import ErrorSemantico
from src.tabla import Tabla


@pytest.fixture
def ventas():
    return Tabla(["ciudad", "unidades", "precio"], [
        {"ciudad": "Bogota", "unidades": 3, "precio": 100},
        {"ciudad": "Cali", "unidades": 10, "precio": 50},
        {"ciudad": "Bogota", "unidades": 2, "precio": 300},
        {"ciudad": "Cali", "unidades": None, "precio": 70},
    ])


def test_desde_csv_infiere_tipos():
    t = Tabla.desde_csv("datos/ventas.csv")
    assert isinstance(t.filas[0]["unidades"], int)
    assert isinstance(t.filas[0]["ciudad"], str)


def test_seleccionar(ventas):
    assert ventas.seleccionar(["ciudad"]).columnas == ["ciudad"]


def test_seleccionar_columna_inexistente(ventas):
    with pytest.raises(ErrorSemantico, match="no existe"):
        ventas.seleccionar(["ingreso"])


def test_filtrar_no_modifica_original(ventas):
    nueva = ventas.filtrar(lambda f: f["ciudad"] == "Cali")
    assert len(nueva) == 2 and len(ventas) == 4


def test_ordenar_numerico_y_nulos_al_final(ventas):
    t = ventas.ordenar("unidades")
    assert [f["unidades"] for f in t.filas] == [2, 3, 10, None]


def test_renombrar(ventas):
    t = ventas.renombrar("precio", "valor")
    assert "valor" in t.columnas and "precio" not in t.columnas


def test_eliminar_nulos(ventas):
    assert len(ventas.eliminar_nulos()) == 3


def test_rellenar_nulos(ventas):
    assert ventas.rellenar_nulos("unidades", 0).filas[3]["unidades"] == 0


def test_convertir_tipo_invalido(ventas):
    with pytest.raises(ErrorSemantico, match="tipos incompatibles"):
        ventas.convertir_tipo("ciudad", "entero")


def test_agrupar_y_resumir(ventas):
    r = Tabla.resumir(ventas.agrupar(["ciudad"]), [
        ("total", "suma", "precio"), ("n", "contar", None),
        ("prom", "media", "precio"), ("med", "mediana", "precio"),
        ("mn", "minimo", "precio"), ("mx", "maximo", "precio"),
        ("sd", "desviacion_estandar", "precio")])
    bogota = r.filas[0]
    assert bogota["total"] == 400 and bogota["n"] == 2 and bogota["prom"] == 200
    assert bogota["med"] == 200 and bogota["mn"] == 100 and bogota["mx"] == 300
    assert bogota["sd"] == pytest.approx(100.0)


def test_suma_de_texto_falla(ventas):
    with pytest.raises(ErrorSemantico, match="tipos incompatibles"):
        Tabla.resumir(ventas.agrupar(["ciudad"]), [("x", "suma", "ciudad")])


def test_guardar_csv_sin_filas_conserva_encabezado(ventas, tmp_path):
    ruta = tmp_path / "vacio.csv"
    ventas.filtrar(lambda f: False).guardar_csv(str(ruta))
    assert ruta.read_text().strip() == "ciudad,unidades,precio"


# ---------- Datos reales: separadores y nombres de columna ----------
from src.tabla import RESERVADAS, normalizar_nombre


def test_normalizar_nombres():
    assert normalizar_nombre("Valor Total ($)") == "valor_total"
    assert normalizar_nombre("Categoría") == "categoria"
    assert normalizar_nombre("2024 Ventas") == "c_2024_ventas"
    assert normalizar_nombre("texto") == "texto_col"                 # palabra reservada
    assert normalizar_nombre("Precio", usados=["precio"]) == "precio_2"


def test_csv_con_punto_y_coma_bom_y_lineas_vacias(tmp_path):
    ruta = tmp_path / "excel.csv"
    ruta.write_bytes("\ufeffCiudad;Valor Total\nBogotá;10\n\nCali;20\n".encode("utf-8"))
    t = Tabla.desde_csv(str(ruta))
    assert t.columnas == ["ciudad", "valor_total"]
    assert [f["valor_total"] for f in t.filas] == [10, 20]


def test_reservadas_sincronizadas_con_la_gramatica():
    import re
    texto = open("grammar/Cocosette.g4", encoding="utf-8").read()
    palabras = set()
    for linea in texto.splitlines():
        if re.match(r"^[A-Z_]+\s*:", linea):
            palabras |= set(re.findall(r"'([a-z_]+)'", linea))
    assert palabras == RESERVADAS

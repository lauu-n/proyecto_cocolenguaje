#!/usr/bin/env python3
# ================================================================
# validar.py — DSL Cocosette (Corte 1)
# ================================================================
# Este script sirve para revisar si un archivo .coco esta bien
# escrito.
#
# No ejecuta el programa del DSL. Eso viene despues, en el Corte 2,
# cuando exista el Visitor.
#
# Lo unico que hace aqui es:
# 1. Leer el archivo .coco
# 2. Convertirlo en tokens (lexer)
# 3. Revisar el orden de los tokens (parser)
# 4. Avisar si hay errores, con linea y columna
#
# Como usarlo:
#   python3 src/validar.py ejemplos/validos/*.coco
#   python3 src/validar.py ejemplos/invalidos/*.coco
#   python3 src/validar.py ruta/a/un/archivo.coco
#
# Antes de correrlo hay que generar el lexer y el parser, con:
#   make generar
# (esto ejecuta: cd grammar && antlr4 -Dlanguage=Python3 -visitor -o ../src/parser Cocosette.g4)
#
# Tambien hay que tener instalado antlr4-python3-runtime
# (ver requirements.txt).

import sys
from pathlib import Path

# ================================================================
# IMPORTACIONES
# ================================================================
# Aqui traemos el codigo que ya existe y que no escribimos nosotros.
#
# IMPORTANTE — por que estas importaciones SI estan permitidas:
#
# En este proyecto se nos pidio no usar librerias de ciencia de datos
# como pandas, NumPy o Matplotlib. La idea es que nosotros mismos
# construyamos, desde cero, la parte de datos, filtros, agregaciones
# y graficas (eso es el Corte 2 y el Corte 3).
#
# Pero eso NO aplica a ANTLR4. ANTLR4 no es una libreria de ciencia
# de datos: es la herramienta obligatoria del curso para construir el
# lexer y el parser (esta pedida en el enunciado del proyecto, no es
# una libreria de apoyo opcional). Usar `antlr4-python3-runtime` no es
# lo mismo que usar pandas: no nos resuelve el problema del dominio
# (ventas, filtros, graficas), solo nos da la maquinaria generica de
# tokenizar y reconocer gramaticas, que de todas formas ANTLR4 nos
# obliga a usar para generar el lexer y el parser. Reimplementar
# ANTLR4 desde cero seria reimplementar el curso completo, no el DSL.
#
# Por eso: SI se puede importar antlr4 aqui. NO se puede importar
# pandas, NumPy o Matplotlib mas adelante en el proyecto.
from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

# ----------------------------------------------------------------
# DE DONDE HEREDA CADA COSA (para la sustentacion)
# ----------------------------------------------------------------
# Este proyecto usa dos "capas" de codigo. Es importante no
# confundirlas cuando pregunten de donde hereda una clase:
#
# CAPA 1: el runtime de antlr4 (paquete antlr4-python3-runtime,
# instalado con pip, viene en requirements.txt). Esto es codigo de
# terceros, escrito por el proyecto ANTLR, NO por nosotros. Aqui
# viven las clases BASE genericas que sirven para CUALQUIER gramatica,
# no solo la nuestra:
#   - FileStream          -> lee un archivo de texto
#   - CommonTokenStream   -> guarda y entrega tokens al parser
#   - Lexer               -> algoritmo generico de tokenizacion
#   - Parser              -> algoritmo generico de reconocimiento
#   - ErrorListener       -> clase base para reaccionar a errores
#
# CAPA 2: el codigo generado por ANTLR a partir de nuestro archivo
# grammar/Cocosette.g4 (carpeta src/parser/, ver mas abajo). Estas
# clases SI son especificas de Cocosette, pero nosotros NO las
# escribimos a mano, las genera el comando `antlr4`. Por eso tampoco
# estan guardadas en el repositorio (ver .gitignore): se recrean cada
# vez que se corre `make generar`.
#
# La relacion de herencia entre las dos capas es:
#
#   class CocosetteLexer(Lexer):            # Lexer viene de la capa 1
#   class CocosetteParser(Parser):          # Parser viene de la capa 1
#
# En palabras simples: `Lexer` y `Parser` (capa 1) ya saben COMO
# tokenizar y reconocer en general (el algoritmo de automatas esta
# ahi). `CocosetteLexer` y `CocosetteParser` (capa 2) heredan ese
# comportamiento y solo le agregan la tabla de reglas CONCRETAS de
# nuestro lenguaje (COCOCARGAR, ID, STRING, la regla `programa`,
# etc.), que ANTLR saca directamente de grammar/Cocosette.g4. Osea:
# `CocosetteLexer` no reimplementa la tokenizacion desde cero, la
# hereda de `Lexer` y solo aporta el "que" (las reglas de Cocosette),
# no el "como" (el algoritmo de reconocimiento).
#
# Esta es tambien la razon por la que antlr4 SI se puede importar
# aqui, aunque el proyecto prohiba usar librerias como pandas, NumPy
# o Matplotlib: esa prohibicion es para no depender de librerias que
# ya resuelvan el DOMINIO del proyecto (datos, filtros, graficas), y
# antlr4 no resuelve nada de eso. Ademas, el enunciado del curso pide
# ANTLR4 como herramienta obligatoria para el lexer/parser (no es una
# libreria de apoyo opcional como pandas). Reimplementar `Lexer` y
# `Parser` desde cero seria ANTLR4 completo, no el DSL.
#
# Como CocosetteLexer y CocosetteParser no estan en el repositorio,
# primero hay que decirle a Python donde buscarlos una vez generados.
sys.path.append(str(Path(__file__).resolve().parent / "parser"))

try:
    # Si estos dos imports fallan, es porque todavia no se corrio
    # `make generar` y los archivos CocosetteLexer.py /
    # CocosetteParser.py todavia no existen en el disco.
    from CocosetteLexer import CocosetteLexer
    from CocosetteParser import CocosetteParser
except ImportError:
    print("No se encontro el lexer/parser generado por ANTLR.")
    print("Ejecuta primero:")
    print("  make generar")
    print("  (equivale a: cd grammar && antlr4 -Dlanguage=Python3 -visitor -o ../src/parser Cocosette.g4)")
    sys.exit(1)


# ================================================================
# CLASE: ColectorDeErrores
# ================================================================
# Esta clase sirve para guardar los errores que encuentre el lexer
# o el parser.
#
# DE DONDE HEREDA Y POR QUE (para la sustentacion):
#
# ColectorDeErrores(ErrorListener) hereda de
# `antlr4.error.ErrorListener.ErrorListener`, que es de la capa 1
# (viene del runtime de antlr4, no la escribimos nosotros).
#
# `ErrorListener` define un "contrato": cualquier clase que herede de
# ella puede sobreescribir el metodo `syntaxError`, y ANTLR se encarga
# de LLAMAR ese metodo automaticamente cada vez que el lexer o el
# parser encuentran algo que no reconocen (esto se llama "hook": nosotros
# no llamamos syntaxError nunca a mano, ANTLR lo invoca solo).
#
# Por defecto (si no hicieramos esta clase), tanto CocosetteLexer
# como CocosetteParser usan un `ConsoleErrorListener` (tambien de la
# capa 1) que simplemente imprime el error por consola y sigue de
# largo, sin guardar nada.
#
# Aqui usamos HERENCIA + OVERRIDE (sobreescritura): creamos una
# subclase propia que hereda toda la estructura de `ErrorListener`
# pero reemplaza el metodo `syntaxError` por nuestra propia version,
# que en vez de imprimir directo guarda el mensaje (con linea y
# columna) en una lista (`self.errores`). Esto nos permite decidir
# nosotros mismos, mas abajo en `validar_archivo`, que hacer con esos
# errores (mostrarlos todos juntos y marcar el archivo como invalido).
#
# Se crea UNA instancia distinta de ColectorDeErrores para el lexer y
# otra para el parser (ver validar_archivo), porque cada uno puede
# fallar por razones distintas: el lexer falla si encuentra un
# caracter que ninguna regla lexica reconoce (error LEXICO); el parser
# falla si los tokens estan en un orden que ninguna regla del parser
# permite (error SINTACTICO).
class ColectorDeErrores(ErrorListener):

    def __init__(self):
        super().__init__()
        self.errores = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errores.append(f"  linea {line}, columna {column}: {msg}")


# ================================================================
# FUNCION: validar_archivo
# ================================================================
# Esta funcion revisa un solo archivo .coco.
#
# Pasos:
# 1. Leer el archivo
# 2. Convertirlo en tokens
# 3. Revisar el orden de los tokens
# 4. Mostrar si es valido o invalido
def validar_archivo(ruta: str) -> bool:

    # Paso 1: leer el archivo como texto.
    entrada = FileStream(ruta, encoding="utf-8")

    # Paso 2: el lexer recorre el texto letra por letra y lo separa
    # en tokens (COCOCARGAR, ID, STRING, INT, etc.), segun las reglas
    # escritas en grammar/Cocosette.g4.
    lexer = CocosetteLexer(entrada)
    errores_lexicos = ColectorDeErrores()
    lexer.removeErrorListeners()
    lexer.addErrorListener(errores_lexicos)

    # Paso 3: el CommonTokenStream guarda los tokens y se los va
    # entregando al parser de a uno.
    tokens = CommonTokenStream(lexer)

    # Paso 4: el parser revisa si los tokens vienen en un orden
    # valido, segun las reglas del .g4 (programa, sentencia,
    # expresion, etc.).
    parser = CocosetteParser(tokens)
    errores_sintacticos = ColectorDeErrores()
    parser.removeErrorListeners()
    parser.addErrorListener(errores_sintacticos)

    # programa() es el metodo generado a partir de la regla raiz
    # "programa" del .g4. Devuelve el arbol de analisis sintactico
    # completo.
    arbol = parser.programa()

    # Si hubo errores lexicos o sintacticos, se muestran y se marca
    # el archivo como invalido.
    errores = errores_lexicos.errores + errores_sintacticos.errores
    if errores:
        print(f"[INVALIDO] {ruta}")
        for err in errores:
            print(err)
        return False

    # Si no hubo errores, se muestra un resumen corto del arbol
    # (solo para verlo rapido en la consola).
    resumen_arbol = arbol.toStringTree(recog=parser)
    if len(resumen_arbol) > 90:
        resumen_arbol = resumen_arbol[:90] + " ..."
    print(f"[VALIDO]   {ruta}")
    print(f"           arbol: {resumen_arbol}")
    return True


# ================================================================
# FUNCION: main
# ================================================================
# Esta funcion recibe los archivos por linea de comandos y los
# valida uno por uno.
def main():
    if len(sys.argv) < 2:
        print("Uso: python3 src/validar.py <archivo1.coco> [archivo2.coco ...]")
        sys.exit(1)

    resultados = [validar_archivo(ruta) for ruta in sys.argv[1:]]
    total = len(resultados)
    validos = sum(resultados)
    print(f"\n{validos}/{total} archivo(s) sintacticamente validos")


if __name__ == "__main__":
    main()

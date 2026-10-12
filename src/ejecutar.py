#!/usr/bin/env python3
"""
ejecutar.py - Ejecuta un programa Cocosette (.coco)

Flujo completo del Corte 1 + Corte 2:
    archivo .coco -> lexer -> parser -> arbol -> Evaluador (Visitor) -> resultados

Uso (desde la raiz del repositorio):
    python3 -m src.ejecutar ejemplos/validos/04_pipeline_corte2.coco
"""
import sys

from antlr4 import FileStream, CommonTokenStream

from src.errores import ColectorDeErrores, ErrorSemantico
from src.evaluador import EvaluadorCocosette
from src.parser.CocosetteLexer import CocosetteLexer
from src.parser.CocosetteParser import CocosetteParser
from src.tabla import Tabla


def ejecutar(ruta, mostrar=True):
    """Devuelve el Contexto final, o None si hubo errores."""
    lexer = CocosetteLexer(FileStream(ruta, encoding="utf-8"))
    errores_lexicos = ColectorDeErrores()
    lexer.removeErrorListeners()
    lexer.addErrorListener(errores_lexicos)

    parser = CocosetteParser(CommonTokenStream(lexer))
    errores_sintacticos = ColectorDeErrores()
    parser.removeErrorListeners()
    parser.addErrorListener(errores_sintacticos)

    arbol = parser.programa()

    errores = errores_lexicos.errores + errores_sintacticos.errores
    if errores:
        print(f"[ERROR SINTACTICO] {ruta}")
        print("\n".join(errores))
        return None

    evaluador = EvaluadorCocosette()
    try:
        evaluador.visit(arbol)
    except ErrorSemantico as e:
        print(f"[ERROR SEMANTICO] {ruta}")
        print(f"  {e}")
        return None

    print(f"[OK] {ruta}")
    if mostrar:
        for nombre, valor in evaluador.contexto.items():
            if isinstance(valor, Tabla):
                print(f"\n{nombre}  ({len(valor)} filas)")
                print(valor.vista_previa())
            else:
                print(f"\n{nombre} = {valor}")
    return evaluador.contexto


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 -m src.ejecutar <archivo.coco>")
        sys.exit(1)
    sys.exit(0 if ejecutar(sys.argv[1]) is not None else 1)


if __name__ == "__main__":
    main()

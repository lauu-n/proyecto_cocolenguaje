"""
Errores propios del DSL Cocosette.

- ErrorSemantico: lo lanzan Tabla, Contexto y el Evaluador cuando el
programa es sintacticamente valido pero no tiene sentido (variable no
declarada, columna inexistente, tipos incompatibles, operacion no
permitida).
- ColectorDeErrores: igual al de validar.py, reutilizable para ejecutar.py.
"""
from antlr4.error.ErrorListener import ErrorListener


class ErrorSemantico(Exception):
    def __init__(self, mensaje, linea=None, columna=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna

    def asignar_posicion(self, linea, columna):
        self.linea = linea
        self.columna = columna

    def __str__(self):
        if self.linea is not None:
            return f"Error semantico (linea {self.linea}, columna {self.columna}): {self.mensaje}"
        return f"Error semantico: {self.mensaje}"


class ColectorDeErrores(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errores = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errores.append(f"  linea {line}, columna {column}: {msg}")

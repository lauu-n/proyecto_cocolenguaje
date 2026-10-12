"""
Contexto de ejecucion = tabla de simbolos del DSL Cocosette.

Asocia cada identificador (nombre de variable) con el objeto que
representa: una Tabla, una TablaAgrupada o un valor simple (numero,
texto, booleano).

El Evaluador (Visitor) consulta aqui cada vez que encuentra un ID que
no es una columna de la fila que esta procesando.
"""
from src.errores import ErrorSemantico


class Contexto:
    def __init__(self):
        self._simbolos = {}

    def declarar(self, nombre, valor):
        """Crea la variable, o la reemplaza si ya existia."""
        self._simbolos[nombre] = valor

    def existe(self, nombre):
        return nombre in self._simbolos

    def obtener(self, nombre):
        if nombre not in self._simbolos:
            raise ErrorSemantico(f"la variable '{nombre}' no ha sido declarada")
        return self._simbolos[nombre]

    def items(self):
        return self._simbolos.items()

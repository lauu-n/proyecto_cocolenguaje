"""
Evaluador del DSL Cocosette (Corte 2): patron Visitor.

CocosetteVisitor (generado por ANTLR) trae un metodo visitX por cada
regla/etiqueta de grammar/Cocosette.g4, que por defecto solo recorre
los hijos. Aqui los sobreescribimos para EJECUTAR cada nodo:

    arbol sintactico --visit--> operaciones sobre Tabla + Contexto

Idea clave para filtrar/crear: las expresiones se evaluan FILA POR FILA.
Mientras se procesa una fila, `self._fila` apunta a ella y un
identificador se busca primero entre las columnas de esa fila y despues
en el Contexto (variables).
"""
from src.parser.CocosetteVisitor import CocosetteVisitor

from src.contexto import Contexto
from src.errores import ErrorSemantico
from src.tabla import Tabla, TablaAgrupada, es_numero, nombre_tipo


class EvaluadorCocosette(CocosetteVisitor):

    def __init__(self):
        super().__init__()
        self.contexto = Contexto()
        self._fila = None        # fila que se esta evaluando (None = fuera de una fila)
        self._actual = None      # resultado intermedio del pipeline en curso

    # ============================================================
    # Utilidades
    # ============================================================
    def _error(self, ctx, mensaje):
        return ErrorSemantico(mensaje, ctx.start.line, ctx.start.column)

    def _ejecutar(self, ctx, funcion, *args):
        """Llama funcion(*args); si lanza un ErrorSemantico sin posicion,
        le agrega la linea/columna del nodo que se estaba visitando."""
        try:
            return funcion(*args)
        except ErrorSemantico as e:
            if e.linea is None:
                e.asignar_posicion(ctx.start.line, ctx.start.column)
            raise

    @staticmethod
    def _texto(token):
        """Quita las comillas de un STRING y resuelve \\"."""
        return token.getText()[1:-1].replace('\\"', '"')

    def _tabla_actual(self, ctx, operacion):
        if isinstance(self._actual, TablaAgrupada):
            raise self._error(ctx, f"operacion no permitida: '{operacion}' no puede ir "
                                   f"despues de 'agrupar'; use 'resumir' primero")
        return self._actual

    # ============================================================
    # Programa y sentencias
    # ============================================================
    def visitPrograma(self, ctx):
        for sentencia in ctx.sentencia():
            self.visit(sentencia)

    def visitSentencia(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitAsignacion(self, ctx):
        nombre = ctx.ID().getText()
        valor = self.visit(ctx.cocoFuente())
        self.contexto.declarar(nombre, valor)

    # ---- Fuentes de datos ---------------------------------------
    def visitFuenteCarga(self, ctx):
        return self.visit(ctx.cargaCSV())

    def visitFuenteExpresion(self, ctx):
        return self.visit(ctx.expresion())

    def visitCargaCSV(self, ctx):
        ruta = self._texto(ctx.STRING())
        try:
            return Tabla.desde_csv(ruta)
        except FileNotFoundError:
            raise self._error(ctx, f"no se encontro el archivo '{ruta}'")

    def visitFuentePipeline(self, ctx):
        nombre = ctx.ID().getText()
        base = self._ejecutar(ctx, self.contexto.obtener, nombre)
        if not isinstance(base, Tabla):
            raise self._error(ctx, f"'{nombre}' es {nombre_tipo(base)}, no una tabla; "
                                   f"solo las tablas admiten '|>'")
        self._actual = base
        for operacion in ctx.operacion():
            self._actual = self.visit(operacion)
        resultado, self._actual = self._actual, None
        if isinstance(resultado, TablaAgrupada):
            raise self._error(ctx, "operacion no permitida: 'agrupar' debe ir seguido de 'resumir'")
        return resultado

    def visitOperacion(self, ctx):
        return self.visit(ctx.getChild(0))

    # ---- Guardar CSV --------------------------------------------
    def visitCocoGuardarCSV(self, ctx):
        nombre = ctx.ID().getText()
        valor = self._ejecutar(ctx, self.contexto.obtener, nombre)
        if not isinstance(valor, Tabla):
            raise self._error(ctx, f"no se puede guardar '{nombre}': es {nombre_tipo(valor)}, "
                                   f"no una tabla")
        valor.guardar_csv(self._texto(ctx.STRING()))

    # ---- Graficar -----------------------------------------------
    def visitCocoGraficar(self, ctx):
        # Corte 3: aqui se generara la grafica. En el Corte 2 solo se reconoce.
        return None

    # ============================================================
    # Operaciones de pipeline
    # ============================================================
    def visitListaCocolumnas(self, ctx):
        return [i.getText() for i in ctx.ID()]

    def visitCocoSeleccion(self, ctx):
        tabla = self._tabla_actual(ctx, "seleccionar")
        return self._ejecutar(ctx, tabla.seleccionar, self.visit(ctx.listaCocolumnas()))

    def visitCocoFiltro(self, ctx):
        tabla = self._tabla_actual(ctx, "filtrar")

        def predicado(fila):
            resultado = self._evaluar_en_fila(fila, ctx.cocondicion())
            if resultado is not None and not isinstance(resultado, bool):
                raise self._error(ctx, f"la condicion de 'filtrar' debe ser verdadera o falsa, "
                                       f"pero produjo {nombre_tipo(resultado)}")
            return resultado is True          # nulo -> la fila no pasa el filtro

        return self._ejecutar(ctx, tabla.filtrar, predicado)

    def visitCocondicion(self, ctx):
        return self.visit(ctx.expresion())

    def visitCocoCrear(self, ctx):
        tabla = self._tabla_actual(ctx, "crear")
        nombre = ctx.ID().getText()
        return self._ejecutar(ctx, tabla.crear_columna, nombre,
                              lambda fila: self._evaluar_en_fila(fila, ctx.expresion()))

    def visitCocoOrdenar(self, ctx):
        tabla = self._tabla_actual(ctx, "ordenar")
        return self._ejecutar(ctx, tabla.ordenar, ctx.ID().getText(),
                              ctx.COCOORDENARDESC() is not None)

    def visitCocoRenombrar(self, ctx):
        tabla = self._tabla_actual(ctx, "renombrar")
        return self._ejecutar(ctx, tabla.renombrar, ctx.ID(0).getText(), ctx.ID(1).getText())

    def visitCocoEliminarDuplicados(self, ctx):
        return self._tabla_actual(ctx, "eliminar_duplicados").eliminar_duplicados()

    def visitCocoNulos(self, ctx):
        tabla = self._tabla_actual(ctx, "tratamiento de nulos")
        if ctx.COCOELIMINARNULL() is not None:
            return tabla.eliminar_nulos()
        valor = self._evaluar_en_fila(None, ctx.expresion())
        return self._ejecutar(ctx, tabla.rellenar_nulos, ctx.ID().getText(), valor)

    def visitCocoConvertir(self, ctx):
        tabla = self._tabla_actual(ctx, "convertir")
        return self._ejecutar(ctx, tabla.convertir_tipo, ctx.ID().getText(),
                              ctx.tipoDato().getText())

    def visitCocoAgrupar(self, ctx):
        tabla = self._tabla_actual(ctx, "agrupar")
        return self._ejecutar(ctx, tabla.agrupar, self.visit(ctx.listaCocolumnas()))

    def visitAsignacionAgregada(self, ctx):
        ids = ctx.ID()                       # [nombre_salida] o [nombre_salida, columna]
        columna = ids[1].getText() if len(ids) > 1 else None
        return (ids[0].getText(), ctx.funcionAgregacion().getText(), columna)

    def visitCocoResumir(self, ctx):
        especificaciones = [self.visit(a) for a in ctx.asignacionAgregada()]
        entrada = self._actual
        if not isinstance(entrada, TablaAgrupada):
            # Sin 'agrupar': estadisticas descriptivas de TODA la tabla (un solo grupo,
            # incluso si no hay filas: contar() da 0 y las demas funciones dan nulo).
            entrada = TablaAgrupada(entrada, [], {(): list(entrada.filas)})
        return self._ejecutar(ctx, Tabla.resumir, entrada, especificaciones)

    # ============================================================
    # Expresiones
    # ============================================================
    def _evaluar_en_fila(self, fila, nodo_expresion):
        anterior, self._fila = self._fila, fila
        try:
            return self.visit(nodo_expresion)
        finally:
            self._fila = anterior

    def _numero(self, ctx, valor, operador):
        if valor is not None and not es_numero(valor):
            raise self._error(ctx, f"tipos incompatibles: '{operador}' requiere numeros, "
                                   f"pero recibio {nombre_tipo(valor)} ('{valor}')")
        return valor

    def _booleano(self, ctx, valor, operador):
        if valor is not None and not isinstance(valor, bool):
            raise self._error(ctx, f"tipos incompatibles: '{operador}' requiere valores "
                                   f"verdadero/falso, pero recibio {nombre_tipo(valor)}")
        return valor

    def visitExpParentesis(self, ctx):
        return self.visit(ctx.expresion())

    def visitExpLiteral(self, ctx):
        return self.visit(ctx.literal())

    def visitLiteral(self, ctx):
        if ctx.INT() is not None:
            return int(ctx.INT().getText())
        if ctx.FLOAT() is not None:
            return float(ctx.FLOAT().getText())
        if ctx.STRING() is not None:
            return self._texto(ctx.STRING())
        return ctx.COCOBOOLEANO().getText() == "verdadero"

    def visitExpIdentificador(self, ctx):
        nombre = ctx.ID().getText()
        if self._fila is not None and nombre in self._fila:     # 1) columna de la fila actual
            return self._fila[nombre]
        if self.contexto.existe(nombre):                        # 2) variable
            return self.contexto.obtener(nombre)
        if self._fila is not None:
            raise self._error(ctx, f"'{nombre}' no es una columna de la tabla ni una variable "
                                   f"declarada (columnas: {', '.join(self._fila.keys())})")
        raise self._error(ctx, f"la variable '{nombre}' no ha sido declarada")

    def visitExpUnaria(self, ctx):
        operador = ctx.op.text
        valor = self.visit(ctx.expresion())
        if operador == "-":
            valor = self._numero(ctx, valor, "-")
            return None if valor is None else -valor
        valor = self._booleano(ctx, valor, "!")
        return None if valor is None else (not valor)

    def visitExpPotencia(self, ctx):
        base = self._numero(ctx, self.visit(ctx.expresion(0)), "^")
        exponente = self._numero(ctx, self.visit(ctx.expresion(1)), "^")
        if base is None or exponente is None:
            return None
        try:
            return base ** exponente
        except (ZeroDivisionError, OverflowError):
            raise self._error(ctx, "operacion invalida en '^' (division por cero o desborde)")

    def visitExpMultiplicativa(self, ctx):
        operador = ctx.op.text
        izq = self._numero(ctx, self.visit(ctx.expresion(0)), operador)
        der = self._numero(ctx, self.visit(ctx.expresion(1)), operador)
        if izq is None or der is None:
            return None
        if operador == "*":
            return izq * der
        if der == 0:
            raise self._error(ctx, f"division por cero en '{operador}'")
        return izq / der if operador == "/" else izq % der

    def visitExpAditiva(self, ctx):
        operador = ctx.op.text
        izq = self.visit(ctx.expresion(0))
        der = self.visit(ctx.expresion(1))
        if izq is None or der is None:
            return None
        if operador == "+" and isinstance(izq, str) and isinstance(der, str):
            return izq + der                                    # concatenacion de textos
        izq = self._numero(ctx, izq, operador)
        der = self._numero(ctx, der, operador)
        return izq + der if operador == "+" else izq - der

    def visitExpRelacional(self, ctx):
        operador = ctx.op.text
        izq = self.visit(ctx.expresion(0))
        der = self.visit(ctx.expresion(1))
        if izq is None or der is None:
            return False                                        # comparar con nulo -> falso
        ambos_numeros = es_numero(izq) and es_numero(der)
        ambos_textos = isinstance(izq, str) and isinstance(der, str)
        if not (ambos_numeros or ambos_textos):
            raise self._error(ctx, f"tipos incompatibles: no se puede comparar {nombre_tipo(izq)} "
                                   f"con {nombre_tipo(der)} usando '{operador}'")
        return {"<": izq < der, "<=": izq <= der, ">": izq > der, ">=": izq >= der}[operador]

    def visitExpIgualdad(self, ctx):
        izq = self.visit(ctx.expresion(0))
        der = self.visit(ctx.expresion(1))
        if es_numero(izq) != es_numero(der) and izq is not None and der is not None:
            raise self._error(ctx, f"tipos incompatibles: no se puede comparar {nombre_tipo(izq)} "
                                   f"con {nombre_tipo(der)} usando '{ctx.op.text}'")
        iguales = izq == der
        return iguales if ctx.op.text == "==" else not iguales

    def visitExpAnd(self, ctx):
        izq = self._booleano(ctx, self.visit(ctx.expresion(0)), "&&")
        if izq is False:
            return False
        der = self._booleano(ctx, self.visit(ctx.expresion(1)), "&&")
        return False if der is False else (None if izq is None or der is None else True)

    def visitExpOr(self, ctx):
        izq = self._booleano(ctx, self.visit(ctx.expresion(0)), "||")
        if izq is True:
            return True
        der = self._booleano(ctx, self.visit(ctx.expresion(1)), "||")
        return True if der is True else (None if izq is None or der is None else False)

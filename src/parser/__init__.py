# Esta carpeta recibe el codigo generado por ANTLR4 a partir de
# grammar/Cocosette.g4 (CocosetteLexer.py, CocosetteParser.py,
# CocosetteVisitor.py, CocosetteListener.py, y los archivos
# .tokens / .interp).
#
# Generalo con:
#   make generar
# (equivale a: cd grammar && antlr4 -Dlanguage=Python3 -visitor -o ../src/parser Cocosette.g4)
#
# Estos archivos no se incluyen en el repositorio (ver .gitignore)
# porque se regeneran automaticamente a partir de la gramatica.
#
# CocosetteLexer hereda de Lexer, y CocosetteParser hereda de
# Parser (ambas clases base vienen de antlr4-python3-runtime, no de
# este proyecto). Ver ../../docs/conceptos_antlr.md para el detalle
# de que hereda de que y como se relacionan estos archivos generados
# con grammar/Cocosette.g4 y con src/validar.py.

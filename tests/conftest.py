import os
import sys

# Permite `import src...` al correr pytest desde cualquier carpeta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

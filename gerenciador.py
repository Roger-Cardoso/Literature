"""Inicia o Literature Studio a partir de qualquer diretório."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from gerenciador_visual import main
if __name__=='__main__':main()

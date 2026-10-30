"""Validação do pacote público no GitHub Actions."""
from pathlib import Path
import sys
from pacote_publicacao import verificar
if __name__=='__main__':
 try:
  meta=verificar(Path(sys.argv[1] if len(sys.argv)>1 else 'publicado'))
  print(f"Publicação conferida: {len(meta['arquivos'])} arquivos públicos.")
 except (ValueError,OSError) as e:raise SystemExit('Publicação recusada: '+str(e))

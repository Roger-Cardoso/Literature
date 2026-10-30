"""Entrada compatível: gera a saída pública sem alterar fontes editoriais."""
from scripts.gerar_site import gerar
if __name__ == '__main__':
    gerar()
    print('Site gerado em site/.')

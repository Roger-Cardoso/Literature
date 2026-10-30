"""Configuração pela mesma janela, em cópia temporária sem acesso ao Disqus."""
import json,shutil,sys,tempfile
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
from gestao_projeto import Projeto
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(ROOT,destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.git','.agents','.aws','.codex','.literature-backups','.literature-lixeira','__pycache__','site'))
 gv.ROOT=destino;gv.Projeto=lambda:Projeto(destino);app=gv.Studio();app.update()
 try:
  app.configurar_site();app.update();painel=app.overlay_stack[-1]
  entradas=[w for w in painel.body.winfo_children() if isinstance(w,ttk.Entry)]
  ativo=next(w for w in painel.body.winfo_children() if isinstance(w,ttk.Checkbutton));ativo.invoke()
  salvar=next(w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button));salvar.invoke();app.update()
  assert not json.loads((destino/'configuracao-site.json').read_text())['comentarios']['ativado'],'Ativação sem serviço deve ser recusada'
  entradas[1].insert(0,'https://comments.example');entradas[2].insert(0,'public-key');salvar.invoke();app.update()
  config=json.loads((destino/'configuracao-site.json').read_text());assert config['comentarios']['ativado'] and config['comentarios']['api_url']=='https://comments.example'
  assert not app.overlay_stack and list((destino/'.literature-backups').rglob('configuracao-site.json'))
  print('OK: configuração na mesma janela; serviço e chave pública obrigatórios ao ativar; gravação e backup; catálogo vazio suportado; nenhuma conta ou comentário real criado.')
 finally:app.destroy()

"""Reações no Studio com serviço em memória e projeto sintético temporário."""
import json,shutil,sys,tempfile,time
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import reacoes_visual as rv
from gestao_projeto import Projeto
from fixture_projeto import preparar_fixture
ROOT=Path(__file__).resolve().parents[1]
class ClienteTeste:
 def __init__(self,api,token):
  assert len(token)>=32
  self.items=[{'thread_id':json.dumps(['literature','obra',None]),'title':'Obra sintética','reactions_enabled':1,'likes':8,'dislikes':2,'paused':0},{'thread_id':json.dumps(['literature','obra','cap']), 'title':'Capítulo sintético','reactions_enabled':1,'likes':3,'dislikes':0,'paused':0}]
 def reacoes(self,depois='',busca=''):return {'items':[dict(i) for i in self.items if busca.lower() in i['title'].lower()],'next':None}
 def pausar_reacoes(self,ident,pausado):next(i for i in self.items if i['thread_id']==ident)['paused']=int(pausado)
 def exportar_reacoes(self):return {'schema_version':1,'reacoes':self.items}
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'projeto';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('node_modules','.wrangler','.git','.agents','.aws','.codex','.literature-backups','.literature-lixeira','__pycache__','site'));preparar_fixture(root)
 config=json.loads((root/'configuracao-site.json').read_text());config['comentarios']['api_url']='https://comments.example';(root/'configuracao-site.json').write_text(json.dumps(config));gv.ROOT=root;gv.Projeto=lambda:Projeto(root);rv.ClienteComentarios=ClienteTeste
 app=gv.Studio();app.update()
 def widgets(w,classe):return [c for c in w.winfo_children() if isinstance(c,classe)]+[item for c in w.winfo_children() for item in widgets(c,classe)]
 def button(nome):return next(w for w in widgets(painel,ttk.Button) if w.cget('text')==nome)
 def esperar(cond):
  fim=time.monotonic()+5
  while time.monotonic()<fim:
   app.update()
   if cond():return
   time.sleep(.02)
  raise AssertionError('Operação não concluída na interface de reações')
 try:
  app.gerenciar_reacoes();app.update();painel=app.overlay_stack[-1];entries=widgets(painel,ttk.Entry);entries[0].insert(0,'x'*40);button('Conectar / atualizar').invoke();lista=widgets(painel,ttk.Treeview)[0];esperar(lambda:len(lista.get_children())==2);assert entries[0].get()==''
  ident=lista.get_children()[0];lista.selection_set(ident);app.update();button('Pausar / retomar selecionado').invoke();esperar(lambda:lista.item(ident,'values')[-1]=='Pausado')
  button('Pausar / retomar selecionado').invoke();esperar(lambda:lista.item(ident,'values')[-1]=='Ativo');assert lista.item(ident,'values')[3]=='10'
  entries[1].insert(0,'Capítulo');button('Aplicar busca').invoke();esperar(lambda:len(lista.get_children())==1);assert lista.item(lista.get_children()[0],'text')=='Capítulo sintético'
  dest=Path(tmp)/'totais.json';original=rv.filedialog.asksaveasfilename;rv.filedialog.asksaveasfilename=lambda **k:str(dest)
  try:button('Exportar totais…').invoke();esperar(lambda:dest.exists())
  finally:rv.filedialog.asksaveasfilename=original
  assert len(json.loads(dest.read_text())['reacoes'])==2,'Exportação inclui todo o catálogo, sem se limitar à busca'
  assert 'x'*40 not in dest.read_text();assert len(app.overlay_stack)==1
  print('OK: reações na mesma janela; conexão assíncrona; totais; seleção; pausa e retomada sem perder votos; busca; exportação completa; credencial só na sessão.')
 finally:app.destroy()

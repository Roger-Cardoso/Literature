"""Moderação integrada com serviço substituto em memória; nenhuma conexão real."""
import json,shutil,sys,tempfile,time
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import moderacao_visual as mv
from gestao_projeto import Projeto
from gerar_site import gerar
ROOT=Path(__file__).resolve().parents[1]
class ClienteTeste:
 def __init__(self,url,token):assert len(token)>=32;self.items=[{'id':'9d272cf6-5273-4b98-8ea4-5456bbb93c85','thread_id':'["literature","obra",null]','author':'Leitora','body':'Texto pendente','status':'pending','title':'Obra de teste','parent_id':None}]
 def listar(self,estado='pending',depois=0):return {'items':[dict(i) for i in self.items if estado=='all' or i['status']==estado],'next':None}
 def alterar(self,ident,estado):next(x for x in self.items if x['id']==ident)['status']=estado
 def excluir(self,ident):self.items=[]
 def sincronizar(self,manifesto):return {'total':len(manifesto['threads'])}
 def exportar(self):return {'schema_version':1,'comentarios':self.items}
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(ROOT,destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.git','.agents','.aws','.codex','.literature-backups','.literature-lixeira','__pycache__','site'))
 config=json.loads((destino/'configuracao-site.json').read_text());config['comentarios']['api_url']='https://comments.example';(destino/'configuracao-site.json').write_text(json.dumps(config));gerar(destino)
 gv.ROOT=destino;gv.Projeto=lambda:Projeto(destino);mv.ClienteComentarios=ClienteTeste;app=gv.Studio();app.update()
 def botao(w,texto):
  for c in w.winfo_children():
   if isinstance(c,ttk.Button) and c.cget('text')==texto:return c
   r=botao(c,texto)
   if r:return r
 def esperar(cond):
  limite=time.monotonic()+4
  while time.monotonic()<limite:
   app.update()
   if cond():return
   time.sleep(.02)
  raise AssertionError('A interface não concluiu a operação')
 try:
  app.moderar_comentarios();app.update();painel=app.overlay_stack[-1]
  def achar(w,classe):
   return [c for c in w.winfo_children() if isinstance(c,classe)]+[x for c in w.winfo_children() for x in achar(c,classe)]
  token=achar(painel.body,ttk.Entry)[0];token.insert(0,'x'*40);botao(painel.body,'Conectar / atualizar').invoke();lista=achar(painel.body,ttk.Treeview)[0]
  esperar(lambda:len(lista.get_children())==1);assert token.get()==''
  ident=lista.get_children()[0];lista.selection_set(ident);botao(painel.body,'Aprovar').invoke();esperar(lambda:not lista.get_children())
  filtro=achar(painel.body,ttk.Combobox)[0];filtro.set('Aprovados');botao(painel.body,'Atualizar').invoke();esperar(lambda:len(lista.get_children())==1)
  lista.selection_set(ident);botao(painel.body,'Ocultar').invoke();esperar(lambda:not lista.get_children())
  filtro.set('Todos');botao(painel.body,'Atualizar').invoke();esperar(lambda:len(lista.get_children())==1)
  original=mv.filedialog.asksaveasfilename;dest=Path(tmp)/'copia-privada.json';mv.filedialog.asksaveasfilename=lambda **k:str(dest)
  try:botao(painel.body,'Exportar cópia…').invoke();esperar(lambda:dest.exists())
  finally:mv.filedialog.asksaveasfilename=original
  assert json.loads(dest.read_text())['comentarios'][0]['status']=='hidden'
  sim=mv.messagebox.askyesno;mv.messagebox.askyesno=lambda *a,**k:True
  try:
   lista.selection_set(ident);botao(painel.body,'Excluir definitivamente…').invoke();esperar(lambda:not lista.get_children())
  finally:mv.messagebox.askyesno=sim
  assert 'x'*40 not in (destino/'configuracao-site.json').read_text()
  print('OK: moderação na mesma janela; token apagado do campo; consulta assíncrona; aprovar; ocultar; exportar cópia; excluir; nenhuma credencial publicada.')
 finally:app.destroy()

"""Revisão e envio da publicação na mesma janela do Literature Studio."""
import json
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser
from editor_componente import modulo
from rolagem import TextoRolavel
from pacote_publicacao import PacotePublicacao
from github_publicacao import GitHub,configuracao,destino,preparar_revisao,enviar,salvar_recibo,ultimo_recibo,acompanhar,sincronizar_comentarios,ambiente,limpar_erro

class PublicacaoPagina(ttk.Frame):
 def __init__(self,parent,studio):
  super().__init__(parent,padding=16);self.studio=studio;self.gh=GitHub();self.pacote=None;self.revisao=None;self.recibo=ultimo_recibo(studio.projeto.root);self.ocupado=False;self.fila=queue.Queue();self.poll=None;self.auth=None;self.auth_cancel=threading.Event()
  self.rolagem=modulo.ScrollableFrame(self);self.rolagem.pack(fill='both',expand=True);body=self.rolagem.content
  cfg=configuracao(studio.projeto.root);self.repo=tk.StringVar(value=cfg['repositorio']);self.branch=tk.StringVar(value=cfg['branch']);self.sincronizar=tk.BooleanVar(value=cfg['sincronizar_comentarios']);self.mensagem=tk.StringVar(value='Atualizar publicação do Literature')
  ttk.Label(body,text='Publicar o Literature',font=('Georgia',22)).pack(anchor='w')
  ttk.Label(body,text='Prepare, confira os arquivos e envie a versão pública ao GitHub. O envio usa a conta do GitHub CLI e funciona sem configurar o Git nesta pasta.',wraplength=720).pack(anchor='w',pady=8)
  cfgbox=ttk.Frame(body);cfgbox.pack(fill='x');cfgbox.columnconfigure(0,weight=4);cfgbox.columnconfigure(1,weight=1)
  ttk.Label(cfgbox,text='Repositório').grid(row=0,column=0,sticky='w');ttk.Label(cfgbox,text='Branch').grid(row=0,column=1,sticky='w')
  ttk.Entry(cfgbox,textvariable=self.repo).grid(row=1,column=0,sticky='ew',padx=(0,8));ttk.Entry(cfgbox,textvariable=self.branch,width=14).grid(row=1,column=1,sticky='ew')
  barra=ttk.Frame(body);barra.pack(fill='x',pady=8)
  for i,(texto,cmd) in enumerate([('Conectar GitHub',self.conectar),('Autorizar no navegador',lambda:webbrowser.open('https://github.com/login/device')),('Cancelar autenticação',self.cancelar_auth),('Preparar e revisar',self.preparar),('Consultar publicação',self.consultar)]):ttk.Button(barra,text=texto,command=cmd).grid(row=i//2,column=i%2,sticky='ew',padx=(0,5),pady=3)
  barra.columnconfigure(0,weight=1);barra.columnconfigure(1,weight=1)
  self.estado=tk.StringVar(value='Prepare a publicação para comparar a versão local com o repositório.');ttk.Label(body,textvariable=self.estado,wraplength=720).pack(anchor='w',pady=5)
  quadro=ttk.Frame(body);quadro.pack(fill='both',expand=True);quadro.columnconfigure(0,weight=1);quadro.rowconfigure(0,weight=1)
  self.lista=ttk.Treeview(quadro,columns=('acao','tamanho'),show='tree headings',height=6,selectmode='browse');self.lista.heading('#0',text='Arquivo público');self.lista.heading('acao',text='Mudança');self.lista.heading('tamanho',text='Bytes');self.lista.column('#0',width=450);self.lista.column('acao',width=90);self.lista.column('tamanho',width=80)
  sy=ttk.Scrollbar(quadro,orient='vertical',command=self.lista.yview);sx=ttk.Scrollbar(quadro,orient='horizontal',command=self.lista.xview);self.lista.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);self.lista.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew')
  self.detalhe=TextoRolavel(body,height=6,wrap='word');self.detalhe.pack(fill='both',expand=True,pady=8);self.detalhe.configure(state='disabled');self.lista.bind('<<TreeviewSelect>>',self.ver_arquivo)
  ttk.Label(body,text='Descrição da atualização').pack(anchor='w');ttk.Entry(body,textvariable=self.mensagem).pack(fill='x',pady=3)
  ttk.Checkbutton(body,text='Sincronizar comentários após implantação aprovada, usando a credencial local',variable=self.sincronizar).pack(anchor='w',pady=5)
  self.botao_enviar=ttk.Button(body,text='Enviar versão revisada',command=self.publicar,state='disabled');self.botao_enviar.pack(anchor='w',pady=5)
  rodape=ttk.Frame(body);rodape.pack(fill='x')
  for i,(nome,cmd) in enumerate([('Abrir site',self.abrir_site),('Abrir execução no GitHub',self.abrir_execucao),('Sincronizar comentários agora',self.sincronizar_agora)]):ttk.Button(rodape,text=nome,command=cmd).grid(row=i//2,column=i%2,sticky='ew',padx=3,pady=3)
  rodape.columnconfigure(0,weight=1);rodape.columnconfigure(1,weight=1)
  body.bind('<Configure>',lambda e:[w.configure(wraplength=max(240,e.width-20)) for w in body.winfo_children() if isinstance(w,ttk.Label)])
  for var in (self.repo,self.branch):var.trace_add('write',self.invalidar)
  self.after(100,self.receber)
  if self.recibo:self.estado.set('Há um envio anterior. Use Consultar publicação para conferir a implantação.')
 def invalidar(self,*args):
  self.revisao=None;self.botao_enviar.configure(state='disabled');self.estado.set('Destino alterado. Prepare e revise novamente.')
 def tarefa(self,func,ok):
  if self.ocupado or self.studio.ocupado:return
  self.ocupado=True;self.studio.ocupado=True;self.botao_enviar.configure(state='disabled')
  def run():
   try:self.fila.put(('resultado',True,func(),ok))
   except Exception as e:self.fila.put(('resultado',False,limpar_erro(e),ok))
  threading.Thread(target=run,daemon=True).start()
 def receber(self):
  try:
   while True:
    kind,success,data,ok=self.fila.get_nowait()
    if kind=='auth':
     self.estado.set('Autorize sua conta no endereço e com o código exibidos abaixo.');self.detalhe.configure(state='normal');self.detalhe.insert('end',data+'\n');self.detalhe.see('end');self.detalhe.configure(state='disabled');continue
    if kind=='auth_done':self.auth=None;self.estado.set(data);continue
    self.ocupado=False;self.studio.ocupado=False
    if success:
     try:ok(data)
     except Exception as e:self.estado.set(limpar_erro(e))
    else:self.estado.set(data)
    self.botao_enviar.configure(state='normal' if self.revisao and self.revisao['mudancas'] and not self.ocupado else 'disabled')
  except queue.Empty:pass
  self.after(100,self.receber)
 def conectar(self):
  if self.ocupado or self.auth:return
  if not shutil.which('gh'):self.estado.set('Instale o GitHub CLI para conectar sua conta. Instruções no guia de publicação do Studio.');return
  self.auth_cancel.clear();self.auth=True;self.detalhe.configure(state='normal');self.detalhe.delete('1.0','end');self.detalhe.configure(state='disabled');self.estado.set('Conferindo conexão com o GitHub…')
  def run():
   try:
    try:
     login=self.gh.usuario();self.fila.put(('auth_done',True,'Conectado como '+login,None));return
    except Exception:pass
    if self.auth_cancel.is_set():self.fila.put(('auth_done',False,'Autenticação cancelada.',None));return
    env=ambiente();env.pop('GH_PROMPT_DISABLED',None);env['GH_BROWSER']='true'
    p=subprocess.Popen(['gh','auth','login','--hostname','github.com','--git-protocol','https','--web'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',env=env)
    self.auth=p
    if self.auth_cancel.is_set():p.terminate()
    for line in p.stdout:
     if self.auth_cancel.is_set():p.terminate();break
     line=line.strip()
     if line:self.fila.put(('auth',True,limpar_erro(line),None))
    code=p.wait();self.fila.put(('auth_done',code==0,'Conexão concluída. Prepare a publicação.' if code==0 else 'Autenticação não concluída. Tente novamente.',None))
   except Exception as e:self.fila.put(('auth_done',False,limpar_erro(e),None))
  threading.Thread(target=run,daemon=True).start()
 def cancelar_auth(self):
  self.auth_cancel.set()
  if isinstance(self.auth,subprocess.Popen):self.auth.terminate()
 def preparar(self):
  if self.ocupado or not self.studio.guard_publicacao():return
  try:repo,branch=destino(self.repo.get(),self.branch.get())
  except Exception as e:self.estado.set(str(e));return
  self.invalidar();self.estado.set('Validando, gerando e comparando com o GitHub…');sincronizar=self.sincronizar.get()
  def run():
   p=PacotePublicacao(self.studio.projeto.root)
   try:
    r=preparar_revisao(p,self.gh,repo,branch)
    path='.literature-studio.json';projeto=self.studio.projeto;_,rev=projeto.ler(path) if projeto.caminho(path).exists() else ({},None)
    projeto.salvar(path,{'schema_version':1,'repositorio':repo,'branch':branch,'sincronizar_comentarios':sincronizar},rev)
    return p,r
   except Exception:p.fechar();raise
  def mostrar(result):
   if self.pacote:self.pacote.fechar()
   self.pacote,self.revisao=result;self.lista.delete(*self.lista.get_children())
   for i,item in enumerate(self.revisao['mudancas']):self.lista.insert('','end',iid=str(i),text=item['path'],values=(item['acao'],item['bytes']))
   n=len(self.revisao['mudancas']);self.estado.set(f"{n} arquivo(s) com mudanças em {repo} → {branch}. Confira a lista e clique em Enviar versão revisada." if n else 'A versão pública já coincide com o repositório. Nenhum envio necessário.')
  self.tarefa(run,mostrar)
 def ver_arquivo(self,event=None):
  if not self.revisao:return
  sel=self.lista.selection()
  if not sel:return
  item=self.revisao['mudancas'][int(sel[0])];texto='Este arquivo será removido da próxima publicação.'
  if item['acao']!='remover':
   try:
    data=self.pacote.ler(item['rel']);texto=data[:50000].decode('utf-8')
    if len(data)>50000:texto+='\n\n[Prévia limitada aos primeiros 50 KB.]'
   except UnicodeDecodeError:texto='Recurso binário: '+str(item['bytes'])+' bytes.'
   except Exception as e:texto=str(e)
  self.detalhe.configure(state='normal');self.detalhe.delete('1.0','end');self.detalhe.insert('1.0',texto);self.detalhe.configure(state='disabled')
 def publicar(self):
  if self.ocupado or not self.revisao or not self.studio.guard_publicacao():return
  pacote,revisao=self.pacote,self.revisao;mensagem=self.mensagem.get();sincronizar=self.sincronizar.get()
  self.estado.set('Enviando somente os arquivos públicos revisados…')
  def run():
   recibo=enviar(pacote,revisao,self.gh,mensagem)
   if not recibo.get('sem_alteracoes'):
    recibo['sincronizar_automaticamente']=sincronizar;salvar_recibo(self.studio.projeto.root,recibo)
   return recibo
  def enviado(recibo):
   self.recibo=recibo;self.revisao=None;self.estado.set('Versão enviada. Aguardando testes e implantação no GitHub Pages.');self.studio.anotar('Publicação enviada: '+recibo.get('url',recibo['commit']));self.agendar()
  self.tarefa(run,enviado)
 def agendar(self):
  if self.poll:self.after_cancel(self.poll)
  self.poll=self.after(15000,self.consultar)
 def consultar(self):
  if self.poll:self.after_cancel(self.poll)
  self.poll=None
  if self.ocupado:self.agendar();return
  ultimo=ultimo_recibo(self.studio.projeto.root)
  if ultimo:self.recibo=ultimo
  if not self.recibo:self.estado.set('Ainda não há um envio registrado neste projeto.');return
  recibo=self.recibo
  def mostrar(run):
   if run.get('url'):recibo['execucao_url']=run['url']
   recibo['execucao']=run;salvar_recibo(self.studio.projeto.root,recibo)
   if run.get('conclusion')=='success':
    self.estado.set('Publicação aprovada e implantada no GitHub Pages.')
    if recibo.get('sincronizar_automaticamente') and not recibo.get('sincronizado'):self.sincronizar_agora()
   elif run['status']=='completed':self.estado.set('A implantação terminou com estado: '+str(run.get('conclusion'))+'. Abra a execução no GitHub para conferir.')
   else:self.estado.set('GitHub Pages: '+run['status']+'. Você pode continuar trabalhando enquanto aguarda.');self.agendar()
  self.tarefa(lambda:acompanhar(self.gh,recibo),mostrar)
 def sincronizar_agora(self):
  if self.ocupado or not self.recibo:return
  from implantar_comentarios import PRIVADO
  recibo=self.recibo
  if not recibo.get('config_comentarios',{}).get('api_url'):self.estado.set('Publicação concluída. Serviço de comentários não configurado nesta versão.');return
  if not PRIVADO.is_file():self.estado.set('Publicação concluída. Carregue a credencial na moderação para sincronizar os comentários.');return
  self.estado.set('Conferindo implantação e sincronizando discussões publicadas…')
  def ok(result):
   recibo['sincronizado']=True;salvar_recibo(self.studio.projeto.root,recibo);self.estado.set(f"Site publicado e comentários sincronizados: {result['total']} discussões.")
  self.tarefa(lambda:sincronizar_comentarios(self.gh,recibo,PRIVADO),ok)
 def abrir_site(self):
  from configuracao_site import carregar
  webbrowser.open(carregar(self.studio.projeto.root)['url_publica']+'/home/')
 def abrir_execucao(self):
  url=(self.recibo or {}).get('execucao_url') or (self.recibo or {}).get('url')
  if url and url.startswith('https://github.com/'):webbrowser.open(url)

class PublicacaoMixin:
 def guard_publicacao(self):
  if not self._continuar_obras() or not self.salvar_autoria():return False
  if self.editor and self.editor.vinculo and self.editor.text.get('1.0','end-1c').strip():
   from integracao_semantica import sem_runtime
   html=self.projeto.caminho(self.editor.vinculo['alvo']).read_text(encoding='utf-8')
   if sem_runtime(self.editor.build_html())!=html:
    self.exibir_editor(self.editor);self.anotar('Revise e aplique a autoria ao capítulo antes de preparar ou enviar a publicação.');self.editor.revisar();return False
  return True
 def gerenciar_publicacao(self):
  if not self._continuar_obras():return
  try:
   if not hasattr(self,'pagina_publicacao'):
    self.pagina_publicacao=PublicacaoPagina(self.abas,self);self.abas.add(self.pagina_publicacao,text='Publicação no GitHub')
   self.abas.select(self.pagina_publicacao);self.configure(menu='')
  except Exception as e:self.anotar('Publicação: '+str(e))

"""Consulta e controle de reações na janela do Studio, sem guardar credenciais."""
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from configuracao_site import carregar
from cliente_comentarios import ClienteComentarios
from editor_componente import OverlayPanel

class ReacoesMixin:
 def gerenciar_reacoes(self):
  if not self.continuar():return
  try:
   api=carregar(self.projeto.root)['comentarios']['api_url']
   if not api:raise ValueError('Configure o endereço do serviço em Site e comentários.')
   painel=OverlayPanel(self,'Reações dos leitores',width=1000,height=740,scrollable=True)
   ttk.Label(painel.body,text='Gostei e Não gostei',font=('Georgia',20)).pack(anchor='w',pady=8)
   ttk.Label(painel.body,text='Totais por obra e capítulo no catálogo sincronizado. Uma reação por navegador; estes números não representam pessoas únicas. Pausar preserva os votos. Para ativar ou desativar nas fichas, gere e publique a alteração.',wraplength=820).pack(anchor='w',pady=8)
   ttk.Label(painel.body,text='Credencial de moderação — somente nesta sessão').pack(anchor='w');token=ttk.Entry(painel.body,show='•');token.pack(fill='x',pady=5)
   barra=ttk.Frame(painel.body);barra.pack(fill='x',pady=5)
   ttk.Label(painel.body,text='Buscar obra ou capítulo pelo título').pack(anchor='w');busca=ttk.Entry(painel.body);busca.pack(fill='x',pady=5)
   quadro=ttk.Frame(painel.body);quadro.pack(fill='both',expand=True);quadro.columnconfigure(0,weight=1);quadro.rowconfigure(0,weight=1)
   lista=ttk.Treeview(quadro,columns=('tipo','likes','dislikes','total','estado'),show='tree headings',height=9,selectmode='browse')
   lista.heading('#0',text='Obra / capítulo');lista.column('#0',width=330)
   for col,label,width in [('tipo','Tipo',75),('likes','Gostei',75),('dislikes','Não gostei',85),('total','Votos',75),('estado','Situação',150)]:lista.heading(col,text=label);lista.column(col,width=width,anchor='center')
   y=ttk.Scrollbar(quadro,orient='vertical',command=lista.yview);x=ttk.Scrollbar(quadro,orient='horizontal',command=lista.xview);lista.configure(yscrollcommand=y.set,xscrollcommand=x.set);lista.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew')
   estado=tk.StringVar(value='Carregue a credencial e conecte para consultar os totais.');ttk.Label(painel.body,textvariable=estado,wraplength=820).pack(anchor='w',pady=8)
   detalhe=tk.StringVar();ttk.Label(painel.body,textvariable=detalhe,wraplength=820).pack(anchor='w',pady=5)
   sessao={'cliente':None,'ocupado':False,'itens':{},'next':None,'busca':''};eventos=queue.Queue()
   def executar(func,ok):
    if sessao['ocupado']:return
    sessao['ocupado']=True;busca.configure(state='disabled');estado.set('Consultando o serviço…')
    def trabalho():
     try:eventos.put((True,func(),ok))
     except Exception as e:eventos.put((False,str(e),ok))
    threading.Thread(target=trabalho,daemon=True).start()
   def receber():
    if not painel.winfo_exists():return
    try:
     sucesso,dados,ok=eventos.get_nowait();sessao['ocupado']=False;busca.configure(state='normal')
     if sucesso:ok(dados)
     else:estado.set(dados)
    except queue.Empty:pass
    painel.after(80,receber)
   painel.after(80,receber)
   def cliente():
    if not sessao['cliente']:raise ValueError('Conecte ao serviço primeiro.')
    return sessao['cliente']
   def mostrar(pagina,mais=False):
    anterior=lista.selection()
    if not mais:lista.delete(*lista.get_children());sessao['itens']={};detalhe.set('')
    for item in pagina['items']:
     ident=item['thread_id']
     if ident in sessao['itens']:continue
     sessao['itens'][ident]=item
     situacao='Desativado no catálogo' if not item['reactions_enabled'] else 'Pausado' if item['paused'] else 'Ativo'
     lista.insert('','end',iid=ident,text=item['title'],values=('Obra' if json.loads(ident)[2] is None else 'Capítulo',item['likes'],item['dislikes'],item['likes']+item['dislikes'],situacao))
    if anterior and anterior[0] in sessao['itens']:lista.selection_set(anterior[0]);selecionar()
    sessao['next']=pagina.get('next');estado.set(f"{len(sessao['itens'])} itens carregados. "+('Há mais resultados.' if sessao['next'] else 'Consulta concluída.'))
   def atualizar(mais=False):
    if sessao['ocupado']:return
    try:
     c=cliente();after=sessao['next'] if mais else ''
     if mais and after is None:return
     if not mais:
      termo=busca.get().strip()
      if len(termo)>100:raise ValueError('Use até 100 caracteres na busca.')
      sessao['busca']=termo
     termo=sessao['busca'];executar(lambda:c.reacoes(after,termo),lambda d:mostrar(d,mais))
    except Exception as e:estado.set(str(e))
   def carregar_token():
    if sessao['ocupado']:return
    origem=filedialog.askopenfilename(parent=self,title='Credencial privada do Literature',initialdir=Path.home()/'.config/literature',filetypes=[('JSON','*.json')])
    if not origem:return
    try:
     dados=json.loads(Path(origem).read_text(encoding='utf-8'))
     if dados.get('api_url')!=api:raise ValueError('A credencial não corresponde ao serviço configurado.')
     valor=dados.get('admin_token','')
     if not isinstance(valor,str) or len(valor)<32:raise ValueError('Credencial incompleta.')
     token.delete(0,'end');token.insert(0,valor);estado.set('Credencial carregada. Clique em Conectar / atualizar.')
    except (ValueError,OSError) as e:estado.set(str(e))
   def conectar():
    if sessao['ocupado']:return
    try:sessao['cliente']=ClienteComentarios(api,token.get());token.delete(0,'end');atualizar()
    except Exception as e:estado.set(str(e))
   def selecionar(_event=None):
    sel=lista.selection()
    if not sel:return
    item=sessao['itens'][sel[0]];total=item['likes']+item['dislikes'];percentual=f"{item['likes']/total:.1%} de Gostei entre {total} votos" if total else 'Ainda sem votos'
    detalhe.set(item['title']+' — '+percentual+'. '+('Reações pausadas.' if item['paused'] else 'Sem pausa administrativa.'))
   lista.bind('<<TreeviewSelect>>',selecionar)
   def pausar():
    sel=lista.selection()
    if not sel or sessao['ocupado']:return
    try:
     item=sessao['itens'][sel[0]];c=cliente();executar(lambda:c.pausar_reacoes(sel[0],not bool(item['paused'])),lambda _:atualizar())
    except Exception as e:estado.set(str(e))
   def exportar():
    if sessao['ocupado']:return
    try:
     c=cliente();dest=filedialog.asksaveasfilename(parent=self,title='Exportar totais do catálogo sincronizado',initialfile='reacoes-literature.json',defaultextension='.json',filetypes=[('JSON','*.json')])
     if not dest:return
     if Path(dest).resolve().is_relative_to(self.projeto.root):raise ValueError('Salve fora do projeto para não substituir arquivos do site.')
     def salvar(dados):
      try:Path(dest).write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');estado.set('Totais exportados. A cópia não inclui identificadores dos visitantes.')
      except OSError:estado.set('Não foi possível salvar a exportação.')
     executar(c.exportar_reacoes,salvar)
    except Exception as e:estado.set(str(e))
   for nome,cmd in [('Carregar credencial…',carregar_token),('Conectar / atualizar',conectar),('Atualizar',atualizar),('Mais resultados',lambda:atualizar(True))]:ttk.Button(barra,text=nome,command=cmd).pack(side='left',padx=3)
   acoes=ttk.Frame(painel.body);acoes.pack(fill='x',pady=8)
   for nome,cmd in [('Aplicar busca',atualizar),('Pausar / retomar selecionado',pausar),('Exportar totais…',exportar)]:ttk.Button(acoes,text=nome,command=cmd).pack(side='left',padx=3)
   busca.bind('<Return>',lambda _:atualizar())
  except Exception as e:messagebox.showerror('Reações',str(e),parent=self)

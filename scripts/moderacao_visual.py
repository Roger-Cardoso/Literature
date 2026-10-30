"""Moderação de comentários na mesma janela do Studio, sem salvar credenciais."""
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from configuracao_site import carregar
from cliente_comentarios import ClienteComentarios
from editor_componente import OverlayPanel
from estado_publicacao import assinatura_fontes,assinatura_gerada
from rolagem import TextoRolavel

class ModeracaoMixin:
 def moderar_comentarios(self):
  if not self.continuar():return
  try:
   config=carregar(self.projeto.root);api=config['comentarios']['api_url']
   if not api:raise ValueError('Primeiro informe o endereço do Worker em Site e comentários.')
   painel=OverlayPanel(self,'Moderação de comentários',width=1000,height=760,scrollable=True)
   ttk.Label(painel.body,text='Conversas do Literature',font=('Georgia',20)).pack(anchor='w',pady=8)
   ttk.Label(painel.body,text='A credencial de moderação não é salva em arquivos nem publicada. Os nomes dos visitantes não são identidades verificadas.',wraplength=820).pack(anchor='w',pady=6)
   acesso=ttk.Frame(painel.body);acesso.pack(fill='x');ttk.Label(acesso,text='Credencial de moderação').pack(anchor='w');credencial=ttk.Entry(acesso,show='•');credencial.pack(fill='x',pady=5)
   barra=ttk.Frame(painel.body);barra.pack(fill='x',pady=8)
   filtro=ttk.Combobox(barra,state='readonly',values=['Pendentes','Aprovados','Ocultos','Todos'],width=15);filtro.set('Pendentes');filtro.pack(side='left',padx=3)
   quadro=ttk.Frame(painel.body);quadro.pack(fill='both',expand=True);quadro.columnconfigure(0,weight=1);quadro.rowconfigure(0,weight=1)
   lista=ttk.Treeview(quadro,columns=('autor','estado'),show='tree headings',height=7,selectmode='browse');lista.heading('#0',text='Obra / capítulo');lista.heading('autor',text='Nome informado');lista.heading('estado',text='Moderação');lista.column('#0',width=370);lista.column('autor',width=180);lista.column('estado',width=100)
   y=ttk.Scrollbar(quadro,orient='vertical',command=lista.yview);x=ttk.Scrollbar(quadro,orient='horizontal',command=lista.xview);lista.configure(yscrollcommand=y.set,xscrollcommand=x.set);lista.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew')
   texto=TextoRolavel(painel.body,height=7,wrap='word');texto.pack(fill='both',expand=True,pady=8);texto.configure(state='disabled')
   estado=tk.StringVar(value='Informe a credencial e clique em Conectar / atualizar.');ttk.Label(painel.body,textvariable=estado,wraplength=820).pack(anchor='w',pady=6)
   sessao={'cliente':None,'itens':{},'next':None,'ocupado':False};eventos=queue.Queue();filtros={'Pendentes':'pending','Aprovados':'approved','Ocultos':'hidden','Todos':'all'};nomes={'pending':'Pendente','approved':'Aprovado','hidden':'Oculto'}
   def executar(func,ok):
    if sessao['ocupado']:return
    sessao['ocupado']=True;filtro.configure(state='disabled');estado.set('Conectando ao serviço…')
    def trabalho():
     try:eventos.put((True,func(),ok))
     except Exception as e:eventos.put((False,str(e),ok))
    threading.Thread(target=trabalho,daemon=True).start()
   def receber():
    if not painel.winfo_exists():return
    try:
     sucesso,dados,ok=eventos.get_nowait();sessao['ocupado']=False;filtro.configure(state='readonly')
     if sucesso:ok(dados)
     else:estado.set(dados)
    except queue.Empty:pass
    painel.after(80,receber)
   painel.after(80,receber)
   def cliente():
    if not sessao['cliente']:raise ValueError('Conecte à moderação primeiro.')
    return sessao['cliente']
   def mostrar(pagina,acumular=False):
    if not acumular:lista.delete(*lista.get_children());sessao['itens']={}
    for item in pagina['items']:
     sessao['itens'][item['id']]=item;lista.insert('','end',iid=item['id'],text=item.get('title') or 'Discussão fora do catálogo atual',values=(item['author'],nomes[item['status']]))
    sessao['next']=pagina.get('next');estado.set(f"{len(sessao['itens'])} comentário(s) nesta consulta. "+('Há mais resultados.' if sessao['next'] else 'Consulta concluída.'))
   def atualizar(acumular=False):
    try:
     c=cliente();after=sessao['next'] if acumular else 0
     if acumular and after is None:return
     selecionado=filtros[filtro.get()];executar(lambda:c.listar(selecionado,after),lambda d:mostrar(d,acumular))
    except Exception as e:estado.set(str(e))
   def carregar_credencial():
    if sessao['ocupado']:return
    origem=filedialog.askopenfilename(parent=self,title='Arquivo privado da credencial de moderação',initialdir=Path.home()/'.config/literature',filetypes=[('Credencial JSON','*.json')])
    if not origem:return
    try:
     dados=json.loads(Path(origem).read_text(encoding='utf-8'))
     if dados.get('api_url')!=api:raise ValueError('A credencial não corresponde ao endereço do serviço configurado.')
     token=dados.get('admin_token','')
     if not isinstance(token,str) or len(token)<32:raise ValueError('Credencial incompleta.')
     credencial.delete(0,'end');credencial.insert(0,token);estado.set('Credencial carregada somente na sessão. Clique em Conectar / atualizar.')
    except (ValueError,OSError) as e:estado.set(str(e))
   def conectar():
    if sessao['ocupado']:return
    try:
     sessao['cliente']=ClienteComentarios(api,credencial.get());credencial.delete(0,'end');atualizar()
    except Exception as e:estado.set(str(e))
   def detalhe(event=None):
    sel=lista.selection();texto.configure(state='normal');texto.delete('1.0','end')
    if sel:
     item=sessao['itens'][sel[0]];texto.insert('1.0',f"Nome informado: {item['author']}\nEstado: {nomes[item['status']]}\nDiscussão: {item['thread_id']}\nResposta a: {item.get('parent_id') or 'Comentário principal'}\n\n{item['body']}")
    texto.configure(state='disabled')
   lista.bind('<<TreeviewSelect>>',detalhe)
   def alterar(destino):
    sel=lista.selection()
    if not sel or sessao['ocupado']:return
    try:
     c=cliente();executar(lambda:c.alterar(sel[0],destino),lambda _:atualizar())
    except Exception as e:estado.set(str(e))
   def excluir():
    sel=lista.selection()
    if not sel or sessao['ocupado']:return
    if not messagebox.askyesno('Excluir comentário','Excluir definitivamente este comentário e todas as suas respostas? Exporte uma cópia antes se desejar preservá-los.',parent=self):return
    try:
     c=cliente();executar(lambda:c.excluir(sel[0]),lambda _:atualizar())
    except Exception as e:estado.set(str(e))
   def sincronizar():
    if sessao['ocupado']:return
    try:
     c=cliente()
     if assinatura_gerada(self.projeto.root)!=assinatura_fontes(self.projeto.root):raise ValueError('Gere o site com as fontes atuais antes de sincronizar.')
     manifesto=json.loads((self.projeto.root/'site/comentarios-manifesto.json').read_text());n=len(manifesto['threads'])
     if not messagebox.askyesno('Sincronizar discussões',f'Habilitar exatamente as {n} discussões do site gerado? Discussões que saíram do catálogo deixarão de receber envios e de aparecer publicamente. Publique esta mesma versão do site.',parent=self):return
     executar(lambda:c.sincronizar(manifesto),lambda d:estado.set(f"{d['total']} discussões sincronizadas. Comentários existentes foram preservados."))
    except Exception as e:estado.set(str(e))
   def exportar():
    if sessao['ocupado']:return
    try:
     c=cliente();dest=filedialog.asksaveasfilename(parent=self,title='Exportar comentários — inclui pendentes e ocultos',initialfile='comentarios-literature.json',defaultextension='.json',filetypes=[('JSON','*.json')])
     if not dest:return
     if Path(dest).resolve().is_relative_to(self.projeto.root):raise ValueError('Salve a cópia fora da pasta do projeto, para não publicar comentários privados.')
     def guardar(dados):
      try:
       from pathlib import Path
       Path(dest).write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');estado.set('Cópia exportada. Ela inclui comentários não públicos; guarde fora dos arquivos publicados.')
      except OSError:estado.set('Não foi possível salvar a cópia exportada.')
     executar(c.exportar,guardar)
    except Exception as e:estado.set(str(e))
   for nome,cmd in [('Carregar credencial…',carregar_credencial),('Conectar / atualizar',conectar),('Atualizar',atualizar),('Mais resultados',lambda:atualizar(True))]:ttk.Button(barra,text=nome,command=cmd).pack(side='left',padx=3)
   acoes=ttk.Frame(painel.body);acoes.pack(fill='x',pady=8)
   for i,(nome,cmd) in enumerate([('Aprovar',lambda:alterar('approved')),('Ocultar',lambda:alterar('hidden')),('Voltar a pendente',lambda:alterar('pending')),('Excluir definitivamente…',excluir),('Sincronizar discussões…',sincronizar),('Exportar cópia…',exportar)]):
    ttk.Button(acoes,text=nome,command=cmd).grid(row=i//2,column=i%2,sticky='ew',padx=3,pady=3)
   acoes.columnconfigure(0,weight=1);acoes.columnconfigure(1,weight=1)
   ttk.Label(painel.body,text='Ocultar uma mensagem também esconde suas respostas. Aprovar não garante a visibilidade se o comentário original estiver oculto ou a discussão tiver saído do catálogo.',wraplength=820).pack(anchor='w',pady=8)
  except Exception as e:messagebox.showerror('Moderação',str(e),parent=self)

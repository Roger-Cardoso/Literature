"""Operações editoriais por destino e posição, sem renomear textos ou identidades."""
import tkinter as tk
from tkinter import ttk,messagebox
import hierarquia as hier
from editor_componente import OverlayPanel

class OrganizacaoMixin:
 def no_ativo(self,arvore):
  if self.obj and self.atual and self.atual[1].endswith('/editorial.json'):
   no=hier.encontrar(arvore,self.obj.get('id'))
   if no:return no
  _,cap=self.capitulo_ativo()
  return hier.encontrar(arvore,cap['id']) if cap else None
 def atualizar_organizacao(self,slug,ident):
  self.inventario(foco='editorial:'+slug+':'+ident)
  self.anotar('Estrutura atualizada com backup. Identidades, números editoriais, textos e autoria foram preservados. Valide e gere novamente.')
 def deslocar(self,delta):
  if not self.continuar():return
  try:
   slug=self.contexto();doc,rev=self.projeto.ler(f'{slug}/dados/editorial.json');no=self.no_ativo(doc)
   if no is None:raise ValueError('Selecione um capítulo, uma saga, um volume ou um arco.')
   destino=no.posicao[-1]+delta;lista=hier.lista_destino(doc,no.tipo,no.pai)
   if not 1<=destino<=len(lista):self.anotar('O item já está no limite deste agrupamento.');return
   self.projeto.organizar(slug,hier.mover(doc,no.id,no.pai,destino),rev);self.atualizar_organizacao(slug,no.id)
  except Exception as e:messagebox.showerror('Reordenar',str(e),parent=self)
 def localizar_atual(self):
  iid=getattr(self,'_iid_atual',None)
  if not iid:return
  if not self.tree.exists(iid):
   self.navegacao.busca.set('');self.navegacao.filtro.set('Todos')
   if self.navegacao.job:self.navegacao.after_cancel(self.navegacao.job);self.navegacao.job=None
   self.inventario()
  self.navegacao.revelar(iid)
 def _destinos(self,doc,tipo):
  if tipo=='saga' or tipo=='capitulo' and 'capitulos' in doc:return [(None,'Raiz da obra')]
  esperado=hier.NIVEIS[hier.NIVEIS.index(tipo)-1]
  return [(n.id,n.endereco+' · '+' / '.join(n.nomes)) for n in hier.nos(doc) if n.tipo==esperado]
 def _campos_posicao(self,painel,doc,tipo,pai=None,posicao=None,movendo=None):
  destinos=self._destinos(doc,tipo)
  if not destinos:raise ValueError('Crie primeiro o agrupamento de destino em Organizar capítulos.')
  ttk.Label(painel.body,text='Agrupamento de destino').pack(anchor='w',pady=(12,4))
  combo=ttk.Combobox(painel.body,state='readonly',values=[label for _,label in destinos],width=70);combo.pack(fill='x')
  indice=next((i for i,(ident,_) in enumerate(destinos) if ident==pai),0);combo.current(indice)
  ttk.Label(painel.body,text='Posição final entre os itens deste agrupamento (começa em 1)').pack(anchor='w',pady=(12,4))
  valor=tk.StringVar();spin=ttk.Spinbox(painel.body,textvariable=valor,from_=1,to=1,width=10);spin.pack(anchor='w')
  informacao=tk.StringVar();ttk.Label(painel.body,textvariable=informacao,wraplength=650).pack(anchor='w',pady=8)
  def atualizar(event=None,inicial=False):
   ident=destinos[combo.current()][0];lista=hier.lista_destino(doc,tipo,ident)
   limite=len(lista)+(0 if movendo and ident==movendo.pai else 1)
   spin.configure(to=max(1,limite));valor.set(str(posicao if inicial and posicao is not None else limite))
   informacao.set(f'{len(lista)} item(ns) atualmente neste destino. A sequência dos irmãos será ajustada; o número editorial do capítulo não muda.')
  combo.bind('<<ComboboxSelected>>',atualizar);atualizar(inicial=True)
  return lambda:(destinos[combo.current()][0],int(valor.get()))
 def organizar_estrutura(self):
  if not self.continuar():return
  try:
   slug=self.contexto();doc,rev=self.projeto.ler(f'{slug}/dados/editorial.json');no=self.no_ativo(doc)
   painel=OverlayPanel(self,'Organizar capítulos — '+slug,width=800,height=620)
   ttk.Label(painel.body,text='A posição organiza a leitura. IDs, arquivos, autoria e números editoriais são mantidos.',wraplength=650).pack(anchor='w',pady=10)
   if 'capitulos' in doc:
    ttk.Label(painel.body,text='Esta obra usa capítulos simples. Para criar sagas, volumes e arcos, você pode organizar os capítulos existentes em Saga 1 → Volume 1 → Arco 1. A ordem e os metadados dos capítulos serão preservados.',wraplength=650).pack(anchor='w',pady=12)
    def converter():
     try:
      novo=hier.converter_simples(doc);self.projeto.organizar(slug,novo,rev);painel.close();self.atualizar_organizacao(slug,next(hier.nos(novo)).id)
     except Exception as e:painel.set_error(str(e))
    ttk.Button(painel.body,text='Aplicar organização em sagas, volumes e arcos',command=converter).pack(anchor='w',pady=8)
   barra=ttk.Frame(painel.body);barra.pack(fill='x',pady=10)
   def abrir(func):painel.close();func()
   ttk.Button(barra,text='Novo capítulo…',command=lambda:abrir(self.novo_capitulo)).pack(side='left',padx=4)
   if 'sagas' in doc:ttk.Button(barra,text='Novo agrupamento…',command=lambda:abrir(self.novo_agrupamento)).pack(side='left',padx=4)
   if no:
    ttk.Label(painel.body,text='Selecionado: '+no.endereco+' · '+' / '.join(no.nomes),wraplength=650).pack(anchor='w',pady=10)
    posicao=self._campos_posicao(painel,doc,no.tipo,no.pai,no.posicao[-1],no)
    previa=tk.StringVar();ttk.Label(painel.body,textvariable=previa,wraplength=650).pack(anchor='w',pady=12)
    proposta={}
    def revisar():
     try:
      pai,pos=posicao();novo=hier.mover(doc,no.id,pai,pos);alvo=hier.encontrar(novo,no.id)
      proposta.update(doc=novo,pai=pai,pos=pos)
      previa.set('De: '+no.endereco+' · '+' / '.join(no.nomes)+'\nPara: '+alvo.endereco+' · '+' / '.join(alvo.nomes)+'\nOs demais itens dos agrupamentos afetados serão reposicionados.')
      aplicar.configure(state='normal')
     except Exception as e:painel.set_error(str(e))
    def gravar():
     try:
      pai,pos=posicao()
      if (pai,pos)!=(proposta.get('pai'),proposta.get('pos')):raise ValueError('O destino ou a posição mudou. Confira novamente a movimentação.')
      self.projeto.organizar(slug,proposta['doc'],rev);painel.close();self.atualizar_organizacao(slug,no.id)
     except Exception as e:painel.set_error(str(e))
    ttk.Button(painel.footer,text='Conferir movimentação',command=revisar).pack(side='left',padx=6)
    aplicar=ttk.Button(painel.footer,text='Aplicar movimentação com backup',command=gravar,state='disabled');aplicar.pack(side='left',padx=6)
    if no.tipo=='capitulo':
     ttk.Button(painel.body,text='Inserir novo capítulo antes deste…',command=lambda:abrir(lambda:self.novo_capitulo('antes'))).pack(anchor='w',pady=4)
     ttk.Button(painel.body,text='Inserir novo capítulo depois deste…',command=lambda:abrir(lambda:self.novo_capitulo('depois'))).pack(anchor='w',pady=4)
  except Exception as e:messagebox.showerror('Organizar capítulos',str(e),parent=self)
 def novo_capitulo(self,relacao='depois'):
  if not self.continuar():return
  painel=None
  try:
   slug=self.contexto();doc,rev=self.projeto.ler(f'{slug}/dados/editorial.json');no=self.no_ativo(doc)
   pai=None;pos=None
   if no:
    if no.tipo=='arco':pai=no.id
    elif no.tipo=='capitulo':pai=no.pai;pos=no.posicao[-1]+(relacao!='antes')
    else:pai=next((n.id for n in hier.nos(doc) if n.tipo=='arco' and n.caminho[:len(no.caminho)]==no.caminho),None)
   # Valida destinos antes de abrir o painel.
   if not self._destinos(doc,'capitulo'):raise ValueError('Crie uma saga, um volume e um arco em Organizar capítulos antes de inserir capítulos.')
   painel=OverlayPanel(self,'Novo capítulo',width=760,height=520)
   ttk.Label(painel.body,text='Título do capítulo').pack(anchor='w',pady=8);titulo=ttk.Entry(painel.body);titulo.pack(fill='x');titulo.focus_set()
   posicao=self._campos_posicao(painel,doc,'capitulo',pai,pos)
   ttk.Label(painel.body,text='Será criado como rascunho. A posição será inserida sem alterar os IDs, textos ou números editoriais existentes.',wraplength=650).pack(anchor='w',pady=16)
   def criar():
    try:
     destino,indice=posicao();ident=self.projeto.novo_capitulo(slug,titulo.get(),doc,rev,destino=destino,posicao=indice);painel.close();self.atualizar_organizacao(slug,ident)
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Criar capítulo nesta posição',command=criar).pack(pady=8)
  except Exception as e:
   if painel:painel.close()
   messagebox.showerror('Novo capítulo',str(e),parent=self)
 def novo_agrupamento(self):
  if not self.continuar():return
  try:
   slug=self.contexto();doc,rev=self.projeto.ler(f'{slug}/dados/editorial.json');no=self.no_ativo(doc)
   if 'capitulos' in doc:raise ValueError('Use Organizar capítulos para converter a obra simples em hierarquia.')
   painel=OverlayPanel(self,'Novo agrupamento',width=760,height=570)
   ttk.Label(painel.body,text='Tipo de agrupamento').pack(anchor='w',pady=6)
   tipo=ttk.Combobox(painel.body,state='readonly',values=['saga','volume','arco']);tipo.pack(fill='x');tipo.set('saga' if not no else {'saga':'volume','volume':'arco','arco':'arco','capitulo':'arco'}[no.tipo])
   ttk.Label(painel.body,text='Nome').pack(anchor='w',pady=6);nome=ttk.Entry(painel.body);nome.pack(fill='x')
   campos=ttk.Frame(painel.body);campos.pack(fill='x');posicao=[None]
   # O quadro de posição reutiliza o mesmo contrato dos capítulos.
   class Quadro:
    body=campos
   def atualizar(event=None):
    for w in campos.winfo_children():w.destroy()
    try:
     pai=None;ancestral=no;indice={n.id:n for n in hier.nos(doc)}
     esperado=hier.NIVEIS[hier.NIVEIS.index(tipo.get())-1] if tipo.get()!='saga' else None
     while ancestral and esperado:
      if ancestral.tipo==esperado:pai=ancestral.id;break
      ancestral=indice.get(ancestral.pai)
     posicao[0]=self._campos_posicao(Quadro,doc,tipo.get(),pai)
    except ValueError as e:posicao[0]=None;ttk.Label(campos,text=str(e),wraplength=650).pack()
   tipo.bind('<<ComboboxSelected>>',atualizar);atualizar()
   def criar():
    try:
     if posicao[0] is None:raise ValueError('Crie primeiro o agrupamento pai.')
     pai,pos=posicao[0]();novo,ident=hier.novo_grupo(doc,tipo.get(),nome.get(),pai,pos);self.projeto.organizar(slug,novo,rev);painel.close();self.atualizar_organizacao(slug,ident)
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Criar agrupamento nesta posição',command=criar).pack(pady=8)
  except Exception as e:messagebox.showerror('Novo agrupamento',str(e),parent=self)

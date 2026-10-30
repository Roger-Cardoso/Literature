"""Navegação hierárquica com posições, filtros e filhos de capítulos sob demanda."""
import tkinter as tk
from tkinter import ttk
import hierarquia as hier

class ArvoreEditorial(ttk.Frame):
 def __init__(self,parent,projeto,atualizar,subir,descer,revelar):
  super().__init__(parent);self.projeto=projeto;self.atualizar=atualizar;self.job=None;self.filtrando=False;self.abertos_base=set();self.itens={};self.referencias={};self.pais={};self.nos={};self.pendentes={};self.caminhos={}
  self.busca=tk.StringVar();self.filtro=tk.StringVar(value='Todos')
  ttk.Label(self,text='Buscar título, número, ID ou agrupamento').pack(anchor='w',pady=(0,4))
  ttk.Entry(self,textvariable=self.busca).pack(fill='x')
  barra=ttk.Frame(self);barra.pack(fill='x',pady=5)
  barra.columnconfigure(0,weight=1)
  ttk.Combobox(barra,textvariable=self.filtro,values=['Todos','publicado','rascunho','arquivado'],state='readonly',width=12).grid(row=0,column=0,sticky='ew',padx=(0,4))
  ttk.Button(barra,text='↑ Subir',width=7,command=subir).grid(row=0,column=1,padx=2)
  ttk.Button(barra,text='↓ Descer',width=7,command=descer).grid(row=0,column=2,padx=2)
  ttk.Button(barra,text='Expandir caminho atual',command=revelar).grid(row=1,column=0,columnspan=2,sticky='ew',pady=5,padx=(0,4))
  ttk.Button(barra,text='Recolher',command=self.recolher).grid(row=1,column=2,sticky='ew',pady=5)
  quadro=ttk.Frame(self);quadro.pack(fill='both',expand=True);quadro.columnconfigure(0,weight=1);quadro.rowconfigure(0,weight=1)
  self.tree=ttk.Treeview(quadro,show='tree headings',columns=('posicao','estado'),selectmode='browse')
  self.tree.heading('#0',text='Obra e estrutura');self.tree.heading('posicao',text='Posição');self.tree.heading('estado',text='Publicação')
  self.tree.column('#0',width=265,minwidth=180);self.tree.column('posicao',width=85,minwidth=65,stretch=False);self.tree.column('estado',width=90,minwidth=75,stretch=False)
  vertical=ttk.Scrollbar(quadro,orient='vertical',command=self.tree.yview);horizontal=ttk.Scrollbar(quadro,orient='horizontal',command=self.tree.xview)
  self.tree.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
  self.tree.grid(row=0,column=0,sticky='nsew');vertical.grid(row=0,column=1,sticky='ns');horizontal.grid(row=1,column=0,sticky='ew')
  self.resumo=tk.StringVar();ttk.Label(self,textvariable=self.resumo).pack(anchor='w',pady=4)
  self.tree.bind('<<TreeviewOpen>>',self.abrir)
  for var in (self.busca,self.filtro):var.trace_add('write',self.agendar)
 def agendar(self,*args):
  if self.job:self.after_cancel(self.job)
  self.job=self.after(250,self.filtrar)
 def filtrar(self):self.job=None;self.atualizar()
 def todos(self,pai=''):
  for iid in self.tree.get_children(pai):
   yield iid;yield from self.todos(iid)
 def recolher(self):
  for iid in self.todos():self.tree.item(iid,open=False)
 def registrar(self,iid,descr,pai,caminho):
  self.referencias[iid]=descr;self.pais[iid]=pai;self.caminhos[iid]=caminho
 def inserir(self,iid,pai,texto,descr=None,posicao='',estado='',aberto=False):
  self.tree.insert(pai,'end',iid=iid,text=texto,values=(posicao,estado),open=aberto)
  if descr:self.itens[iid]=descr
 def montar(self,atual=None):
  if self.job:self.after_cancel(self.job);self.job=None
  abertos={i for i in self.todos() if self.tree.item(i,'open')};y=self.tree.yview()[0] if self.tree.get_children() else 0
  ativo=bool(self.busca.get().strip() or self.filtro.get()!='Todos')
  if ativo and not self.filtrando:self.abertos_base=abertos.copy()
  if not ativo and self.filtrando:abertos=self.abertos_base
  primeiro=not self.referencias;self.filtrando=ativo
  preparados=[]
  for slug in self.projeto.obras():
   info,_=self.projeto.ler(f'{slug}/dados/info-obra.json');arvore,_=self.projeto.ler(f'{slug}/dados/editorial.json');hier.validar(arvore)
   preparados.append((slug,info,arvore))
  self.tree.delete(*self.tree.get_children());self.itens={};self.referencias={};self.pais={};self.nos={};self.pendentes={};self.caminhos={}
  total=visiveis=0;termo=hier.normalizar(self.busca.get().strip())
  for slug,info,arvore in preparados:
   raiz='obra:'+slug;path=f'{slug}/dados/info-obra.json';titulo=info['titulo']
   self.registrar(raiz,(slug,path,()),'',titulo);self.inserir(raiz,'',titulo,self.referencias[raiz],estado=info['estado_publicacao'],aberto=primeiro or raiz in abertos)
   capa=raiz+':capa';self.registrar(capa,(slug,path,('capa',)),raiz,titulo+' / Capa');self.inserir(capa,raiz,'Capa',self.referencias[capa])
   for campo,nome in [('personagens','Personagens'),('lore','Universo')]:
    grupo=raiz+':'+campo;self.registrar(grupo,(slug,path,()),raiz,titulo+' / '+nome);self.inserir(grupo,raiz,nome,self.referencias[grupo],aberto=grupo in abertos)
    for i,item in enumerate(info.get(campo,[])):
     iid=grupo+':'+item['id'];texto=item.get('nome',item.get('titulo','Recurso'));self.registrar(iid,(slug,path,(campo,i)),grupo,titulo+' / '+nome+' / '+texto)
     if campo!='personagens':self.inserir(iid,grupo,texto,self.referencias[iid])
   estrutura=raiz+':estrutura';self.registrar(estrutura,(slug,path,()),raiz,titulo+' / Estrutura da obra');self.inserir(estrutura,raiz,'Estrutura da obra',self.referencias[estrutura],aberto=primeiro or estrutura in abertos)
   lista=list(hier.nos(arvore));indice={no.id:no for no in lista};contagens={no.id:0 for no in lista};mostrar=set()
   for no in lista:
    if no.tipo=='capitulo':
     total+=1;pai=no.pai
     while pai:contagens[pai]+=1;pai=indice[pai].pai
     ids=[no.id];ancestral=no.pai
     while ancestral:ids.append(ancestral);ancestral=indice[ancestral].pai
     texto=' '.join([*no.nomes,*ids,str(no.item.get('numero',''))])
     if (not termo or termo in hier.normalizar(texto)) and (self.filtro.get()=='Todos' or self.filtro.get()==no.item['estado_publicacao']):
      visiveis+=1;mostrar.add(no.id);pai=no.pai
      while pai:mostrar.add(pai);pai=indice[pai].pai
   if not ativo:mostrar.update(indice)
   elif self.filtro.get()=='Todos':
    for no in lista:
     if no.tipo!='capitulo' and termo in hier.normalizar(' '.join([*no.nomes,no.id])):
      mostrar.add(no.id);pai=no.pai
      while pai:mostrar.add(pai);pai=indice[pai].pai
   for no in lista:
    iid='editorial:'+slug+':'+no.id;pai='editorial:'+slug+':'+no.pai if no.pai else estrutura
    descr=(slug,f'{slug}/dados/editorial.json',no.caminho);self.nos[iid]=no;self.registrar(iid,descr,pai,titulo+' / '+no.endereco+' · '+' / '.join(no.nomes))
    if no.tipo=='capitulo':
     filhos=[(iid+':html','Texto HTML',(slug,f'{slug}/{no.item["arquivo"]}',None))]
     for campo,nome in [('cenas','Cena'),('notas','Nota')]:
      for j,item in enumerate(no.item.get(campo,[])):
       filhos.append((iid+':'+campo+':'+item['id'],item.get('titulo_cena',item.get('titulo',nome)),(slug,descr[1],no.caminho+(campo,j))))
     for chave,texto,ref in filhos:self.registrar(chave,ref,iid,self.caminhos[iid]+' / '+texto)
     self.pendentes[iid]=filhos
    if no.id not in mostrar:continue
    texto=no.titulo if no.tipo=='capitulo' else no.tipo.capitalize()+' · '+no.titulo+f' ({contagens[no.id]} caps)'
    numero=str(no.item.get('numero','')).strip()
    if no.tipo=='capitulo' and numero:texto=numero+' · '+texto
    self.inserir(iid,pai,texto,descr,no.endereco,no.item.get('estado_publicacao',''),aberto=iid in abertos or ativo and no.tipo!='capitulo')
    if no.tipo=='capitulo':
     if iid in abertos:self.materializar(iid)
     else:self.tree.insert(iid,'end',iid=iid+':pendente',text='Expandir para texto, cenas e notas')
   if ativo:self.tree.item(raiz,open=True);self.tree.item(estrutura,open=True)
  self.resumo.set(f'{visiveis} de {total} capítulos' if ativo else f'{total} capítulos · ordem editorial')
  if atual and self.tree.exists(atual):self.tree.selection_set(atual);self.tree.focus(atual)
  elif atual and self.pais.get(atual) in self.pendentes and self.tree.exists(self.pais[atual]):
   self.materializar(self.pais[atual]);self.tree.selection_set(atual);self.tree.focus(atual)
  self.tree.yview_moveto(y)
 def materializar(self,iid):
  filhos=self.pendentes.get(iid)
  if filhos is None:return
  for chave in self.tree.get_children(iid):self.tree.delete(chave)
  for chave,texto,descr in filhos:self.inserir(chave,iid,texto,descr)
  # `itens` é partilhado com o Studio; não substituir durante expansão.
  self.pendentes.pop(iid,None)
 def abrir(self,event=None):self.materializar(self.tree.focus())
 def revelar(self,iid):
  if not self.tree.exists(iid) and ':personagens:' in iid:iid=self.pais.get(iid,iid)
  cadeia=[];alvo=iid
  while alvo:
   cadeia.append(alvo);alvo=self.pais.get(alvo,'')
  for alvo in reversed(cadeia):
   pai=self.pais.get(alvo)
   if not self.tree.exists(alvo) and pai and self.tree.exists(pai):self.materializar(pai)
   if self.tree.exists(alvo):self.tree.item(alvo,open=True)
  if self.tree.exists(iid):
   self.materializar(iid);self.tree.selection_set(iid);self.tree.focus(iid);self.tree.see(iid)

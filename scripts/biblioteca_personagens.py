"""Biblioteca de personagens como página persistente da janela de gestão."""
import tkinter as tk
from tkinter import ttk
from hierarquia import normalizar
from personagens import validar_catalogo,indice_participacoes

class BibliotecaPersonagens(ttk.Frame):
 def __init__(self,parent,projeto,abrir,criar,excluir):
  super().__init__(parent,padding=18);self.projeto=projeto;self.slug=None;self.abrir=abrir;self.criar=criar;self.excluir=excluir;self.catalogo={};self.contagens={}
  self.titulo=tk.StringVar(value='Biblioteca de personagens');ttk.Label(self,textvariable=self.titulo,font=('Georgia',21)).pack(anchor='w')
  ttk.Label(self,text='Clique em um personagem para abrir sua ficha de metadados. IDs mantêm os vínculos mesmo após renomeações.',wraplength=700).pack(anchor='w',pady=8)
  barra=ttk.Frame(self);barra.pack(fill='x',pady=8)
  barra.columnconfigure(0,weight=1);barra.columnconfigure(1,weight=1)
  for i,(texto,cmd) in enumerate([('Novo personagem…',lambda:self.criar()),('Abrir ficha',self.abrir_selecionado),('Excluir personagem…',self.excluir_selecionado),('Atualizar',lambda:self.atualizar())]):ttk.Button(barra,text=texto,command=cmd).grid(row=i//2,column=i%2,sticky='ew',padx=(0,5),pady=3)
  self.busca=tk.StringVar();ttk.Label(self,text='Buscar por nome, apelido ou identidade').pack(anchor='w');ttk.Entry(self,textvariable=self.busca).pack(fill='x',pady=(4,12))
  quadro=ttk.Frame(self);quadro.pack(fill='both',expand=True);quadro.rowconfigure(0,weight=1);quadro.columnconfigure(0,weight=1)
  self.lista=ttk.Treeview(quadro,show='tree headings',columns=('apelidos','descricao','capitulos','id'),selectmode='browse')
  for coluna,nome,largura in [('#0','Personagem',190),('apelidos','Apelidos',150),('descricao','Apresentação',240),('capitulos','Capítulos associados',145),('id','Identidade permanente',240)]:self.lista.heading(coluna,text=nome);self.lista.column(coluna,width=largura,minwidth=65,stretch=coluna in ('#0','descricao'))
  y=ttk.Scrollbar(quadro,orient='vertical',command=self.lista.yview);x=ttk.Scrollbar(quadro,orient='horizontal',command=self.lista.xview);self.lista.configure(yscrollcommand=y.set,xscrollcommand=x.set)
  self.lista.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew')
  self.resumo=tk.StringVar();ttk.Label(self,textvariable=self.resumo,wraplength=700).pack(anchor='w',pady=10)
  self.busca.trace_add('write',lambda *args:self.filtrar());self.lista.bind('<ButtonRelease-1>',self.clicar);self.lista.bind('<Return>',lambda e:self.abrir_selecionado())
 def atualizar(self,slug=None):
  if slug is not None and slug!=self.slug:self.busca.set('')
  self.slug=slug or self.slug
  if not self.slug:return
  info,_=self.projeto.ler(f'{self.slug}/dados/info-obra.json');arvore,_=self.projeto.ler(f'{self.slug}/dados/editorial.json')
  self.catalogo=validar_catalogo(info);indice=indice_participacoes(arvore);self.contagens={ident:len({r['capitulo'] for r in indice.get(ident,[])}) for ident in self.catalogo}
  self.titulo.set('Personagens — '+info['titulo']);self.filtrar()
 def filtrar(self):
  anterior=self.lista.selection();self.lista.delete(*self.lista.get_children());termo=normalizar(self.busca.get())
  for p in sorted(self.catalogo.values(),key=lambda p:(normalizar(p['nome']),p['id'])):
   if termo not in normalizar(' '.join([p['nome'],p['id'],*p.get('aliases',[])])):continue
   self.lista.insert('','end',iid=p['id'],text=p['nome'],values=(', '.join(p.get('aliases',[])),p.get('descricao_curta',''),self.contagens[p['id']],p['id']))
  if anterior and self.lista.exists(anterior[0]):self.lista.selection_set(anterior[0]);self.lista.focus(anterior[0])
  n=len(self.lista.get_children());self.resumo.set(f'{n} de {len(self.catalogo)} personagens. Enter também abre a ficha.' if self.catalogo else 'Nenhum personagem cadastrado. Use Novo personagem para começar.')
 def clicar(self,event):
  iid=self.lista.identify_row(event.y)
  if iid and self.lista.identify_region(event.x,event.y) in {'tree','cell'}:
   self.lista.selection_set(iid);self.lista.focus(iid);self.abrir_selecionado()
 def abrir_selecionado(self):
  sel=self.lista.selection()
  if sel:self.abrir(self.slug,sel[0])
 def excluir_selecionado(self):
  sel=self.lista.selection()
  if sel:self.excluir(self.slug,sel[0])

"""Biblioteca de obras com busca, filtros e ações na janela do Studio."""
import tkinter as tk
from tkinter import ttk
from hierarquia import normalizar

class BibliotecaObras(ttk.Frame):
 def __init__(self,parent,projeto,acoes):
  super().__init__(parent,padding=18);self.projeto=projeto;self.acoes=acoes;self.obras=[]
  ttk.Label(self,text='Biblioteca de obras',font=('Georgia',23)).pack(anchor='w')
  ttk.Label(self,text='Organize suas publicações e seus projetos em elaboração. Selecione uma obra para gerenciar seus metadados.',wraplength=690).pack(anchor='w',pady=8)
  barra=ttk.Frame(self);barra.pack(fill='x')
  for i,(nome,acao) in enumerate([('Nova obra…','nova'),('Abrir metadados','abrir'),('Arquivar / voltar a rascunho…','estado'),('Exportar fontes…','exportar'),('Excluir com recuperação…','excluir'),('Restaurar obra…','restaurar')]):
   ttk.Button(barra,text=nome,command=lambda a=acao:self.executar(a)).grid(row=i//2,column=i%2,sticky='ew',padx=(0,5),pady=3)
  barra.columnconfigure(0,weight=1);barra.columnconfigure(1,weight=1)
  filtros=ttk.Frame(self);filtros.pack(fill='x',pady=12);filtros.columnconfigure(0,weight=1)
  self.busca=tk.StringVar();self.estado=tk.StringVar(value='Todas')
  ttk.Label(filtros,text='Buscar título, autor, endereço ou identidade').grid(row=0,column=0,sticky='w')
  ttk.Entry(filtros,textvariable=self.busca).grid(row=1,column=0,sticky='ew',padx=(0,7))
  ttk.Combobox(filtros,textvariable=self.estado,values=['Todas','rascunho','publicado','arquivado'],state='readonly',width=13).grid(row=1,column=1)
  ttk.Button(filtros,text='Atualizar',command=self.atualizar).grid(row=1,column=2,padx=4)
  quadro=ttk.Frame(self);quadro.pack(fill='both',expand=True);quadro.columnconfigure(0,weight=1);quadro.rowconfigure(0,weight=1)
  self.lista=ttk.Treeview(quadro,columns=('autor','estado','andamento','capitulos','personagens','slug'),show='tree headings',selectmode='browse')
  for col,titulo,largura in [('#0','Obra',220),('autor','Autor',150),('estado','Publicação',100),('andamento','Andamento',120),('capitulos','Capítulos / públicos',150),('personagens','Personagens',110),('slug','Endereço',180)]:self.lista.heading(col,text=titulo);self.lista.column(col,width=largura,minwidth=80,stretch=col=='#0')
  y=ttk.Scrollbar(quadro,orient='vertical',command=self.lista.yview);x=ttk.Scrollbar(quadro,orient='horizontal',command=self.lista.xview);self.lista.configure(yscrollcommand=y.set,xscrollcommand=x.set)
  self.lista.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew')
  self.resumo=tk.StringVar();ttk.Label(self,textvariable=self.resumo,wraplength=690).pack(anchor='w',pady=10)
  self.busca.trace_add('write',lambda *a:self.filtrar());self.estado.trace_add('write',lambda *a:self.filtrar())
  self.lista.bind('<Double-1>',self.duplo_clique);self.lista.bind('<Return>',lambda e:self.executar('abrir'))
 def atualizar(self):
  self.obras=self.projeto.biblioteca_obras();self.filtrar()
 def filtrar(self):
  selecionado=self.lista.selection();self.lista.delete(*self.lista.get_children());termo=normalizar(self.busca.get())
  for o in self.obras:
   p=o['info'];slug=o['slug']
   if termo not in normalizar(' '.join([p['titulo'],p['autor'],slug,p['id_obra']])):continue
   if self.estado.get()!='Todas' and self.estado.get()!=p['estado_publicacao']:continue
   self.lista.insert('','end',iid=slug,text=p['titulo'],values=(p['autor'],p['estado_publicacao'],p['estado_obra'],f"{o['capitulos']} / {o['publicados']}",o['personagens'],slug))
  if selecionado and self.lista.exists(selecionado[0]):self.lista.selection_set(selecionado[0])
  self.resumo.set(f'{len(self.lista.get_children())} de {len(self.obras)} obras. Duplo clique ou Enter abre a ficha. Exclusões podem ser restauradas; gere o site para atualizar a saída local.')
 def duplo_clique(self,event):
  if self.lista.identify_row(event.y) and self.lista.identify_region(event.x,event.y) in {'tree','cell'}:self.executar('abrir')
 def executar(self,acao):
  if acao in {'nova','restaurar'}:self.acoes[acao]();return
  selecionado=self.lista.selection()
  if not selecionado:self.resumo.set('Selecione uma obra na lista antes de continuar.');return
  self.acoes[acao](selecionado[0])

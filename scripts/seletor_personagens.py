"""Seletor visual que exibe nomes, mas devolve IDs permanentes."""
import tkinter as tk
from tkinter import ttk
from hierarquia import normalizar

class SeletorPersonagens(ttk.Frame):
 def __init__(self,parent,personagens,selecionados=(),multiplo=True):
  super().__init__(parent);self.catalogo={p['id']:p for p in personagens};self.ordem=list(dict.fromkeys(selecionados));self.selecionados=set(self.ordem);self.visiveis=[];self.multiplo=multiplo;self._atualizando=False
  self.busca=tk.StringVar();ttk.Entry(self,textvariable=self.busca).pack(fill='x')
  quadro=ttk.Frame(self);quadro.pack(fill='both',expand=True,pady=4)
  self.lista=tk.Listbox(quadro,selectmode='multiple' if multiplo else 'browse',exportselection=False,height=6)
  scroll=ttk.Scrollbar(quadro,orient='vertical',command=self.lista.yview);scroll.pack(side='right',fill='y');horizontal=ttk.Scrollbar(quadro,orient='horizontal',command=self.lista.xview);horizontal.pack(side='bottom',fill='x');self.lista.configure(yscrollcommand=scroll.set,xscrollcommand=horizontal.set);self.lista.pack(fill='both',expand=True)
  self.resumo=tk.StringVar();ttk.Label(self,textvariable=self.resumo,wraplength=580).pack(anchor='w')
  ttk.Button(self,text='Limpar seleção',command=lambda:self.selecionar([])).pack(anchor='w',pady=3)
  self.lista.bind('<<ListboxSelect>>',self.alterar);self.busca.trace_add('write',lambda *a:self.filtrar());self.filtrar()
 def filtrar(self):
  self._atualizando=True
  try:
   termo=normalizar(self.busca.get());self.lista.delete(0,'end');self.visiveis=[]
   itens=sorted(self.catalogo.values(),key=lambda p:(normalizar(p['nome']),p['id']))
   itens += [{'id':ident,'nome':'Referência ausente'} for ident in self.ordem if ident not in self.catalogo]
   for p in itens:
    if termo not in normalizar(' '.join([p['nome'],p['id'],*p.get('aliases',[])])):continue
    label=p['nome']+' — '+p['id']
    if p.get('aliases'):label+=' · '+', '.join(p['aliases'])
    self.visiveis.append(p['id']);self.lista.insert('end',label)
    if p['id'] in self.selecionados:self.lista.selection_set(len(self.visiveis)-1)
   self._resumo()
  finally:self._atualizando=False
 def alterar(self,event=None):
  if self._atualizando:return
  escolhidos={self.visiveis[i] for i in self.lista.curselection()}
  if self.multiplo:self.selecionados.difference_update(self.visiveis);self.selecionados.update(escolhidos)
  elif escolhidos:self.selecionados=escolhidos
  self._resumo()
 def _resumo(self):
  nomes=[self.catalogo[x]['nome'] if x in self.catalogo else 'Referência ausente: '+x for x in self.ids()]
  self.resumo.set('Selecionados: '+', '.join(nomes) if nomes else 'Nenhum personagem selecionado. Busque por nome, apelido ou ID.' if self.catalogo else 'Nenhum personagem cadastrado nesta obra. Use Personagens para criar o cadastro.')
 def ids(self):return [x for x in dict.fromkeys([*self.ordem,*self.catalogo,*sorted(self.selecionados)]) if x in self.selecionados]
 def get(self):return '\n'.join(self.ids())
 def selecionar(self,ids):
  self.selecionados=set(ids);self.ordem=list(dict.fromkeys([*self.ordem,*ids]));self.filtrar()

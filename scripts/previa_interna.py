"""Prévia textual da publicação na própria janela, sem executar HTML ou scripts."""
from html.parser import HTMLParser
from rolagem import TextoRolavel
import json
import tkinter as tk
from tkinter import ttk
class Leitura(HTMLParser):
 def __init__(self,widget):super().__init__();self.widget=widget;self.oculto=0;self.tags=[]
 def handle_starttag(self,t,a):
  if t in ('script','style'):self.oculto+=1;return
  if self.oculto:return
  if t in ('p','h1','h2','h3','section','details','li','hr'):self.widget.insert('end','\n\n')
  if t in ('h1','h2','h3','strong','b','em','i'):self.tags.append(t)
  if t=='br':self.widget.insert('end','\n')
  if t=='img':self.widget.insert('end','[Imagem: '+dict(a).get('alt','sem descrição')+']')
 def handle_endtag(self,t):
  if t in ('script','style'):self.oculto=max(0,self.oculto-1)
  if t in self.tags:self.tags.remove(t)
 def handle_data(self,d):
  if not self.oculto:self.widget.insert('end',d,tuple(self.tags))
class Previa(ttk.Frame):
 def __init__(self,parent,root,abrir_browser):
  super().__init__(parent,padding=18);self.root_projeto=root
  ttk.Label(self,text='Prévia de leitura da última geração',font=('Georgia',20)).pack(anchor='w')
  ttk.Label(self,text='Texto e estrutura dentro do Studio. Para conferir CSS, responsividade e interações, abra o site no navegador.',wraplength=700).pack(anchor='w',pady=10)
  barra=ttk.Frame(self);barra.pack(fill='x')
  self.seletor=ttk.Combobox(barra,state='readonly',width=65);self.seletor.pack(side='left',fill='x',expand=True);self.seletor.bind('<<ComboboxSelected>>',lambda e:self.abrir())
  ttk.Button(barra,text='Atualizar',command=self.atualizar).pack(side='left',padx=5);ttk.Button(barra,text='Conferir site no navegador',command=abrir_browser).pack(side='left')
  self.texto=TextoRolavel(self,wrap='word',font=('Georgia',14),background='#fffdf9',foreground='#29312b',padx=30,pady=25);self.texto.pack(fill='both',expand=True,pady=15)
  for t in ('h1','h2','h3'):self.texto.tag_configure(t,font=('Georgia',22,'bold'))
  for t in ('strong','b'):self.texto.tag_configure(t,font=('Georgia',14,'bold'))
  for t in ('em','i'):self.texto.tag_configure(t,font=('Georgia',14,'italic'))
  self.atualizar()
 def atualizar(self):
  self.arquivos=[];nomes=[];site=self.root_projeto/'site'
  if not (site/'catalogo.json').is_file():return
  for obra in json.loads((site/'catalogo.json').read_text()):
   base=site/obra.get('slug',obra['id_obra']);tree=json.loads((base/'dados/estrutura.json').read_text())
   for s in tree['sagas']:
    for v in s['volumes']:
     for a in v['arcos']:
      for c in a['capitulos']:nomes.append(obra['titulo']+' / '+c['titulo']);self.arquivos.append(base/c['arquivo'])
  self.seletor['values']=nomes
  if nomes:self.seletor.current(0);self.abrir()
 def abrir(self):
  i=self.seletor.current()
  if i<0:return
  self.texto.configure(state='normal');self.texto.delete('1.0','end');Leitura(self.texto).feed(self.arquivos[i].read_text());self.texto.configure(state='disabled')

"""Roteamento único da roda: widget sob o mouse, depois o contêiner ancestral."""
import tkinter as tk
from tkinter import ttk
class TextoRolavel(tk.Text):
 def __init__(self,parent,**kw):
  self.container=ttk.Frame(parent)
  super().__init__(self.container,**kw);self.container._roda_alvo=self
  barra=ttk.Scrollbar(self.container,orient='vertical',command=self.yview);barra.pack(side='right',fill='y');self.configure(yscrollcommand=barra.set)
  if kw.get('wrap')=='none':
   horizontal=ttk.Scrollbar(self.container,orient='horizontal',command=self.xview);horizontal.pack(side='bottom',fill='x');self.configure(xscrollcommand=horizontal.set)
 def pack(self,**kw):
  self.container.pack(**kw);super().pack(side='left',fill='both',expand=True)

def instalar(root):
 tag='LiteratureWheel'+str(id(root))
 def registrar(event=None):
  def visitar(w):
   tags=w.bindtags()
   if tag not in tags:w.bindtags((tag,)+tags)
   for filho in w.winfo_children():visitar(filho)
  try:visitar(event.widget if event else root)
  except (tk.TclError,AttributeError):pass
 def rolar(event):
  num=getattr(event,'num',None);delta=getattr(event,'delta',0)
  if num==4:passos=-3
  elif num==5:passos=3
  elif delta:passos=-int(delta/120)*3 if abs(delta)>=120 else (-1 if delta>0 else 1)
  else:return
  eixo='x' if getattr(event,'state',0)&1 else 'y'
  w=event.widget
  while w is not None:
   alvo=getattr(w,'_roda_alvo',w)
   view=getattr(alvo,eixo+'view',None)
   if callable(view):
    try:
     inicio,fim=map(float,view())
     if (passos<0 and inicio>0.00001) or (passos>0 and fim<0.99999):
      getattr(alvo,eixo+'view_scroll')(passos,'units');return 'break'
    except (tk.TclError,TypeError,ValueError):pass
   w=getattr(w,'master',None)
  # Não deixa a roda alterar uma escolha de combo ao tentar rolar o formulário.
  return 'break'
 for seq in ('<MouseWheel>','<Button-4>','<Button-5>','<Shift-MouseWheel>','<Shift-Button-4>','<Shift-Button-5>'):root.bind_class(tag,seq,rolar)
 root.bind('<Map>',registrar,add='+');registrar()
 root._roteador_roda=rolar
 return rolar

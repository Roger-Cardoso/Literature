"""Reproduz roda sobre filhos e áreas aninhadas somente em cópia temporária."""
import sys,shutil,tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gerenciador_visual import Studio
from editor_componente import modulo,OverlayPanel,SemanticWidget
from rolagem import TextoRolavel
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto
from fixture_projeto import preparar_fixture
temporario=tempfile.TemporaryDirectory();destino=Path(temporario.name)/'projeto'
shutil.copytree(Path(__file__).resolve().parents[1],destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.git','.agents','.aws','.codex','.literature-backups','.literature-lixeira','__pycache__','site'))
preparar_fixture(destino)
from gerar_site import gerar
gerar(destino)
gv.ROOT=integ.ROOT=destino;gv.Projeto=integ.Projeto=lambda:Projeto(destino)
app=Studio();app.update()
def roda(w):
 w.event_generate('<Button-5>');app.update()
try:
 desc=next(d for d in app.itens.values() if d[2]==())
 app.carregar(desc);app.update();app.canvas.yview_moveto(0);app.update()
 antes=app.canvas.yview()[0];roda(app.widgets['titulo']);assert app.canvas.yview()[0]>antes,'Formulário sobre Entry'
 texto=app.widgets['sinopse'];texto.insert('end','\nLinha'*300);app.update();texto.yview_moveto(0);roda(texto);assert texto.yview()[0]>0,'Texto aninhado'
 texto.yview_moveto(1);app.canvas.yview_moveto(0);app.update();roda(texto);assert app.canvas.yview()[0]>0,'Propagação no limite do texto'
 painel=OverlayPanel(app,'Teste de painel rolável',scrollable=True,width=650,height=450)
 labels=[]
 for i in range(120):
  label=ttk.Label(painel.body,text='Campo '+str(i));label.pack();labels.append(label)
 app.update();painel.body_scroll.canvas.yview_moveto(0);app.update();roda(labels[0]);assert painel.body_scroll.canvas.yview()[0]>0,'Painel sobre Label'
 painel.close();app.update()
 painel=OverlayPanel(app,'Revisão longa',width=650,height=450)
 texto=TextoRolavel(painel.body,wrap='none');texto.pack(fill='both',expand=True);texto.insert('1.0','\n'.join('Linha de comparação '+str(i) for i in range(400)));texto.configure(state='disabled');app.update();roda(texto);assert texto.yview()[0]>0,'Texto de revisão desabilitado'
 texto.configure(state='normal');texto.insert('end','X'*1000);texto.configure(state='disabled');texto.see('end');app.update();texto.xview_moveto(0);texto.event_generate('<Button-5>',state=1);app.update();assert texto.xview()[0]>0,'Rolagem horizontal da comparação';painel.close()
 app.base=app.valor()
 aba=ttk.Frame(app.abas);app.abas.add(aba,text='Teste editor');app.abas.select(aba)
 ed=SemanticWidget(aba);ed.pack(fill='both',expand=True);app.update()
 ed.text.insert('1.0','\n'.join('Parágrafo '+str(i) for i in range(600)));app.update();ed.text.yview_moveto(0);roda(ed.text);assert ed.text.yview()[0]>0,'Texto do editor semântico'
 def buscar(w):
  if isinstance(w,modulo.ScrollableFrame):return w
  for filho in w.winfo_children():
   achado=buscar(filho)
   if achado:return achado
 sidebar=buscar(ed)
 for i in range(80):ttk.Label(sidebar.content,text='Recurso '+str(i)).pack()
 app.update();sidebar.canvas.yview_moveto(0);app.update();roda(sidebar.content.winfo_children()[-1]);assert sidebar.canvas.yview()[0]>0,'Barra lateral semântica'
 ed.destroy();app.abas.forget(aba);aba.destroy()
 app.previa();app.update();prev=app.aba_previa.texto;prev.configure(state='normal');prev.insert('end','\nPrévia'*500);prev.configure(state='disabled');app.update();prev.yview_moveto(0);roda(prev);assert prev.yview()[0]>0,'Prévia interna'
 app.abas.select(app.aba_dados);app.update()
 app.tree.delete(*app.tree.get_children())
 for i in range(300):app.tree.insert('','end',text=str(i))
 app.update();app.tree.yview_moveto(0);roda(app.tree);assert app.tree.yview()[0]>0,'Árvore de navegação'
 print('OK: roda no formulário, texto aninhado, propagação, painel interno, revisão somente leitura árvore, editor semântico, barra lateral e prévia.')
finally:app.destroy();temporario.cleanup()

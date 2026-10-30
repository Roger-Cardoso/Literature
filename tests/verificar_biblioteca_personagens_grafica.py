"""Navegação árvore → biblioteca → ficha e CRUD, exclusivamente em cópia temporária."""
from pathlib import Path
import sys,shutil,tempfile
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(root,destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.git','.agents','.codex','.aws','__pycache__','.literature-backups'))
 from fixture_projeto import preparar_fixture;preparar_fixture(destino)
 gv.ROOT=integ.ROOT=destino;gv.Projeto=integ.Projeto=lambda:Projeto(destino);p=Projeto(destino)
 app=gv.Studio();app.update()
 try:
  grupo='obra:obra-1:personagens';app.tree.selection_set(grupo);app.tree.focus(grupo);app.update()
  biblioteca=app.biblioteca_personagens
  assert app.abas.select()==str(biblioteca) and app.tree.get_children(grupo)==()
  catalogo=p.ler('obra-1/dados/info-obra.json')[0]['personagens'];assert set(biblioteca.lista.get_children())=={x['id'] for x in catalogo}
  canon=catalogo[0]['id'];biblioteca.lista.see(canon);app.update();box=biblioteca.lista.bbox(canon)
  biblioteca.lista.event_generate('<ButtonRelease-1>',x=10,y=box[1]+5);app.update()
  assert app.obj['id']==canon and app.abas.select()==str(app.aba_dados),'Um clique deve abrir a ficha'
  assert not app.tree.exists('obra:obra-1:personagens:'+canon),'Não criar nó individual ao abrir ficha'
  # Cancelar saída da ficha mantém os metadados em edição.
  app.widgets['nome'].insert('end',' pendente');ask=gv.messagebox.askyesnocancel;gv.messagebox.askyesnocancel=lambda *a,**k:None
  try:app.gerenciar_personagens()
  finally:gv.messagebox.askyesnocancel=ask
  assert app.abas.select()==str(app.aba_dados) and app.widgets['nome'].get().endswith(' pendente')
  app.widgets['nome'].delete(0,'end');app.widgets['nome'].insert(0,'Nome editado na ficha');assert app.salvar();app.update()
  app.gerenciar_personagens();app.update();assert biblioteca.lista.item(canon,'text')=='Nome editado na ficha'
  # CRUD: criação abre a ficha, exclusão revisada retorna à biblioteca.
  biblioteca.criar();app.update();painel=app.overlay_stack[-1]
  next(w for w in painel.body.winfo_children() if w.winfo_class()=='TEntry').insert(0,'Personagem temporário')
  next(w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)).invoke();app.update()
  novo=app.obj['id'];assert app.obj['nome']=='Personagem temporário' and app.abas.select()==str(app.aba_dados)
  assert app.tree.get_children(grupo)==() and not app.tree.exists('obra:obra-1:personagens:'+novo)
  # Clicar novamente no grupo já selecionado volta à biblioteca.
  app.tree.see(grupo);app.update();box=app.tree.bbox(grupo);app.tree.event_generate('<ButtonRelease-1>',x=box[0]+20,y=box[1]+5);app.update()
  assert app.abas.select()==str(biblioteca) and biblioteca.lista.exists(novo)
  biblioteca.lista.selection_set(novo);biblioteca.excluir_selecionado();app.update();painel=app.overlay_stack[-1]
  next(w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)).invoke();app.update()
  assert not biblioteca.lista.exists(novo) and app.abas.select()==str(biblioteca)
  assert novo not in {x['id'] for x in p.ler('obra-1/dados/info-obra.json')[0]['personagens']}
  assert list((destino/'.literature-backups').rglob('info-obra.json'))
  # Participação existente impede exclusão e mantém o cadastro.
  arvore,rev=p.ler('obra-1/dados/editorial.json');next(c for _,c in p.capitulos(arvore))['personagens_ids']=[canon];p.organizar('obra-1',arvore,rev)
  app.excluir_personagem('obra-1',canon);app.update();painel=app.overlay_stack[-1]
  assert not any(isinstance(w,ttk.Button) for w in painel.footer.winfo_children()),'Exclusão de personagem em uso deve ficar bloqueada'
  painel.close();assert canon in {x['id'] for x in p.ler('obra-1/dados/info-obra.json')[0]['personagens']}
  # Uma linha desatualizada não pode abrir a ficha de outro personagem.
  biblioteca.lista.insert('','end',iid='removido',text='Registro antigo');biblioteca.lista.selection_set('removido')
  erros=[];mostrar=gv.messagebox.showerror;gv.messagebox.showerror=lambda *a,**k:erros.append(a)
  try:biblioteca.abrir_selecionado()
  finally:gv.messagebox.showerror=mostrar
  app.update();assert erros and app.abas.select()==str(biblioteca) and not biblioteca.lista.exists('removido')
  print('OK: árvore sem personagens filhos; biblioteca única; clique simples → ficha; cancelamento preserva edição; criar, editar e excluir com backup; bloqueio de personagem em uso.')
 finally:app.destroy()

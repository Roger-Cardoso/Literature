"""Fluxo completo de obras em janela real, sempre em cópia temporária."""
from pathlib import Path
import shutil,sys,tempfile
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(ROOT,destino,ignore=shutil.ignore_patterns('.git','.agents','.codex','.aws','__pycache__','.literature-backups','.literature-lixeira','site'))
 from fixture_projeto import preparar_fixture;preparar_fixture(destino)
 gv.ROOT=integ.ROOT=destino;gv.Projeto=integ.Projeto=lambda:Projeto(destino);p=Projeto(destino)
 app=gv.Studio();app.update()
 def botao(w,texto):
  for c in w.winfo_children():
   if isinstance(c,ttk.Button) and c.cget('text')==texto:return c
   achado=botao(c,texto)
   if achado:return achado
 def entradas(painel):return [w for w in painel.body.winfo_children() if isinstance(w,ttk.Entry)]
 try:
  app.gerenciar_obras();app.update();b=app.biblioteca_obras;assert set(b.lista.get_children())==set(p.obras())
  app.gerenciar_obras();app.update();assert len([x for x in app.abas.tabs() if x==str(b)])==1
  app.nova_obra();app.update();painel=app.overlay_stack[-1]
  for campo,valor in zip(entradas(painel),['Teste de biblioteca','Autor de teste','teste-biblioteca']):campo.insert(0,valor)
  botao(painel.footer,'Criar obra').invoke();app.update();slug='teste-biblioteca'
  assert app.atual==(slug,f'{slug}/dados/info-obra.json',()) and app.obj['titulo']=='Teste de biblioteca'
  original=app.widgets['titulo'].get();app.widgets['titulo'].delete(0,'end');erro=gv.messagebox.showerror;gv.messagebox.showerror=lambda *a,**k:None
  try:assert not app.salvar()
  finally:gv.messagebox.showerror=erro
  assert p.ler(f'{slug}/dados/info-obra.json')[0]['titulo']==original and app.obj['titulo']==original
  app.widgets['titulo'].insert(0,original)
  ident=app.obj['id_obra'];app.widgets['titulo'].delete(0,'end');app.widgets['titulo'].insert(0,'Nome editado');assert app.salvar();app.update()
  app.gerenciar_obras();app.update();assert b.lista.item(slug,'text')=='Nome editado'
  b.busca.set('autor de teste');app.update();assert b.lista.get_children()==(slug,);b.busca.set('');b.estado.set('rascunho');app.update();assert b.lista.exists(slug)
  # Arquivamento exige revisão e mantém a identidade e o conteúdo.
  app.estado_obra(slug);app.update();painel=app.overlay_stack[-1];botao(painel.footer,'Confirmar com backup').invoke();app.update()
  assert p.ler(f'{slug}/dados/info-obra.json')[0]['estado_publicacao']=='arquivado';b.estado.set('arquivado');app.update();assert b.lista.exists(slug)
  # Exporta fontes, não um pacote público.
  dialog=gv.filedialog.asksaveasfilename;pacote=Path(tmp)/'fontes.zip';gv.filedialog.asksaveasfilename=lambda **k:str(pacote)
  try:app.exportar_fontes_obra(slug)
  finally:gv.filedialog.asksaveasfilename=dialog
  assert pacote.is_file()
  # Editor vivo é fechado somente após confirmação de exclusão.
  tree,rev=p.ler(f'{slug}/dados/editorial.json');cap=p.novo_capitulo(slug,'Capítulo inicial',tree,rev)
  app.inventario(foco='editorial:'+slug+':'+cap);app.editor_semantico();app.update();assert app.editor.vinculo['slug']==slug
  if app.editor.dirty:assert app.editor.save_project()
  autoria=app.editor.project_path;assert autoria and autoria.is_file();bytes_autoria=autoria.read_bytes()
  app.gerenciar_obras();app.update();app.excluir_obra(slug);app.update();painel=app.overlay_stack[-1]
  entradas(painel)[0].insert(0,'errado');botao(painel.footer,'Excluir e guardar para recuperação').invoke();app.update();assert slug in p.obras()
  entradas(painel)[0].delete(0,'end');entradas(painel)[0].insert(0,slug);botao(painel.footer,'Excluir e guardar para recuperação').invoke();app.update()
  assert slug not in p.obras() and app.editor is None and not app.tree.exists('obra:'+slug) and app.atual is None
  assert app.abas.select()==str(b) and not b.lista.exists(slug)
  app.restaurar_obra();app.update();painel=app.overlay_stack[-1];botao(painel.body,'Restaurar como rascunho').invoke();app.update()
  info,_=p.ler(f'{slug}/dados/info-obra.json');assert info['id_obra']==ident and info['estado_publicacao']=='rascunho';assert autoria.read_bytes()==bytes_autoria
  assert app.atual[0]==slug and app.tree.exists('obra:'+slug)
  # Cancelar navegação mantém os dados não salvos e não muda a aba.
  app.widgets['titulo'].insert('end',' pendente');ask=gv.messagebox.askyesnocancel;gv.messagebox.askyesnocancel=lambda *a,**k:None
  try:app.gerenciar_obras()
  finally:gv.messagebox.askyesnocancel=ask
  assert app.abas.select()==str(app.aba_dados) and app.widgets['titulo'].get().endswith(' pendente')
  print('OK: biblioteca única; criação e ficha; edição; busca e filtro; arquivamento; exportação; exclusão confirmada com editor aberto; limpeza de sessão; restauração de IDs e autoria; cancelamento sem perda.')
 finally:app.destroy()

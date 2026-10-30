"""Teste gráfico isolado. Execute em sessão de desktop; não modifica as obras reais."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto'
 shutil.copytree(root,destino,ignore=shutil.ignore_patterns('.git','.agents','.aws','.codex','__pycache__','.literature-backups','.unilit-build-*'))
 from fixture_projeto import preparar_fixture;preparar_fixture(destino)
 gv.ROOT=integ.ROOT=destino
 gv.Projeto=integ.Projeto=lambda:Projeto(destino)
 app=gv.Studio();app.update_idletasks()
 try:
  descr=next(d for d in app.itens.values() if d[0]=='obra-1' and d[2] is not None and d[1].endswith('editorial.json') and len(d[2])==8)
  app.carregar(descr);app.editor_semantico();app.update_idletasks();ed=app.editor
  assert ed.winfo_toplevel() is app and ed.master is app.aba_editor
  assert len(ed.entities)>=2
  cap=app.obj
  assert ed.text.get('1.0','end-1c').strip(),'Capítulo não deve abrir vazio'
  legado=ed.project_data();legado['sections']=[];ed.load_project_data(legado)
  ed.recuperar_cenas_exatas(cap)
  assert {s['id'] for s in ed.project_data()['sections']} >= {c['ancora'] for c in cap['cenas']},'Recuperação da autoria antiga sem cenas'
  ed.notify=lambda *a,**k:None
  ed.text.insert('end','\nTexto de verificação adicionado.')
  ed.revisar();app.update_idletasks();assert ed.overlay_stack
  painel=ed.overlay_stack[-1]
  botoes=[w for w in painel.footer.winfo_children() if hasattr(w,'invoke')]
  assert botoes
  botoes[-1].invoke();app.update_idletasks()
  html=(destino/ed.vinculo['alvo']).read_text()
  assert 'Texto de verificação adicionado.' in html
  assert all(c['ancora'] in html for c in cap['cenas'])
  assert list((destino/'.literature-backups').rglob(Path(cap['arquivo']).name))
  assert ed.project_path.is_file()
  # Abrir autoria externa mantém o capítulo selecionado como destino.
  externo=Path(tmp)/'autoria-externa.narrproj';externo.write_text(json.dumps(ed.project_data(),ensure_ascii=False))
  antes_externo=externo.read_bytes();vinculo=dict(ed.vinculo)
  original_dialog=integ.filedialog.askopenfilename;original_confirm=ed.confirm_discard
  integ.filedialog.askopenfilename=lambda **kw:str(externo);ed.confirm_discard=lambda:True
  try:ed.open_project()
  finally:integ.filedialog.askopenfilename=original_dialog;ed.confirm_discard=original_confirm
  assert ed.vinculo==vinculo and ed.project_path.is_relative_to(destino)
  assert ed.save_project() and externo.read_bytes()==antes_externo
  # Uma alteração externa não bloqueia para sempre: aparece na comparação,
  # mas alterações depois de abrir essa comparação continuam protegidas.
  ed.vinculo['base']='revisao-antiga';ed.revisar();app.update_idletasks();assert ed.overlay_stack
  painel=ed.overlay_stack[-1]
  alvo=destino/ed.vinculo['alvo'];atual=alvo.read_text()+'\n<!-- alteração externa após revisão -->';alvo.write_text(atual)
  [w for w in painel.footer.winfo_children() if hasattr(w,'invoke')][-1].invoke()
  assert alvo.read_text()==atual,'Alteração posterior à comparação não pode ser sobrescrita'
  painel.close()
  app.previa();app.update_idletasks();assert app.aba_previa.winfo_toplevel() is app
  assert not any(w.winfo_class()=='Toplevel' for w in app.winfo_children())
  from importar_autoria import importar_html
  dados,avisos=importar_html('<p>Veja <span data-glossary-term="lua">lua</span>.</p><script id="story-glossary" type="application/json">{"lua":"Definição de teste"}</script>',{'cenas':[]},ed.default_section_meta(scope='chapter'),ed.schema)
  ed.abrir_autoria(dados)
  exportado=ed.exportar_capitulo()
  assert exportado.count('data-glossary-term="lua"')==1,'Ligação explícita precisa sobreviver à reexportação, sem duplicação'
  assert 'Definição de teste' in exportado
  from estado_publicacao import assinatura_fontes
  app.validacao_assinatura=assinatura_fontes(destino);app.atualizar_estado()
  assert 'Validação: aprovada' in app.estado_texto.get()
  assert 'aguarda revisão e aplicação' in app.estado_texto.get()
  print('OK: uma janela; autoria → revisão → HTML com backup; guia preservado; prévia interna; originais intactos.')
 finally:app.destroy()

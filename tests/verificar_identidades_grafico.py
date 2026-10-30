"""Integração de identidades e apresentação contextual, em cópia temporária."""
import json,re,shutil,sys,tempfile
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto
from editor_componente import modulo
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(root,destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.git','.aws','.codex','.agents','__pycache__','.literature-backups'))
 from fixture_projeto import preparar_fixture;preparar_fixture(destino)
 gv.ROOT=integ.ROOT=destino;gv.Projeto=integ.Projeto=lambda:Projeto(destino);p=Projeto(destino)
 app=gv.Studio();app.update()
 try:
  info,rev=p.ler('obra-1/dados/info-obra.json');ident=info['personagens'][0]['id'];info['personagens'][0]['aliases']=['Apelido pesquisável'];p.salvar('obra-1/dados/info-obra.json',info,rev)
  descr=next(d for d in app.itens.values() if d[0]=='obra-1' and d[1].endswith('editorial.json') and len(d[2])==8)
  app.carregar(descr);app.editor_semantico();app.update();ed=app.editor
  notificar=ed.notify;ed.notify=lambda *a,**k:None
  try:ed.reload_schema()
  finally:ed.notify=notificar
  assert 'data-pov-display-name' in ed.schema['section']['attributes']
  assert 'creature' in ed.schema['roles']['thought']['attributes']['data-thinker']['entity_types']
  quadro=ttk.Frame(ed);campo_nome=modulo.FieldEditor(quadro,ed,'data-display-name',{'kind':'text'},'???');assert campo_nome.get()=='???';quadro.destroy()
  dados=ed.project_data();dados['entities']=[ed.entities[ident]];dados['section']['data-pov-character']=ident;dados['section']['data-pov-display-name']='???'
  dados['semantic'].append({'id':'identidade-teste','start':0,'end':min(4,len(dados['text'])),'meta':{'data-role':'thought','data-thinker':ident,'data-display-name':'Voz desconhecida'}})
  ed.abrir_autoria(dados);ed.sincronizar_recursos();assert ed.save_project()
  salvo=json.loads(ed.project_path.read_text());assert ident in salvo['integracao_entidades']['bases']
  info,rev=p.ler('obra-1/dados/info-obra.json');info['personagens'][0]['nome']='Nome atualizado na biblioteca';p.salvar('obra-1/dados/info-obra.json',info,rev)
  ed.sincronizar_recursos();assert ed.entities[ident]['name']=='Nome atualizado na biblioteca'
  ed.entities[ident]['name']='Proposta local';ed.sincronizar_recursos();assert ident in ed.estado_entidades['conflitos'];assert any('Concilie' in e for e in ed.validate_document())
  ed.conciliar_entidades();app.update();painel=ed.overlay_stack[-1]
  def procurar(w,texto):
   for c in w.winfo_children():
    if isinstance(c,ttk.Button) and c.cget('text')==texto:return c
    achado=procurar(c,texto)
    if achado:return achado
  procurar(painel.body,'Usar dados do cadastro').invoke();app.update();assert not ed.estado_entidades['conflitos']
  html=ed.exportar_capitulo();assert 'data-display-name="Voz desconhecida"' in html and 'data-pov-display-name="???"' in html
  registro=json.loads(re.search(r'<script id="story-entities" type="application/json">([\s\S]*?)</script>',html)[1]);assert [e['id'] for e in registro]==[ident],'Exportação inclui somente entidades utilizadas'
  quadro=ttk.Frame(ed);campo=modulo.FieldEditor(quadro,ed,'data-thinker',ed.schema['roles']['thought']['attributes']['data-thinker'],ident)
  campo.seletor.busca.set('Apelido pesquisável');app.update();assert campo.get()==ident;quadro.destroy()
  ed.consultar_ocorrencias();app.update();painel=ed.overlay_stack[-1];lista=next(c for c in painel.body.winfo_children() if isinstance(c,ttk.Treeview));assert len(lista.get_children())>=2;painel.close()
  # Importação sem identidade de obra confirmada deve isolar IDs coincidentes.
  externo=Path(tmp)/'externo.narrproj';externo.write_text(json.dumps({'version':5,'text':'Texto externo','entities':[{'id':ident,'name':'Lugar de outra obra','type':'location'}],'section':{'id':'cap-externo','data-scope':'chapter','data-pov-character':ident}}));antes=externo.read_bytes()
  dialog=integ.filedialog.askopenfilename;confirmar=ed.confirm_discard;integ.filedialog.askopenfilename=lambda **k:str(externo);ed.confirm_discard=lambda:True
  try:ed.open_project()
  finally:integ.filedialog.askopenfilename=dialog;ed.confirm_discard=confirmar
  local=next(e for e in ed.entities.values() if e['name']=='Lugar de outra obra');assert local['id']!=ident and local['type']=='location'
  assert ed.section_meta['data-pov-character']==local['id'] and externo.read_bytes()==antes
  assert ed.estado_entidades['importacoes'][0]['ids'][ident]==local['id']
  print('OK: base persistente; cadastro atualizado; conflito local preservado e conciliado; seletor por apelido; ocorrências; nome contextual; exportação enxuta; colisão externa isolada com origem preservada.')
 finally:app.destroy()

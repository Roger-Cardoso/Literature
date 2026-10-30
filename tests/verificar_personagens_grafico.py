"""Cadastro, referências e vínculo semântico em cópia isolada, sem alterar a obra real."""
import sys,shutil,tempfile,json
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto,hash_arquivo
from seletor_personagens import SeletorPersonagens
from personagens import participacoes
from gerar_site import preparar

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(root,destino,ignore=shutil.ignore_patterns('.git','.codex','.aws','.agents','__pycache__','.literature-backups'))
 from fixture_projeto import preparar_fixture;preparar_fixture(destino)
 gv.ROOT=integ.ROOT=destino;gv.Projeto=integ.Projeto=lambda:Projeto(destino);p=Projeto(destino)
 info,rev=p.ler('obra-1/dados/info-obra.json');canon=info['personagens'][0]['id'];outro=info['personagens'][1]['id'];info['personagens'][0]['aliases']=['Apelido único'];info['personagens'][1]['nome']=info['personagens'][0]['nome'];p.salvar('obra-1/dados/info-obra.json',info,rev)
 app=gv.Studio();app.update()
 try:
  capid=next(c['id'] for _,c in p.capitulos(p.ler('obra-1/dados/editorial.json')[0]));iid='editorial:obra-1:'+capid
  app.inventario(foco=iid);app.update();seletor=app.widgets['personagens_ids'];assert isinstance(seletor,SeletorPersonagens)
  seletor.selecionar([canon,outro]);seletor.busca.set('Apelido único');app.update();assert seletor.ids()==[canon,outro],'Busca deve manter seleção oculta e distinguir homônimos por ID'
  seletor.selecionar([canon]);assert app.salvar();app.update()
  arvore,_=p.ler('obra-1/dados/editorial.json');cap=next(c for _,c in p.capitulos(arvore) if c['id']==capid);assert cap['personagens_ids']==[canon]
  cena=cap['cenas'][0];cena_iid=iid+':cenas:'+cena['id'];app.inventario(foco=cena_iid);app.update();app.widgets['personagens_ids'].selecionar([outro]);assert app.salvar()
  assert participacoes(p.ler('obra-1/dados/editorial.json')[0],outro)[0]['cena']==cena['id']
  # Renomear preserva todas as referências.
  app.inventario(foco='obra:obra-1:personagens:'+canon);app.update();app.widgets['nome'].delete(0,'end');app.widgets['nome'].insert(0,'Nome canônico atualizado');assert app.salvar()
  app.consultar_participacoes();app.update();locais=app._participacoes_personagem_ui;assert len(locais.get_children())==1
  locais.selection_set(locais.get_children()[0]);painel=app.overlay_stack[-1];[w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)][-1].invoke();app.update();assert app.obj['id']==capid
  app.editor_semantico();app.update();ed=app.editor;assert ed.entities[canon]['name']=='Nome canônico atualizado'
  # Cria autoria fictícia com referências a uma identidade importada.
  data=ed.project_data();texto=data['text'];data['entities'].append({'id':'origem-importada','name':'Nome importado','type':'character'});data['section']['data-pov-character']='origem-importada'
  data['semantic'].append({'id':'marca-teste-vinculo','start':0,'end':min(5,len(texto)),'meta':{'data-role':'thought','data-thinker':'origem-importada'}})
  ed.abrir_autoria(data);ed.text.insert('end','\nAcréscimo reversível.');ed.text.edit_separator();antes=ed.text.get('1.0','end-1c');intervalos=[(x['id'],x['start'],x['end']) for x in ed.project_data()['semantic']]
  ed.vincular_personagens();app.update();origem,alvo=ed._vinculo_personagens_ui;alvo.selecionar([canon]);painel=ed.overlay_stack[-1];botoes=[w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)];botoes[0].invoke();app.update();botoes[1].invoke();app.update()
  assert not ed.overlay_stack and 'origem-importada' not in ed.entities
  assert ed.section_meta['data-pov-character']==canon
  assert ed.text.get('1.0','end-1c')==antes and [(x['id'],x['start'],x['end']) for x in ed.project_data()['semantic']]==intervalos
  ed.text.edit_undo();app.update();assert ed.text.get('1.0','end-1c')==texto,'Vínculo não pode apagar o histórico de escrita'
  ed.participacoes_capitulo();app.update();assert canon in ed._participacoes_ui.ids()
  ed._participacoes_ui.selecionar([canon,outro]);painel=ed.overlay_stack[-1];next(w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)).invoke();app.update()
  cap=next(c for _,c in p.capitulos(p.ler('obra-1/dados/editorial.json')[0]) if c['id']==capid);assert cap['personagens_ids']==[canon,outro]
  # Salvar as participações não aplica implicitamente o texto da autoria.
  assert 'origem-importada' not in (destino/ed.vinculo['alvo']).read_text()
  preparar(destino)
  print('OK: seleção por nome/apelido e ID; homônimos; capítulos e cenas; consulta inversa; renomeação; vínculo de POV/pensamento; texto, intervalos e desfazer preservados; participações com backup.')
 finally:app.destroy()

"""Mil capítulos fictícios: árvore, movimentação visual e integração, em cópia isolada."""
import sys
import tempfile
import shutil
import json
from pathlib import Path
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_hierarquia import estrutura
import gerenciador_visual as gv
import integracao_semantica as integ
from gestao_projeto import Projeto,hash_arquivo
import hierarquia as h
from gerar_site import gerar,preparar

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(root,destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.git','.aws','.agents','.codex','site','__pycache__','.literature-backups'))
 from fixture_projeto import preparar_fixture;preparar_fixture(destino)
 p=Projeto(destino);doc=estrutura(1000);h.lista_destino(doc,'capitulo','arco-a').reverse()
 info,rev=p.ler('obra-1/dados/info-obra.json');info['personagens']=[];info['lore']=[];p.salvar('obra-1/dados/info-obra.json',info,rev)
 p.salvar('obras.json',{'schema_version':2,'obras':['obra-1']},hash_arquivo(destino/'obras.json'))
 p.organizar('obra-1',doc,hash_arquivo(destino/'obra-1/dados/editorial.json'))
 for no in h.nos(doc):
  if no.tipo=='capitulo':
   caminho=destino/'obra-1'/no.item['arquivo'];caminho.parent.mkdir(exist_ok=True,parents=True);caminho.write_text('<p>Texto fictício preservado.</p>',encoding='utf-8')
 gerar(destino)
 gv.ROOT=integ.ROOT=destino;gv.Projeto=integ.Projeto=lambda:Projeto(destino)
 app=gv.Studio();app.update()
 try:
  nav=app.navegacao;iid='editorial:obra-1:cap-500';arco_b='editorial:obra-1:arco-b'
  assert len(nav.nos)==1004 and len([n for n in nav.nos.values() if n.tipo=='capitulo'])==1000
  assert app.tree.exists(arco_b),'Arco vazio precisa existir na árvore'
  assert not app.tree.exists(iid+':html'),'Filhos do capítulo devem ser carregados sob demanda'
  assert app.tree.get_children('editorial:obra-1:arco-a')[0]=='editorial:obra-1:cap-0','Ordem visual usa ordem editorial, não índice físico'
  app.carregar(nav.referencias[iid]);nav.revelar(iid);app.update()
  assert app.obj['id']=='cap-500' and app.tree.exists(iid+':html')
  assert str(app.widgets['ordem'].cget('state'))=='readonly'
  app.tree.item('obra:obra-1',open=False);app.localizar_atual();app.update();assert app.tree.item('obra:obra-1','open')
  fonte=destino/'obra-1/writed/cap-500.html';antes=fonte.read_bytes()
  app.organizar_estrutura();app.update();painel=app.overlay_stack[-1]
  combo=next(w for w in painel.body.winfo_children() if isinstance(w,ttk.Combobox));combo.current(1);combo.event_generate('<<ComboboxSelected>>');app.update()
  botoes=[w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)];botoes[0].invoke();app.update();assert str(botoes[1].cget('state'))=='normal'
  botoes[1].invoke();app.update()
  assert app._iid_atual==iid and app.obj['id']=='cap-500'
  assert app.tree.parent(iid)==arco_b and app.tree.set(iid,'posicao')=='1.1.2.1'
  assert fonte.read_bytes()==antes and app.obj['numero']=='510'
  app.editor_semantico();app.update();ed=app.editor;vinculo=dict(ed.vinculo)
  app.deslocar(1);app.update();assert ed.vinculo==vinculo,'Vínculo semântico não muda ao reorganizar'
  # Insere antes do capítulo selecionado por meio do próprio painel visual.
  app.novo_capitulo('antes');app.update();painel=app.overlay_stack[-1]
  entrada=next(w for w in painel.body.winfo_children() if w.winfo_class()=='TEntry');entrada.insert(0,'Capítulo inserido')
  next(w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)).invoke();app.update()
  novo=app.obj['id'];assert novo!='cap-500' and app.obj['estado_publicacao']=='rascunho'
  assert app.tree.set('editorial:obra-1:'+novo,'posicao')=='1.1.2.1'
  assert app.tree.set(iid,'posicao')=='1.1.2.2'
  nav.busca.set('cap-500');app.inventario();app.update();assert app.tree.exists(iid)
  assert len([n for chave,n in nav.nos.items() if n.tipo=='capitulo' and app.tree.exists(chave)])==1
  nav.busca.set('');nav.filtro.set('rascunho');app.inventario();app.update()
  assert app.tree.exists('editorial:obra-1:'+novo) and not app.tree.exists(iid)
  nav.filtro.set('Todos');app.inventario();app.update()
  assert app._iid_atual=='editorial:obra-1:'+novo and app.obj['id']==novo
  arvore,_=p.ler('obra-1/dados/editorial.json');publicos=[c['id'] for _,c in p.capitulos(arvore) if c['estado_publicacao']=='publicado']
  saida=preparar(destino)[0][2];gerados=[c['id'] for _,c in p.capitulos(saida)]
  assert publicos==gerados and len(gerados)==1000,'Publicação e gerenciador precisam da mesma ordem'
  # Os painéis continuam acessíveis quando a árvore ocupa parte da janela.
  app.carregar(nav.referencias[iid]);app.abas.select(app.aba_editor);app.update()
  app.geometry('850x650');app.update()
  assert ed.text.winfo_ismapped() and ed.text.winfo_width()>100,'A coluna de texto precisa continuar utilizável em janela menor'
  if ed._workspace.winfo_width()<1000:
   ed.alternar_painel('propriedades');app.update();assert ed._painel_propriedades.winfo_ismapped()
   ed.alternar_painel('ferramentas');app.update();assert ed._painel_ferramentas.winfo_ismapped()
  app.geometry('1180x800');app.update()
  # Criação de agrupamento pelo painel, mantendo o mesmo volume selecionado.
  app.carregar(nav.referencias['editorial:obra-1:volume']);app.novo_agrupamento();app.update();painel=app.overlay_stack[-1]
  nome=next(w for w in painel.body.winfo_children() if w.winfo_class()=='TEntry');nome.insert(0,'Arco criado visualmente')
  next(w for w in painel.footer.winfo_children() if isinstance(w,ttk.Button)).invoke();app.update()
  assert app.obj['nome']=='Arco criado visualmente' and app.obj['capitulos']==[]
  assert nav.nos[app._iid_atual].pai=='volume'
  # Uma reorganização externa é resolvida pelo ID no recarregamento.
  app.carregar(nav.referencias[iid]);arvore,rev=p.ler('obra-1/dados/editorial.json')
  p.organizar('obra-1',h.mover(arvore,'cap-500','arco-a',1),rev);app.recarregar();app.update()
  assert app.obj['id']=='cap-500' and app._iid_atual==iid
  assert app.tree.set(iid,'posicao')=='1.1.1.1'
  assert ed.vinculo==vinculo
  arvore,_=p.ler('obra-1/dados/editorial.json');publicos=[c['id'] for _,c in p.capitulos(arvore) if c['estado_publicacao']=='publicado']
  assert publicos==[c['id'] for _,c in p.capitulos(preparar(destino)[0][2])]
  assert fonte.read_bytes()==antes
  print('OK: 1.000 capítulos; hierarquia e grupos vazios; ordem editorial; filhos sob demanda; movimento visual; inserção antes; filtros; seleção e vínculo semântico preservados; ordem pública igual.')
 finally:app.destroy()

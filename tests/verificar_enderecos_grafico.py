"""Endereço editável da obra e número permanente do capítulo na mesma janela."""
import json,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
from gestao_projeto import Projeto
from fixture_projeto import preparar_fixture
from hierarquia import nos
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'projeto';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.literature-backups','.git','.agents','.codex','.aws','site','__pycache__'));preparar_fixture(root)
 gv.ROOT=root;gv.Projeto=lambda:Projeto(root);app=gv.Studio();app.update()
 def alterar(key,text):w=app.widgets[key];w.delete(0,'end');w.insert(0,text)
 try:
  app.abrir_obra('obra-1');app.update();alterar('endereco_publico','livro-teste');assert app.salvar();app.update();alterar('titulo','Novo título fictício');assert app.salvar();app.update()
  info,_=app.projeto.ler('obra-1/dados/info-obra.json');assert info['endereco_publico']=='livro-teste';assert info['enderecos_anteriores'];assert info['titulo']=='Novo título fictício'
  tree,_=app.projeto.ler('obra-1/dados/editorial.json');cap=next(n for n in nos(tree) if n.tipo=='capitulo');app.carregar(('obra-1','obra-1/dados/editorial.json',cap.caminho));app.update();assert str(app.widgets['numero_url'].cget('state'))=='readonly'
  alterar('titulo','Primeira alteração');assert app.salvar();app.update();alterar('titulo','Segunda alteração');assert app.salvar();app.update()
  tree,_=app.projeto.ler('obra-1/dados/editorial.json');salvo=next(n.item for n in nos(tree) if n.id==cap.id);assert salvo['titulo']=='Segunda alteração';assert salvo['numero_url']==cap.item['numero_url']
  print('OK: endereço editável e prévia na ficha; histórico; título independente; número do capítulo protegido; duas gravações consecutivas mantêm o documento integrado.')
 finally:app.destroy()

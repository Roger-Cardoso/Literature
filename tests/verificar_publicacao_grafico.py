"""Fluxo visual completo em cópia temporária, sem escrever no GitHub real."""
from pathlib import Path
import sys,shutil,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gerenciador_visual as gv
import publicacao_visual as pv
from gestao_projeto import Projeto
from fixture_projeto import preparar_fixture
from test_publicacao import GitHubFake
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 destino=Path(tmp)/'projeto';shutil.copytree(ROOT,destino,ignore=shutil.ignore_patterns('node_modules','.wrangler','.git','.agents','.aws','.codex','site','publicado','.literature-backups','.literature-lixeira','.literature-publicacoes','.literature-studio.json','__pycache__'));preparar_fixture(destino)
 gv.ROOT=destino;gv.Projeto=lambda:Projeto(destino);fake=GitHubFake();fake.usuario=lambda:'autor-teste';pv.GitHub=lambda:fake
 app=gv.Studio();app.update()
 def esperar(cond):
  fim=time.monotonic()+12
  while time.monotonic()<fim:
   app.update()
   if cond():return
   time.sleep(.03)
  raise AssertionError('A operação não terminou na interface')
 try:
  app.gerenciar_publicacao();app.update();page=app.pagina_publicacao;app.gerenciar_publicacao();assert app.abas.select()==str(page)
  page.sincronizar.set(False);page.preparar();esperar(lambda:page.revisao is not None and not page.ocupado)
  assert page.lista.get_children() and str(page.botao_enviar.cget('state'))=='normal'
  page.lista.selection_set(page.lista.get_children()[0]);page.ver_arquivo();assert page.detalhe.get('1.0','end-1c')
  # Formulário pode ser rolado por mouse mesmo com os controles de revisão.
  page.rolagem.canvas.yview_moveto(0);app.update();entrada=next(w for w in page.rolagem.content.winfo_children() if w.winfo_class()=='TEntry');entrada.event_generate('<Button-5>');app.update();assert page.rolagem.canvas.yview()[0]>0
  page.publicar();esperar(lambda:page.recibo is not None and not page.ocupado);assert fake.head==page.recibo['commit'];assert not page.revisao
  fake.runs=[{'id':1,'head_sha':fake.head,'status':'completed','conclusion':'success','html_url':'https://github.com/teste/execucao'}]
  page.consultar();esperar(lambda:'aprovada' in page.estado.get() and not page.ocupado)
  assert page.recibo['execucao']['conclusion']=='success'
  page.preparar();esperar(lambda:page.revisao is not None and not page.ocupado);assert not page.revisao['mudancas'];assert str(page.botao_enviar.cget('state'))=='disabled'
  page.repo.set('Outro/Repositorio');app.update();assert page.revisao is None and str(page.botao_enviar.cget('state'))=='disabled'
  print('OK: aba única; geração e revisão; prévia; roda do mouse; envio de arquivos públicos; recibo; acompanhamento; ausência de mudanças; destino alterado invalida revisão; nenhuma escrita no GitHub real.')
 finally:
  if getattr(app,'pagina_publicacao',None) and app.pagina_publicacao.pacote:app.pagina_publicacao.pacote.fechar()
  app.destroy()

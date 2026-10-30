"""Contrato de publicação: apenas saída pública, revisão selada e avanço sem força."""
import base64
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fixture_projeto import preparar_fixture
from pacote_publicacao import PacotePublicacao,git_blob,verificar,MARCADOR
from github_publicacao import preparar_revisao,enviar,ErroPublicacao,destino,acompanhar,salvar_recibo,ultimo_recibo,sincronizar_comentarios
ROOT=Path(__file__).resolve().parents[1]

class GitHubFake:
 def __init__(self):
  self.head='head-0';self.commit_trees={'head-0':'tree-0'};self.trees={'tree-0':{'README.md':{'path':'README.md','type':'blob','mode':'100644','sha':'preservar'}}};self.blobs={};self.calls=[];self.compatible=True;self.truncated=False;self.race=False;self.runs=[]
 def chamar(self,path,metodo='GET',dados=None):
  self.calls.append((path,metodo,copy.deepcopy(dados)))
  if '/git/ref/heads/' in path:return {'object':{'sha':self.head}}
  if '/git/commits/' in path:return {'tree':{'sha':self.commit_trees[path.split('/')[-1]]}}
  if '/git/trees/' in path:
   tree=path.split('/')[-1].split('?')[0];return {'tree':list(self.trees[tree].values()),'truncated':self.truncated}
  if '/contents/.github/workflows/' in path:return {'content':base64.b64encode(('literature-studio-snapshot-v1' if self.compatible else 'antigo').encode()).decode()}
  if path.endswith('/git/blobs'):
   data=base64.b64decode(dados['content']);sha=git_blob(data);self.blobs[sha]=data;return {'sha':sha}
  if path.endswith('/git/trees'):
   tree=copy.deepcopy(self.trees[dados['base_tree']])
   for e in dados['tree']:
    if e.get('sha','') is None:tree.pop(e['path']);continue
    e=copy.deepcopy(e)
    if 'content' in e:
     data=e.pop('content').encode();e['sha']=git_blob(data);self.blobs[e['sha']]=data
    tree[e['path']]=e
   sha='tree-'+str(len(self.trees));self.trees[sha]=tree
   if self.race:self.head='externo'
   return {'sha':sha}
  if path.endswith('/git/commits'):
   sha='head-'+str(len(self.commit_trees));self.commit_trees[sha]=dados['tree'];return {'sha':sha}
  if '/git/refs/heads/' in path:
   assert dados['force'] is False;self.head=dados['sha'];return {'object':{'sha':self.head}}
  if '/actions/workflows/pages.yml/runs' in path:return {'workflow_runs':self.runs}
  raise AssertionError((path,metodo))

class PublicacaoTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'projeto';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('node_modules','.wrangler','.git','.agents','.aws','.codex','site','publicado','.literature-backups','.literature-lixeira','.literature-publicacoes','.literature-studio.json','__pycache__'))
  preparar_fixture(self.root);self.gh=GitHubFake();self.pacote=None
 def tearDown(self):
  if self.pacote:self.pacote.fechar()
  self.tmp.cleanup()
 def pacote_e_revisao(self):
  self.pacote=PacotePublicacao(self.root);return preparar_revisao(self.pacote,self.gh,'Roger-Cardoso/Literature','main')
 def test_pacote_somente_publico_sem_autoria_e_capitulo_rascunho(self):
  (self.root/'obra-1/autoria').mkdir();(self.root/'obra-1/autoria/privado.narrproj').write_text('SEGREDO')
  path=self.root/'obra-1/dados/editorial.json';doc=json.loads(path.read_text());c=doc['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'][0];c['estado_publicacao']='rascunho';path.write_text(json.dumps(doc));(self.root/'obra-1'/c['arquivo']).write_text('SEGREDO DO CAPÍTULO')
  self.pacote_e_revisao();self.assertFalse((self.pacote.pasta/'obra-1'/c['arquivo']).exists());self.assertFalse(list(self.pacote.pasta.rglob('*.narrproj')));verificar(self.pacote.pasta)
 def test_envio_preserva_codigo_e_usa_avanco_sem_forca(self):
  rev=self.pacote_e_revisao();recibo=enviar(self.pacote,rev,self.gh,'Publicar')
  self.assertEqual(self.gh.trees[self.gh.commit_trees[self.gh.head]]['README.md']['sha'],'preservar');self.assertIn('publicado/'+MARCADOR,self.gh.trees[self.gh.commit_trees[self.gh.head]])
  self.assertTrue(all(e['path'].startswith('publicado/') for p,m,d in self.gh.calls if p.endswith('/git/trees') for e in d['tree']))
  self.assertEqual(recibo['commit'],self.gh.head)
 def test_nova_revisao_sem_diferencas_nao_cria_commit(self):
  rev=self.pacote_e_revisao();enviar(self.pacote,rev,self.gh,'Publicar');rev2=preparar_revisao(self.pacote,self.gh,'Roger-Cardoso/Literature','main');self.assertEqual(rev2['mudancas'],[]);n=len(self.gh.commit_trees);self.assertTrue(enviar(self.pacote,rev2,self.gh,'Conferir')['sem_alteracoes']);self.assertEqual(len(self.gh.commit_trees),n)
 def test_remove_somente_arquivos_do_prefixo_gerenciado(self):
  self.gh.trees['tree-0']['publicado/'+MARCADOR]={'path':'publicado/'+MARCADOR,'type':'blob','mode':'100644','sha':'antigo'}
  self.gh.trees['tree-0']['publicado/antigo.html']={'path':'publicado/antigo.html','type':'blob','mode':'100644','sha':'antigo'}
  rev=self.pacote_e_revisao();self.assertTrue(any(x['acao']=='remover' for x in rev['mudancas']));enviar(self.pacote,rev,self.gh,'Atualizar');tree=self.gh.trees[self.gh.commit_trees[self.gh.head]];self.assertNotIn('publicado/antigo.html',tree);self.assertIn('README.md',tree)
 def test_fontes_ou_pacote_alterados_bloqueiam_envio(self):
  rev=self.pacote_e_revisao();(self.root/'home/index.html').write_text('mudança')
  with self.assertRaises(ValueError):enviar(self.pacote,rev,self.gh,'Atualizar')
  self.assertEqual(self.gh.head,'head-0')
 def test_manifesto_recalculado_nao_substitui_revisao_em_memoria(self):
  self.pacote_e_revisao();p=self.pacote.pasta;meta=json.loads((p/MARCADOR).read_text());meta['extra']='alteração';(p/MARCADOR).write_text(json.dumps(meta))
  with self.assertRaises(ValueError):self.pacote.conferir()
 def test_mudanca_remota_antes_ou_durante_upload_nao_e_sobrescrita(self):
  rev=self.pacote_e_revisao();self.gh.race=True
  with self.assertRaises(ErroPublicacao):enviar(self.pacote,rev,self.gh,'Atualizar')
  self.assertEqual(self.gh.head,'externo');self.assertFalse(any(m=='PATCH' for p,m,d in self.gh.calls))
 def test_nao_toma_pasta_existente_sem_marcador(self):
  self.gh.trees['tree-0']['publicado/arquivo.html']={'path':'publicado/arquivo.html','type':'blob','mode':'100644','sha':'qualquer'}
  with self.assertRaises(ErroPublicacao):self.pacote_e_revisao()
 def test_pacote_recusa_arquivo_privado_e_vinculo_simbolico(self):
  self.pacote_e_revisao();p=self.pacote.pasta/'assets/credencial.env';p.write_text('privado')
  with self.assertRaises(ValueError):verificar(self.pacote.pasta)
  p.unlink();p=self.pacote.pasta/'assets/atalho.txt';p.symlink_to(self.root/'README.md')
  with self.assertRaises(ValueError):verificar(self.pacote.pasta)
 def test_arquivo_binario_enviado_com_base64(self):
  data=b'\x89PNG\x00\xff\xfe';(self.root/'assets/imagens/teste.png').write_bytes(data);rev=self.pacote_e_revisao();enviar(self.pacote,rev,self.gh,'Imagem');self.assertEqual(self.gh.blobs[git_blob(data)],data)
 def test_workflow_incompativel_e_arvore_truncada_bloqueiam_revisao(self):
  self.gh.compatible=False
  with self.assertRaises(ErroPublicacao):self.pacote_e_revisao()
 def test_recibo_e_consulta_correspondem_ao_commit_enviado(self):
  rev=self.pacote_e_revisao();r=enviar(self.pacote,rev,self.gh,'Atualizar');salvar_recibo(self.root,r);self.assertEqual(ultimo_recibo(self.root)['commit'],r['commit']);self.gh.runs=[{'id':1,'head_sha':r['commit'],'status':'completed','conclusion':'success','html_url':'https://github.com/execucao'}];self.assertEqual(acompanhar(self.gh,r)['conclusion'],'success')
 def test_sincronizacao_recusa_implantacao_pendente(self):
  with self.assertRaises(ErroPublicacao):sincronizar_comentarios(self.gh,{'repositorio':'Roger-Cardoso/Literature','branch':'main','commit':'head-0'},Path('nao-ler-credencial'))
 def test_nova_publicacao_nao_recebe_manifesto_antigo(self):
  rev=self.pacote_e_revisao();recibo=enviar(self.pacote,rev,self.gh,'Publicar');anterior=recibo['commit'];self.gh.head='novo'
  self.gh.runs=[{'id':1,'head_sha':anterior,'status':'completed','conclusion':'success','html_url':'https://github.com/a'},{'id':2,'head_sha':'novo','status':'completed','conclusion':'success','html_url':'https://github.com/b'}]
  original=self.gh.chamar
  def responder(path,*args):
   if '/contents/publicado/' in path:return {'content':base64.b64encode(json.dumps({'conteudo_sha256':'diferente'}).encode()).decode()}
   return original(path,*args)
  self.gh.chamar=responder
  with self.assertRaises(ErroPublicacao):sincronizar_comentarios(self.gh,recibo,Path('nao-ler-credencial'))
 def test_atualizacao_de_codigo_com_mesmo_pacote_permite_sincronizar(self):
  rev=self.pacote_e_revisao();recibo=enviar(self.pacote,rev,self.gh,'Publicar');anterior=recibo['commit'];self.gh.head='novo'
  self.gh.runs=[{'id':1,'head_sha':anterior,'status':'completed','conclusion':'success','html_url':'https://github.com/a'},{'id':2,'head_sha':'novo','status':'completed','conclusion':'success','html_url':'https://github.com/b'}]
  original=self.gh.chamar
  def responder(path,*args):
   if '/contents/publicado/' in path:return {'content':base64.b64encode(json.dumps({'conteudo_sha256':recibo['conteudo_sha256']}).encode()).decode()}
   return original(path,*args)
  self.gh.chamar=responder;cred=Path(self.tmp.name)/'privado.json';cred.write_text(json.dumps({'api_url':recibo['config_comentarios']['api_url'],'admin_token':'x'*40}))
  with patch('cliente_comentarios.ClienteComentarios') as cls:
   cls.return_value.sincronizar.return_value={'total':4};self.assertEqual(sincronizar_comentarios(self.gh,recibo,cred)['total'],4)
 def test_destinos_invalidos_e_injecao_de_argumentos(self):
  self.assertEqual(destino('https://github.com/Roger-Cardoso/Literature.git','main'),('Roger-Cardoso/Literature','main'))
  for repo,branch in [('--hostname/evil','main'),('owner/repo','../main'),('owner/repo','a//b'),('owner/repo','a.lock')]:
   with self.assertRaises(ValueError):destino(repo,branch)

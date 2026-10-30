"""Contratos de CRUD de obras, integridade e recuperação de autoria."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gestao_projeto import Projeto,ConflitoEdicao
from gerar_site import preparar
ROOT=Path(__file__).resolve().parents[1]

from fixture_projeto import preparar_fixture
class ObrasTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'projeto'
  shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('site','.git','.agents','.aws','.codex','__pycache__','.literature-backups','.literature-lixeira'))
  preparar_fixture(self.root)
  self.p=Projeto(self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_biblioteca_e_estatisticas(self):
  obras=self.p.biblioteca_obras();self.assertEqual({x['slug'] for x in obras},set(self.p.obras()))
  for x in obras:
   a,_=self.p.ler(x['slug']+'/dados/editorial.json');self.assertEqual(x['capitulos'],len(self.p.capitulos(a)))
 def test_edicao_preserva_identidade_e_faz_backup(self):
  info,rev=self.p.ler('obra-1/dados/info-obra.json');self.p.editar_obra('obra-1',{'titulo':'Novo título','autor':'Novo autor'},rev)
  novo,_=self.p.ler('obra-1/dados/info-obra.json');self.assertEqual(novo['id_obra'],info['id_obra']);self.assertEqual(novo['titulo'],'Novo título');self.assertTrue(list((self.root/'.literature-backups').rglob('info-obra.json')))
  with self.assertRaises(ValueError):self.p.editar_obra('obra-1',{'slug':'troca'},rev)
 def test_edicao_concorrente_e_estado_invalido(self):
  info,rev=self.p.ler('obra-1/dados/info-obra.json');self.p.editar_obra('obra-1',{'titulo':'Nome atual'},rev)
  with self.assertRaises(ConflitoEdicao):self.p.editar_obra('obra-1',{'titulo':'Antigo'},rev)
  for dados in ({'titulo':''},{'estado_publicacao':'inexistente'}):
   with self.assertRaises(ValueError):self.p.editar_obra('obra-1',dados,self.p.ler('obra-1/dados/info-obra.json')[1])
 def test_exclusao_e_restauracao_preservam_autorias(self):
  arq=self.root/'obra-1/autoria/teste.narrproj';arq.parent.mkdir(exist_ok=True);arq.write_text('{"text":"Trabalho privado"}')
  antes={str(p.relative_to(self.root/'obra-1')):p.read_bytes() for p in (self.root/'obra-1').rglob('*') if p.is_file()}
  token=self.p.excluir_obra(self.p.preparar_exclusao_obra('obra-1'))
  self.assertNotIn('obra-1',self.p.obras());self.assertFalse((self.root/'obra-1').exists());self.assertEqual(self.p.obras_excluidas()[0]['token'],token)
  self.assertEqual(self.p.restaurar_obra(token),'obra-1')
  for rel,conteudo in antes.items():
   if rel=='dados/info-obra.json':
    novo=json.loads((self.root/'obra-1'/rel).read_text());antigo=json.loads(conteudo);antigo['estado_publicacao']='rascunho';self.assertEqual(novo,antigo)
   else:self.assertEqual((self.root/'obra-1'/rel).read_bytes(),conteudo)
  self.assertEqual(self.p.obras_excluidas(),[])
 def test_revisao_desatualizada_nao_exclui(self):
  proposta=self.p.preparar_exclusao_obra('obra-1');(self.root/'obra-1/novo.txt').write_text('mudança externa')
  with self.assertRaises(ValueError):self.p.excluir_obra(proposta)
  self.assertIn('obra-1',self.p.obras());self.assertTrue((self.root/'obra-1').is_dir())
 def test_falha_no_registro_reverte_exclusao(self):
  proposta=self.p.preparar_exclusao_obra('obra-1');salvar=self.p.salvar
  def falhar(rel,*a):
   if rel=='obras.json':raise OSError('Falha simulada')
   return salvar(rel,*a)
  with patch.object(self.p,'salvar',side_effect=falhar):
   with self.assertRaises(OSError):self.p.excluir_obra(proposta)
  self.assertIn('obra-1',self.p.obras());self.assertTrue((self.root/'obra-1/dados/info-obra.json').exists());self.assertEqual(self.p.obras_excluidas(),[])
 def test_restaura_falha_no_registro_preserva_recuperacao(self):
  token=self.p.excluir_obra(self.p.preparar_exclusao_obra('obra-1'));salvar=self.p.salvar
  def falhar(rel,*a):
   if rel=='obras.json':raise OSError('Falha simulada')
   return salvar(rel,*a)
  with patch.object(self.p,'salvar',side_effect=falhar):
   with self.assertRaises(OSError):self.p.restaurar_obra(token)
  self.assertNotIn('obra-1',self.p.obras());self.assertEqual(self.p.restaurar_obra(token),'obra-1')
 def test_endereco_ocupado_nao_sobrescreve(self):
  token=self.p.excluir_obra(self.p.preparar_exclusao_obra('obra-1'));self.p.nova_obra('obra-1','Outra obra','Autor')
  with self.assertRaises(ValueError):self.p.restaurar_obra(token)
  self.assertEqual(self.p.ler('obra-1/dados/info-obra.json')[0]['titulo'],'Outra obra');self.assertTrue(self.p.obras_excluidas())
 def test_cria_apos_excluir_todas_sem_modelo_vivo(self):
  for slug in self.p.obras():self.p.excluir_obra(self.p.preparar_exclusao_obra(slug))
  self.assertEqual(preparar(self.root),[]);self.p.nova_obra('nova','Nova','Autor');self.assertTrue((self.root/'nova/leitor.html').is_file());self.assertEqual(self.p.obras(),['nova']);preparar(self.root)
 def test_exportacao_inclui_autoria_sem_alterar_fontes(self):
  autoria=self.root/'obra-1/autoria/privada.narrproj';autoria.parent.mkdir(exist_ok=True);autoria.write_text('rascunho')
  assinatura=self.p.preparar_exclusao_obra('obra-1')['assinatura'];dest=Path(self.tmp.name)/'obra.zip';self.p.exportar_obra('obra-1',dest)
  with zipfile.ZipFile(dest) as z:
   self.assertEqual(z.read('obra-1/autoria/privada.narrproj'),b'rascunho');self.assertIn('LEIA-ME.txt',z.namelist());self.assertFalse(any(x.startswith('obra-2/') for x in z.namelist()))
  self.assertEqual(self.p.preparar_exclusao_obra('obra-1')['assinatura'],assinatura)
  with self.assertRaises(ValueError):self.p.exportar_obra('obra-1',self.root/'obra-1/substituir.zip')
 def test_caminhos_e_links_simbolicos(self):
  for slug in ('../obra-1','scripts','obra-1/../obra-2'):
   with self.assertRaises(ValueError):self.p.preparar_exclusao_obra(slug)
  (self.root/'obra-1/atalho').symlink_to(self.root/'obra-2',target_is_directory=True)
  with self.assertRaises(ValueError):self.p.preparar_exclusao_obra('obra-1')
 def test_arquivo_recuperado_alterado_fica_preservado(self):
  token=self.p.excluir_obra(self.p.preparar_exclusao_obra('obra-1'));(self.root/'.literature-lixeira'/token/'obra/novo.txt').write_text('alteração')
  with self.assertRaises(ValueError):self.p.restaurar_obra(token)
  self.assertNotIn('obra-1',self.p.obras());self.assertTrue(self.p.obras_excluidas())

if __name__=='__main__':unittest.main()

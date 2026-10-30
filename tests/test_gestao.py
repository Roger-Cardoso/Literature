import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('gestao',ROOT/'scripts/gestao_projeto.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from fixture_projeto import preparar_fixture
class GestaoTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'projeto';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('site','.git','.agents','.aws','.codex','__pycache__','.literature-backups'))
  preparar_fixture(self.root)
  self.p=m.Projeto(self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_backup_preserva_original(self):
  rel='obra-1/dados/info-obra.json';doc,rev=self.p.ler(rel);antes=self.p.caminho(rel).read_bytes();doc['titulo']='Título editado';self.p.salvar(rel,doc,rev)
  backups=list((self.root/'.literature-backups').rglob('info-obra.json'));self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),antes)
 def test_conflito_nao_sobrescreve(self):
  rel='obra-1/dados/info-obra.json';doc,rev=self.p.ler(rel);self.p.caminho(rel).write_text('{}')
  with self.assertRaises(m.ConflitoEdicao):self.p.salvar(rel,doc,rev)
  self.assertEqual(self.p.caminho(rel).read_text(),'{}')
 def test_criar_obra_e_capitulo_rascunhos(self):
  self.p.nova_obra('obra-teste','Obra teste','Autor');info,_=self.p.ler('obra-teste/dados/info-obra.json');tree,rev=self.p.ler('obra-teste/dados/editorial.json')
  ident=self.p.novo_capitulo('obra-teste','Capítulo teste',tree,rev)
  novo,_=self.p.ler('obra-teste/dados/editorial.json');self.assertEqual(info['estado_publicacao'],'rascunho');self.assertEqual(novo['capitulos'][0]['id'],ident);self.assertEqual(novo['capitulos'][0]['estado_publicacao'],'rascunho')
 def test_nao_edita_saida_ou_fora_projeto(self):
  for rel in ('../fora.json','site/catalogo.json'):
   with self.assertRaises(ValueError):self.p.caminho(rel)
 def test_pacote_somente_saida_publica(self):
  site=self.root/'site';site.mkdir();(site/'index.html').write_text('Publicado')
  dest=Path(self.tmp.name)/'publicacao.zip';self.p.exportar(dest)
  with zipfile.ZipFile(dest) as z:self.assertEqual(z.namelist(),['index.html'])
 def test_ids_nao_dependem_da_ordem(self):
  tree,rev=self.p.ler('obra-2/dados/editorial.json');antigos=[c['id'] for _,c in self.p.capitulos(tree)];self.p.novo_capitulo('obra-2','Novo capítulo',tree,rev)
  self.assertEqual([c['id'] for _,c in self.p.capitulos(tree)][:len(antigos)],antigos)
 def test_organizacao_conflitante_nao_troca_estrutura(self):
  from hierarquia import mover
  rel='obra-1/dados/editorial.json';doc,rev=self.p.ler(rel);cap=next(c for _,c in self.p.capitulos(doc));arco=next(a for a,c in self.p.capitulos(doc) if c['id']==cap['id'])
  proposta=mover(doc,cap['id'],arco['id'],len(arco['capitulos']))
  self.p.caminho(rel).write_text(self.p.caminho(rel).read_text()+'\n')
  antes=self.p.caminho(rel).read_bytes()
  with self.assertRaises(m.ConflitoEdicao):self.p.organizar('obra-1',proposta,rev)
  self.assertEqual(self.p.caminho(rel).read_bytes(),antes)
 def test_novo_capitulo_em_posicao_reverte_arquivo_se_conflitar(self):
  rel='obra-1/dados/editorial.json';doc,rev=self.p.ler(rel);arco,cap=self.p.capitulos(doc)[0]
  self.p.caminho(rel).write_text(self.p.caminho(rel).read_text()+'\n')
  antes={p.relative_to(self.root/'obra-1') for p in (self.root/'obra-1').rglob('*.html')}
  identidades=[c['id'] for _,c in self.p.capitulos(doc)]
  with self.assertRaises(m.ConflitoEdicao):self.p.novo_capitulo('obra-1','Novo',doc,rev,destino=arco['id'],posicao=1)
  self.assertEqual([c['id'] for _,c in self.p.capitulos(doc)],identidades)
  self.assertEqual(antes,{p.relative_to(self.root/'obra-1') for p in (self.root/'obra-1').rglob('*.html')})
 def test_criar_capitulo_no_arco_vazio_e_posicao_explicita(self):
  from hierarquia import nos,encontrar
  rel='obra-1/dados/editorial.json';doc,rev=self.p.ler(rel);arco=next(n for n in nos(doc) if n.tipo=='arco' and not n.item['capitulos'])
  ident=self.p.novo_capitulo('obra-1','Novo',doc,rev,destino=arco.id,posicao=1)
  salvo,_=self.p.ler(rel);novo=encontrar(salvo,ident)
  self.assertEqual(novo.pai,arco.id);self.assertEqual(novo.item['ordem'],1)
  self.assertEqual(novo.item['numero'],'');self.assertTrue(list((self.root/'.literature-backups').rglob('editorial.json')))
if __name__=='__main__':unittest.main()

import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import enderecos
from gestao_projeto import Projeto
from gerar_site import gerar
from fixture_projeto import preparar_fixture
ROOT=Path(__file__).resolve().parents[1]
class EnderecosTest(unittest.TestCase):
 def arvore(self):return {'schema_version':2,'capitulos':[{'id':'um','ordem':1},{'id':'dois','ordem':2}]}
 def test_numeracao_estavel_apos_insercao_reordenacao_exclusao(self):
  original=enderecos.numerar(self.arvore());nova=copy.deepcopy(original);nova['capitulos'].insert(0,{'id':'novo','ordem':0});nova=enderecos.numerar(nova,original)
  nums={c['id']:c['numero_url'] for c in nova['capitulos']};self.assertEqual(nums,{'novo':3,'um':1,'dois':2})
  depois=copy.deepcopy(nova);depois['capitulos']=[c for c in depois['capitulos'] if c['id']!='novo'];depois=enderecos.numerar(depois,nova);depois['capitulos'].append({'id':'outro','ordem':3});depois=enderecos.numerar(depois)
  self.assertEqual(depois['capitulos'][-1]['numero_url'],4)
  ruim=copy.deepcopy(original);ruim['capitulos'][0]['numero_url']=5
  with self.assertRaises(ValueError):enderecos.numerar(ruim,original)
 def test_slug_estavel_e_historico_sem_transferencia_de_numeros(self):
  i=enderecos.obra({'titulo':'A Lenda do Sertão'});self.assertEqual(i['endereco_publico'],'a-lenda-do-sertao')
  mudou=enderecos.obra({**i,'titulo':'Outro título'},i);self.assertEqual(mudou['endereco_publico'],i['endereco_publico'])
  novo=enderecos.obra({**i,'endereco_publico':'novo-endereco'},i);self.assertEqual(novo['enderecos_anteriores'],['a-lenda-do-sertao'])
  for slug in ['home','../outro','A-Lenda','capítulo','a/b','x?y']:
   with self.assertRaises(ValueError):enderecos.validar_slug(slug)
  with self.assertRaises(ValueError):enderecos.validar_catalogo([('um',i),('dois',i)])
  original=enderecos.numerar(self.arvore());novo=copy.deepcopy(original);novo['capitulos']=[{'id':'diferente','ordem':1,'numero_url':1}]
  with self.assertRaises(ValueError):enderecos.numerar(novo,original)
 def test_geracao_real_rotas_legados_e_interacoes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'projeto';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','.git','.agents','.codex','.aws','site','.literature-backups','__pycache__'));preparar_fixture(root)
   p=Projeto(root);info,rev=p.ler('obra-1/dados/info-obra.json');info['endereco_publico']='a-lenda-do-sertao';p.salvar('obra-1/dados/info-obra.json',info,rev)
   antes=(root/'obra-1/dados/editorial.json').read_bytes();gerar(root);out=root/'site'
   self.assertEqual(antes,(root/'obra-1/dados/editorial.json').read_bytes())
   self.assertTrue((out/'a-lenda-do-sertao/index.html').exists());html=(out/'a-lenda-do-sertao/capitulo-3/index.html').read_text();self.assertIn('<base href="/obra-1/">',html);self.assertIn('name="literature-capitulo" content="obra-1-cap-003"',html);self.assertIn('rel="canonical"',html)
   self.assertIn('location.replace',(out/'obra-1/index-obra.html').read_text());self.assertIn('atual.url_publica',(out/'js-global/leitor.js').read_text())
   dto=json.loads((out/'obra-1/dados/estrutura.json').read_text());caps=[n.item for n in __import__('hierarquia').nos(dto) if n.tipo=='capitulo'];self.assertEqual(caps[2]['url_publica'],'/a-lenda-do-sertao/capitulo-3/');self.assertEqual(caps[2]['id'],'obra-1-cap-003')
   self.assertEqual(json.loads((out/'catalogo.json').read_text())[0]['url_publica'],'/a-lenda-do-sertao/')
   busca=json.loads((out/'busca.json').read_text());self.assertTrue(all('leitor.html' not in x['url'] for x in busca['itens']))
   info,rev=p.ler('obra-1/dados/info-obra.json');info['endereco_publico']='outra-rota';p.salvar('obra-1/dados/info-obra.json',info,rev);gerar(root)
   self.assertIn('/outra-rota/capitulo-3/',(out/'a-lenda-do-sertao/capitulo-3/index.html').read_text())

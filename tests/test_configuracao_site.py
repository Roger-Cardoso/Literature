import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from configuracao_site import PADRAO,validar,manifesto_comentarios

class ConfiguracaoSiteTest(unittest.TestCase):
 def test_padrao_desativado_sem_credenciais(self):
  self.assertFalse(validar(copy.deepcopy(PADRAO))['comentarios']['ativado'])
 def test_ativacao_exige_servico_e_chave_publica(self):
  config=copy.deepcopy(PADRAO);config['comentarios']['ativado']=True
  with self.assertRaises(ValueError):validar(config)
  config['comentarios'].update(api_url='https://comments.example',turnstile_site_key='public-key');self.assertTrue(validar(config)['comentarios']['ativado'])
 def test_recusa_enderecos_e_chaves_invalidos(self):
  for valor in ('http://example.com','https://example.com/obra','https://usuario@example.com','https://example.com:8765','https://example.com?q=x'):
   config=copy.deepcopy(PADRAO);config['url_publica']=valor
   with self.assertRaises(ValueError):validar(config)
  config=copy.deepcopy(PADRAO);config['comentarios']['turnstile_site_key']='<script>'
  with self.assertRaises(ValueError):validar(config)
 def test_dominio_deve_corresponder_cname(self):
  with self.assertRaises(ValueError):validar(copy.deepcopy(PADRAO),'outro.example.com')
 def test_migracao_disqus_nao_ativa_nem_exporta_antigas_configuracoes(self):
  novo=validar({'schema_version':1,'url_publica':PADRAO['url_publica'],'disqus':{'ativado':True,'shortname':'antigo'}})
  self.assertEqual(novo['schema_version'],2);self.assertFalse(novo['comentarios']['ativado']);self.assertNotIn('disqus',novo)
 def test_manifesto_apenas_topicos_habilitados_com_ids_estaveis(self):
  config=copy.deepcopy(PADRAO);config['comentarios']['ativado']=True
  info={'id_obra':'obra','titulo':'Título','comentarios':'herdar'};cap={'id':'cap','titulo':'Capítulo','comentarios':'herdar'}
  estrutura={'sagas':[{'volumes':[{'arcos':[{'capitulos':[cap]}]}]}]};resultados=[('slug',info,estrutura,[])]
  manifesto=manifesto_comentarios(config,resultados);self.assertEqual(len(manifesto['threads']),2)
  antigo=manifesto['threads'][1]['id'];cap['titulo']='Novo título';self.assertEqual(manifesto_comentarios(config,resultados)['threads'][1]['id'],antigo)
  info['comentarios']='desativado';cap['comentarios']='ativado';self.assertEqual(manifesto_comentarios(config,resultados)['threads'],[])

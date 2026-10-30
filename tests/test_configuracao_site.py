import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from configuracao_site import PADRAO,validar

class ConfiguracaoSiteTest(unittest.TestCase):
 def test_padrao_desativado_sem_falso_shortname(self):
  self.assertFalse(validar(copy.deepcopy(PADRAO))['disqus']['ativado'])
 def test_ativacao_exige_shortname(self):
  config=copy.deepcopy(PADRAO);config['disqus']['ativado']=True
  with self.assertRaises(ValueError):validar(config)
  config['disqus']['shortname']='literature-real';self.assertTrue(validar(config)['disqus']['ativado'])
 def test_recusa_enderecos_e_shortnames_invalidos(self):
  for valor in ('https://x.disqus.com','x/arquivo','../x','<script>'):
   config=copy.deepcopy(PADRAO);config['disqus']['shortname']=valor
   with self.assertRaises(ValueError):validar(config)
  for valor in ('http://example.com','https://example.com/obra','https://usuario@example.com','https://example.com:8765','https://example.com?q=x'):
   config=copy.deepcopy(PADRAO);config['url_publica']=valor
   with self.assertRaises(ValueError):validar(config)
 def test_dominio_deve_corresponder_cname(self):
  with self.assertRaises(ValueError):validar(copy.deepcopy(PADRAO),'outro.example.com')

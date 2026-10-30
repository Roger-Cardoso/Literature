import copy,sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from identidade_semantica import sincronizar,preparar_importacao,ocorrencias,ids_referenciados

class IdentidadeTest(unittest.TestCase):
 def setUp(self):self.info={'id_obra':'obra-A','personagens':[{'id':'p','nome':'Ana','aliases':['A']} ]}
 def test_primeira_sincronizacao_preserva_divergencias(self):
  for entidade in [{'id':'p','name':'Outro nome','type':'character'},{'id':'p','name':'Local','type':'location'}]:
   entidades,estado=sincronizar({'p':entidade},self.info,{})
   self.assertEqual(entidades['p'],entidade);self.assertIn('p',estado['conflitos'])
 def test_cadastro_alterado_desde_base_atualiza_projecao(self):
  entidades,estado=sincronizar({},self.info,{})
  self.info['personagens'][0]['nome']='Ana atualizada'
  atuais,novo=sincronizar(entidades,self.info,estado)
  self.assertEqual(atuais['p']['name'],'Ana atualizada');self.assertFalse(novo['conflitos'])
 def test_edicao_local_e_concorrente_exigem_revisao(self):
  entidades,estado=sincronizar({},self.info,{});entidades['p']['name']='Edição local'
  _,novo=sincronizar(entidades,self.info,estado);self.assertIn('name',novo['conflitos']['p']['campos'])
  self.info['personagens'][0]['nome']='Edição no cadastro'
  atuais,novo=sincronizar(entidades,self.info,estado);self.assertEqual(atuais['p']['name'],'Edição local');self.assertEqual(novo['bases']['p']['name'],'Ana')
 def test_importacao_com_id_igual_nao_associa_implicitamente(self):
  data={'text':'Intacto','entities':[{'id':'p','name':'Local','type':'location'}],'section':{'data-pov-character':'p'},'semantic':[{'meta':{'data-target':'p','data-target-type':'location'},'start':0,'end':3}]}
  antes=copy.deepcopy(data);novo=preparar_importacao(data,self.info,'hash')
  ident=novo['entities'][0]['id'];self.assertNotEqual(ident,'p');self.assertEqual(novo['section']['data-pov-character'],ident)
  self.assertEqual(novo['semantic'][0]['meta']['data-target-type'],'location');self.assertEqual(novo['integracao_entidades']['importacoes'][0]['ids']['p'],ident);self.assertEqual(data,antes)
 def test_mesma_obra_preserva_origem_e_base(self):
  data={'entities':[{'id':'p','name':'Ana','type':'character'}],'integracao_entidades':{'obra_id':'obra-A','bases':{'p':{'name':'Ana'}}}}
  self.assertEqual(preparar_importacao(data,self.info,'hash'),data)
 def test_importacao_rejeita_ids_repetidos(self):
  with self.assertRaises(ValueError):preparar_importacao({'entities':[{'id':'p','name':'A'},{'id':'p','name':'B'}]},self.info,'hash')
 def test_ocorrencias_distinguem_funcoes_sem_inferir_texto(self):
  data={'text':'Ana','section':{'data-pov-id':'p'},'semantic':[{'id':'m','start':0,'end':3,'meta':{'data-speaker':'p','data-addressee':'outro'}}]}
  self.assertEqual(ids_referenciados(data),{'p','outro'});self.assertEqual([r['funcao'] for r in ocorrencias(data,'p')],['data-pov-character','data-speaker'])
  self.assertEqual(ocorrencias({'text':'Ana'},'p'),[])
 def test_tipo_criatura_nao_e_convertido_em_personagem(self):
  self.info['personagens'][0]['tipo_semantico']='creature';entidades,estado=sincronizar({},self.info,{})
  self.assertEqual(entidades['p']['type'],'creature');self.assertFalse(estado['conflitos'])
if __name__=='__main__':unittest.main()

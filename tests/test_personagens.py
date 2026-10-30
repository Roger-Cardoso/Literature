import copy
import json
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from personagens import validar_catalogo,validar_participacoes,participacoes,personagens_marcados,vincular_entidade
from gestao_projeto import Projeto,hash_arquivo

class PersonagensTest(unittest.TestCase):
 def setUp(self):
  self.info={'personagens':[{'id':'ana','nome':'Ana','aliases':['A']},{'id':'ana-2','nome':'Ana','aliases':[]}]}
  self.arvore={'schema_version':2,'capitulos':[{'id':'cap','titulo':'Capítulo','ordem':1,'arquivo':'texto.html','estado_publicacao':'rascunho','personagens_ids':['ana'],'cenas':[{'id':'cena','titulo_cena':'Cena','personagens_ids':['ana-2'],'visibilidade':'privada'}]}]}
 def test_homonimos_permanecem_distintos(self):self.assertEqual(set(validar_catalogo(self.info)),{'ana','ana-2'})
 def test_referencias_orfas_duplicadas_e_formato_invalido(self):
  for refs in (['ausente'],['ana','ana'],'ana'):
   arvore=copy.deepcopy(self.arvore);arvore['capitulos'][0]['personagens_ids']=refs
   with self.assertRaises(ValueError):validar_participacoes(self.info,arvore)
  self.arvore['capitulos'][0]['cenas'][0]['personagens_ids']=['ausente']
  with self.assertRaises(ValueError):validar_participacoes(self.info,self.arvore)
 def test_consulta_inversa_usa_ids_e_sobrevive_a_renomeacao(self):
  antes=participacoes(self.arvore,'ana');self.info['personagens'][0]['nome']='Nome novo'
  validar_participacoes(self.info,self.arvore);self.assertEqual(participacoes(self.arvore,'ana'),antes)
  self.assertEqual(participacoes(self.arvore,'ana-2')[0]['cena'],'cena');self.assertEqual(antes[0]['cena'],None)
 def test_selecao_inicial_so_inclui_referencias_marcadas_e_canonicas(self):
  data={'text':'Ana citada sem marcação','section':{'data-pov-id':'ana'},'semantic':[{'meta':{'data-speaker':'ana ana-2 externo'}}]}
  self.assertEqual(personagens_marcados(data,self.info),['ana','ana-2'])
  self.assertEqual(personagens_marcados({'text':'Ana'},self.info),[])
 def test_vinculo_atualiza_referencias_preserva_texto_e_intervalos(self):
  data={'text':'Texto intacto','section':{'id':'cap','data-pov-character':'importado'},'sections':[{'id':'sec','start':0,'end':13,'meta':{'data-pov-id':'importado'}}],'semantic':[{'id':'marca','start':0,'end':5,'meta':{'data-role':'dialogue','data-speaker':'importado ana','data-addressee':'ana-2'}}],'entities':[{'id':'importado','name':'Outro nome','type':'character'},{'id':'ana','name':'Nome antigo','type':'character'},{'id':'ana-2','name':'Ana','type':'character'}],'formatting':{'fmt_bold':[[0,5]]}}
  antes=copy.deepcopy(data);novo=vincular_entidade(data,'importado','ana',self.info)
  self.assertEqual(data,antes);self.assertEqual(novo['text'],data['text']);self.assertEqual(novo['formatting'],data['formatting'])
  self.assertEqual(novo['semantic'][0]['meta']['data-speaker'],'ana');self.assertEqual(novo['sections'][0]['meta']['data-pov-id'],'ana')
  self.assertEqual(novo['semantic'][0]['start'],0);self.assertEqual(novo['semantic'][0]['end'],5)
  self.assertEqual([e['id'] for e in novo['entities']].count('ana'),1);self.assertNotIn('importado',[e['id'] for e in novo['entities']])
 def test_vinculo_nao_funde_dois_personagens_do_cadastro(self):
  with self.assertRaises(ValueError):vincular_entidade({'entities':[{'id':'ana','type':'character'}]},'ana','ana-2',self.info)
 def test_metadados_extras_sao_preservados_ou_conflito_bloqueado(self):
  data={'entities':[{'id':'origem','type':'character','name':'Importado','nota':'Texto'},{'id':'ana','type':'character','name':'Ana','cor':'verde'}]}
  novo=vincular_entidade(data,'origem','ana',self.info);alvo=next(e for e in novo['entities'] if e['id']=='ana')
  self.assertEqual(alvo['nota'],'Texto');self.assertEqual(alvo['cor'],'verde')
  data['entities'][1]['nota']='Outra nota'
  with self.assertRaises(ValueError):vincular_entidade(data,'origem','ana',self.info)
 def test_salvar_catalogo_nao_remove_personagem_referenciado(self):
  with tempfile.TemporaryDirectory() as tmp:
   raiz=Path(tmp);(raiz/'obra/dados').mkdir(parents=True);p=Projeto(raiz)
   p.salvar('obra/dados/info-obra.json',self.info,None);p.salvar('obra/dados/editorial.json',self.arvore,None)
   arquivo=raiz/'obra/dados/info-obra.json';antes=arquivo.read_bytes();rev=hash_arquivo(arquivo)
   for payload in ({'personagens':[]},json.dumps({'personagens':[]})):
    with self.assertRaises(ValueError):p.salvar('obra/dados/info-obra.json',payload,rev)
   self.assertEqual(arquivo.read_bytes(),antes)
 def test_exclusao_crud_verifica_texto_autoria_e_revisao(self):
  with tempfile.TemporaryDirectory() as tmp:
   raiz=Path(tmp);(raiz/'obra/dados').mkdir(parents=True);p=Projeto(raiz)
   info=copy.deepcopy(self.info);info['personagens'].append({'id':'livre','nome':'Sem uso'})
   p.salvar('obra/dados/info-obra.json',info,None);p.salvar('obra/dados/editorial.json',self.arvore,None)
   texto=raiz/'obra/texto.html';texto.write_text('<p data-speaker="livre">Fala.</p>')
   arquivo=raiz/'obra/dados/info-obra.json';rev=hash_arquivo(arquivo)
   with self.assertRaises(ValueError):p.excluir_personagem('obra','livre',rev)
   texto.write_text('<p>Texto.</p>');pasta=raiz/'obra/autoria';pasta.mkdir();autoria=pasta/'c.narrproj';autoria.write_text(json.dumps({'section':{'data-pov-character':'livre'}}))
   with self.assertRaises(ValueError):p.excluir_personagem('obra','livre',rev)
   # Um registro de entidade sem marcações é histórico, não participação.
   autoria.write_text(json.dumps({'entities':[{'id':'livre','name':'Sem uso','type':'character'}]}))
   with self.assertRaises(ValueError):p.excluir_personagem('obra','ana',rev)
   with self.assertRaises(ValueError):p.excluir_personagem('obra','livre','revisao-antiga')
   p.excluir_personagem('obra','livre',rev)
   self.assertNotIn('livre',{x['id'] for x in p.ler('obra/dados/info-obra.json')[0]['personagens']})
   self.assertTrue(list((raiz/'.literature-backups').rglob('info-obra.json')))
 def test_ocorrencias_separam_capitulo_aplicado_de_autoria_salva(self):
  with tempfile.TemporaryDirectory() as tmp:
   raiz=Path(tmp);(raiz/'obra/dados').mkdir(parents=True);p=Projeto(raiz)
   p.salvar('obra/dados/info-obra.json',self.info,None);p.salvar('obra/dados/editorial.json',self.arvore,None)
   (raiz/'obra/texto.html').write_text('<p id="m1" data-speaker="ana" data-display-name="???">Fala.</p>')
   (raiz/'obra/autoria').mkdir();(raiz/'obra/autoria/cap.narrproj').write_text(json.dumps({'literature':{'capitulo':'cap'},'semantic':[{'id':'m2','start':0,'end':4,'meta':{'data-thinker':'ana'}}]}))
   refs=p.ocorrencias_personagem('obra','ana')
   self.assertEqual([r['funcao'] for r in refs],['data-speaker','data-thinker'])
   self.assertEqual(refs[0]['origem'],'Capítulo aplicado');self.assertIn('Autoria salva',refs[1]['origem']);self.assertEqual(refs[1]['inicio'],0)
if __name__=='__main__':unittest.main()

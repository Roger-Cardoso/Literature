import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import hierarquia as h

def estrutura(quantidade=4):
 caps=[{'id':f'cap-{i}','titulo':'Capítulo repetido','ordem':i+1,'numero':str(i+10),'arquivo':f'writed/cap-{i}.html','estado_publicacao':'publicado','publicado_em':'2020-01-01','cenas':[{'id':f'cena-{i}','ancora':f'trecho-{i}','visibilidade':'privada'}]} for i in range(quantidade)]
 return {'schema_version':2,'sagas':[{'id':'saga','nome':'Saga','ordem':1,'volumes':[{'id':'volume','nome':'Volume','ordem':1,'arcos':[{'id':'arco-a','nome':'Arco','ordem':1,'capitulos':caps},{'id':'arco-b','nome':'Arco','ordem':2,'capitulos':[]}]}]}]}

class HierarquiaTest(unittest.TestCase):
 def test_apresentacao_ordenada_com_caminho_original(self):
  doc=estrutura();caps=doc['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'];caps.reverse()
  nos=[n for n in h.nos(doc) if n.tipo=='capitulo'];self.assertEqual([n.id for n in nos],['cap-0','cap-1','cap-2','cap-3'])
  self.assertEqual(nos[0].endereco,'1.1.1.1');self.assertEqual(nos[0].caminho[-1],3)
  alvo=doc
  for chave in nos[0].caminho:alvo=alvo[chave]
  self.assertIs(alvo,nos[0].item)
 def test_mover_no_mesmo_grupo_preserva_identidade(self):
  doc=estrutura();antes=copy.deepcopy(doc);novo=h.mover(doc,'cap-0','arco-a',4)
  self.assertEqual(doc,antes)
  caps=h.lista_destino(novo,'capitulo','arco-a');self.assertEqual([c['id'] for c in caps],['cap-1','cap-2','cap-3','cap-0'])
  self.assertEqual([c['ordem'] for c in caps],[1,2,3,4])
  original=h.encontrar(doc,'cap-0').item;movido=h.encontrar(novo,'cap-0').item
  self.assertEqual({k:v for k,v in original.items() if k!='ordem'},{k:v for k,v in movido.items() if k!='ordem'})
 def test_transferir_capitulo_para_arco_vazio(self):
  novo=h.mover(estrutura(),'cap-1','arco-b',1);no=h.encontrar(novo,'cap-1')
  self.assertEqual(no.pai,'arco-b');self.assertEqual(no.endereco,'1.1.2.1')
  self.assertEqual([c['ordem'] for c in h.lista_destino(novo,'capitulo','arco-a')],[1,2,3])
 def test_reordenar_grupo_leva_descendentes(self):
  doc=estrutura();novo=h.mover(doc,'arco-a','volume',2)
  self.assertEqual(h.encontrar(novo,'cap-0').endereco,'1.1.2.1');self.assertEqual(h.encontrar(novo,'cap-0').item,h.encontrar(doc,'cap-0').item)
 def test_transferir_volume_entre_sagas_preserva_descendentes(self):
  doc=estrutura();novo,saga=h.novo_grupo(doc,'saga','Segunda saga',None,2)
  movido=h.mover(novo,'volume',saga,1)
  self.assertEqual(h.encontrar(movido,'cap-0').endereco,'2.1.1.1')
  self.assertEqual(h.encontrar(movido,'cap-0').item,h.encontrar(doc,'cap-0').item)
  self.assertEqual(h.encontrar(movido,'saga').item['volumes'],[])
 def test_rejeita_destinos_posicoes_e_identidades_invalidas(self):
  doc=estrutura()
  for ident,pai,pos in [('cap-0','saga',1),('volume','arco-a',1),('inexistente','arco-a',1),('cap-0','arco-a',0),('cap-0','arco-a',5),('cap-0','arco-b',2)]:
   with self.subTest(ident=ident,pai=pai,pos=pos),self.assertRaises(ValueError):h.mover(doc,ident,pai,pos)
 def test_inserir_grupo_sem_alterar_capitulos(self):
  doc=estrutura();novo,ident=h.novo_grupo(doc,'arco','Novo arco','volume',1)
  self.assertEqual(h.encontrar(novo,ident).endereco,'1.1.1')
  self.assertEqual(h.encontrar(novo,'cap-0').item,h.encontrar(doc,'cap-0').item)
 def test_converter_simples_preserva_metadados(self):
  caps=[n.item for n in h.nos(estrutura()) if n.tipo=='capitulo'];doc={'schema_version':2,'capitulos':caps,'nota_editorial':'Preservar'}
  novo=h.converter_simples(doc);self.assertEqual([n.item for n in h.nos(novo) if n.tipo=='capitulo'],caps)
  self.assertEqual(novo['nota_editorial'],'Preservar');self.assertIn('capitulos',doc);self.assertNotIn('capitulos',novo)
 def test_rejeita_ordens_repetidas_booleanas_e_ids_duplicados(self):
  for campo,valor in [('ordem',1),('ordem',True),('ordem',0),('id','cap-0')]:
   doc=estrutura();h.encontrar(doc,'cap-1').item[campo]=valor
   with self.assertRaises(ValueError):h.validar(doc)
 def test_mil_capitulos_sem_dependencia_da_ordem_fisica(self):
  doc=estrutura(1000);caps=h.lista_destino(doc,'capitulo','arco-a');caps.reverse();h.validar(doc)
  novo=h.mover(doc,'cap-500','arco-b',1)
  self.assertEqual(len([n for n in h.nos(novo) if n.tipo=='capitulo']),1000)
  self.assertEqual(h.encontrar(novo,'cap-500').item['numero'],'510')
  self.assertEqual(h.encontrar(novo,'cap-500').item['arquivo'],'writed/cap-500.html')
if __name__=='__main__':unittest.main()

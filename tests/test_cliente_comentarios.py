import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cliente_comentarios import ClienteComentarios,SemRedirecionamento

class ClienteComentariosTest(unittest.TestCase):
 def test_endereco_secreto_e_redirecionamentos(self):
  with self.assertRaises(ValueError):ClienteComentarios('http://example.com','a'*40)
  with self.assertRaises(ValueError):ClienteComentarios('https://example.com','curto')
  with self.assertRaises(ValueError):SemRedirecionamento().redirect_request(None,None,302,'',{},'https://outro.example')
 def test_autorizacao_somente_no_cabecalho(self):
  c=ClienteComentarios('https://comments.example','s'*40);resposta=Mock();resposta.__enter__=Mock(return_value=resposta);resposta.__exit__=Mock(return_value=None);resposta.read.return_value=b'{"items":[],"next":null}';c._http.open=Mock(return_value=resposta)
  self.assertEqual(c.listar()['items'],[]);req=c._http.open.call_args.args[0]
  self.assertEqual(req.get_header('Authorization'),'Bearer '+'s'*40);self.assertNotIn('s'*40,req.full_url);self.assertEqual(req.get_header('User-agent'),'LiteratureStudio/1.0')
 def test_sincronizacao_em_lotes_e_commit_ao_final(self):
  c=ClienteComentarios('https://comments.example','s'*40);c.chamar=Mock(return_value={'ok':True});c.sincronizar({'schema_version':1,'threads':[{'id':i} for i in range(43)]})
  chamadas=c.chamar.call_args_list;self.assertEqual([len(x.args[2]['threads']) for x in chamadas[:-1]],[20,20,3]);self.assertEqual(chamadas[-1].args[0],'/v1/admin/threads/commit');self.assertEqual(chamadas[-1].args[2]['total'],43)
 def test_falha_em_lote_nao_efetiva_manifesto_parcial(self):
  c=ClienteComentarios('https://comments.example','s'*40);c.chamar=Mock(side_effect=[{},ValueError('falhou')])
  with self.assertRaises(ValueError):c.sincronizar({'schema_version':1,'threads':[{}]*21})
  self.assertFalse(any(x.args[0].endswith('/commit') for x in c.chamar.call_args_list))
 def test_exportacao_com_paginacao_sem_credencial_no_json(self):
  c=ClienteComentarios('https://comments.example','s'*40);c.listar=Mock(side_effect=[{'items':[{'body':'Pendente'}],'next':2},{'items':[{'body':'Oculto'}],'next':None}]);copia=c.exportar();self.assertEqual(len(copia['comentarios']),2);self.assertNotIn('s'*40,json.dumps(copia))
 def test_manifesto_vazio_fecha_discussao_sem_apagar_comentarios(self):
  c=ClienteComentarios('https://comments.example','s'*40);c.chamar=Mock(return_value={});c.sincronizar({'schema_version':1,'threads':[]});self.assertEqual(len(c.chamar.call_args_list),2);self.assertEqual(c.chamar.call_args_list[0].args[2]['threads'],[])

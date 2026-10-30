from pathlib import Path
import json,os,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from implantar_comentarios import gravar_privado,token_oauth,implantar
class ImplantacaoComentariosTest(unittest.TestCase):
 def test_credencial_privada_atomica_e_sem_permissao_publica(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'privado/credencial.json';gravar_privado(path,{'admin_token':'secreto'});self.assertEqual(path.stat().st_mode&0o777,0o600);self.assertEqual(json.loads(path.read_text())['admin_token'],'secreto');self.assertFalse(list(path.parent.glob('.credencial-*')))
 def test_nao_segue_arquivo_privado_simbolico(self):
  with tempfile.TemporaryDirectory() as tmp:
   real=Path(tmp)/'real';real.write_text('preservar');link=Path(tmp)/'link';link.symlink_to(real)
   with self.assertRaises(ValueError):gravar_privado(link,{})
   self.assertEqual(real.read_text(),'preservar')
 def test_recusa_credencial_dentro_do_projeto_antes_da_rede(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):implantar(Path(tmp),arquivo_privado=Path(tmp)/'secreto.json')

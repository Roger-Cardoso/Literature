import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from importar_autoria import importar_html
from integracao_semantica import TextoHTML,sem_runtime,validar_ancoras
class IntegracaoTest(unittest.TestCase):
 def test_importacao_textual_nao_importa_scripts(self):
  p=TextoHTML();p.feed('<p>Texto <b>preservado</b>.</p><script>segredo()</script><p>Outro.</p>')
  self.assertEqual(p.texto(),'Texto preservado.\nOutro.')
 def test_exportacao_mantem_registros_e_remove_execucao(self):
  html='<p>Texto</p><script>alert(1)</script><script id="story-entities" type="application/json">[]</script>'
  novo=sem_runtime(html);self.assertNotIn('alert',novo);self.assertIn('application/json',novo)
 def test_importador_preserva_cenas_e_formatacao(self):
  data,avisos=importar_html('<div class="scene" id="cena-a"><p>Texto <strong>forte</strong>.</p></div><section id="cena-b"><p>Outro texto.</p></section>',{'cenas':[]},{'id':'cap','data-scope':'chapter'},{'roles':{}})
  self.assertEqual({s['id'] for s in data['sections']},{'cena-a','cena-b'})
  a,b=data['formatting']['fmt_bold'][0];self.assertEqual(data['text'][a:b],'forte')
  sec=next(s for s in data['sections'] if s['id']=='cena-a');self.assertEqual(data['text'][sec['start']:sec['end']],'Texto forte.')
 def test_importador_separa_recaptulacao_e_previa(self):
  data,_=importar_html('<details class="recaptulation"><summary>Antes</summary><p>Passado.</p></details><p>Agora.</p><details class="preview"><summary>Próximo</summary><p>Futuro.</p></details>',{'cenas':[]},{'id':'cap'},{'roles':{}})
  self.assertEqual(data['text'],'Agora.');self.assertEqual(data['elements'],{'anteriormente':'Passado.','previa':'Futuro.'})
 def test_reabrir_html_semantico_nao_duplica_secao_principal(self):
  data,_=importar_html('<section id="cap-original" data-scope="chapter"><section id="cena-original" data-scope="scene"><p>Texto.</p></section></section>',{'cenas':[]},{'id':'padrao','data-scope':'chapter'},{'roles':{}})
  self.assertEqual(data['section']['id'],'cap-original')
  self.assertEqual([s['id'] for s in data['sections']],['cena-original'])
 def test_glossario_e_inline_preservados_com_intervalo(self):
  data,avisos=importar_html('<p>Veja <span data-glossary-term="lua">lua</span> e <abbr title="Organização">ONU</abbr>.</p>',{'cenas':[]},{},{'roles':{}})
  termo=next(x for x in data['inline_structures'] if 'data-glossary-term' in x['attrs'])
  self.assertEqual(data['text'][termo['start']:termo['end']],'lua')
  self.assertEqual(termo['attrs']['data-glossary-term'],'lua')
  self.assertEqual(next(x for x in data['inline_structures'] if x['element']=='abbr')['attrs']['title'],'Organização')
  self.assertTrue(any('1 ligações de glossário' in aviso for aviso in avisos))
 def test_alias_normalizado_e_perda_sinalizada(self):
  data,avisos=importar_html('<p data-locutor-id="ana rui" data-funcao-nova="x">Olá.</p>',{'cenas':[]},{},{'roles':{'dialogue':{}}})
  self.assertEqual(data['semantic'][0]['meta']['data-speaker'],'ana rui')
  self.assertNotIn('data-locutor-id',data['semantic'][0]['meta'])
  # Atributos de uma função são preservados, mesmo quando ainda não têm UI própria.
  self.assertEqual(data['semantic'][0]['meta']['data-funcao-nova'],'x')
  _,avisos=importar_html('<p data-funcao-nova="x">Olá.</p>',{'cenas':[]},{},{'roles':{}})
  self.assertIn('Marcação sem reconstrução: data-funcao-nova',avisos)
 def test_ancoras_do_guia_preservadas(self):
  cenas=[{'ancora':'a','visibilidade':'publica'},{'ancora':'b','visibilidade':'publica'}]
  validar_ancoras('<section id="a"></section><section id="b"></section>',cenas)
  for html in ('<section id="a"></section>','<section id="b"></section><section id="a"></section>','<p id="a"></p><p id="a"></p>'):
   with self.assertRaises(ValueError):validar_ancoras(html,cenas)
if __name__=='__main__':unittest.main()

"""Garante a conexão real entre as páginas e a interface de comentários."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class Pagina(HTMLParser):
 def __init__(self,html):
  super().__init__();self.scripts=[];self.secoes=[];self.css=[];self.reacoes=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='script':self.scripts.append(a.get('src',''))
  if tag=='section' and a.get('id')=='comentarios':self.secoes.append(a)
  if tag=='section' and a.get('id')=='reacoes':self.reacoes.append(a)
  if tag=='link' and a.get('rel')=='stylesheet':self.css.append(a.get('href',''))
class PaginasComentariosTest(unittest.TestCase):
 def test_modelos_e_paginas_existentes_carregam_interface_uma_vez(self):
  paginas=[ROOT/'scripts/modelos/obra'/p for p in ('index-obra.html','leitor.html')]
  paginas.extend(p for p in ROOT.glob('*/index-obra.html') if p.parent.name!='site')
  paginas.extend(p for p in ROOT.glob('*/leitor.html') if p.parent.name!='site')
  for caminho in paginas:
   with self.subTest(pagina=str(caminho.relative_to(ROOT))):
    html=caminho.read_text();p=Pagina(html)
    self.assertEqual(len(p.secoes),1);self.assertIn('hidden',p.secoes[0]);self.assertEqual(sum('/comentarios.js' in s for s in p.scripts),1);self.assertEqual(sum('/comentarios.css' in s for s in p.css),1)
    self.assertEqual(len(p.reacoes),1);self.assertIn('hidden',p.reacoes[0]);self.assertEqual(sum('/reacoes.js' in x for x in p.scripts),1);self.assertEqual(sum('/reacoes.css' in x for x in p.css),1)
    if caminho.name=='leitor.html':self.assertLess(next(i for i,s in enumerate(p.scripts) if '/comentarios.js' in s),next(i for i,s in enumerate(p.scripts) if '/leitor.js' in s))
    else:self.assertIn('ComentariosLiterature?.montar',html);self.assertIn('ReacoesLiterature?.montar',html)

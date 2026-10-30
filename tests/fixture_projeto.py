"""Obras sintéticas para testes; nunca recria obras no diretório autoral."""
from pathlib import Path
import json
import shutil

def preparar_fixture(root):
 root=Path(root)
 # Só se chama em diretórios temporários de teste.
 from gestao_projeto import Projeto
 p=Projeto(root)
 for slug in ('obra-1','obra-2'):
  if slug in p.obras():
   registro,rev=p.ler('obras.json');registro['obras'].remove(slug);p.salvar('obras.json',registro,rev)
  if (root/slug).exists():shutil.rmtree(root/slug)
  p.nova_obra(slug,'Obra de teste '+slug,'Autoria fictícia')
  info,rev=p.ler(f'{slug}/dados/info-obra.json');info.update(id_obra='fixture-'+slug,estado_publicacao='publicado' if slug=='obra-1' else 'rascunho',sinopse='Uma história fictícia para testes.',personagens=[{'id':'fixture-'+slug+'-ana','nome':'Ana','aliases':['Aninha']},{'id':'fixture-'+slug+'-bia','nome':'Bia','aliases':[]}]);p.salvar(f'{slug}/dados/info-obra.json',info,rev)
  caps=[{'id':f'{slug}-cap-{i:03}','titulo':f'Capítulo {i}','ordem':i,'numero':str(i),'arquivo':f'writed/{i}.html','estado_publicacao':'publicado','publicado_em':'2020-01-01','sinopse':'Trecho de teste.','cenas':[]} for i in (1,2,3)]
  for c in caps:
   ancora=c['id']+'-trecho'
   c['cenas']=[{'id':c['id']+'-cena','ancora':ancora,'titulo_cena':'Cena de teste','visibilidade':'privada','relevancia':'nao_avaliada','avaliacao_conteudo':'pendente','avisos_conteudo':[]}]
   (root/slug/c['arquivo']).write_text(f'<section id="{ancora}"><p>Texto fictício para teste de leitura.</p></section>',encoding='utf-8')
  arvore={'schema_version':2,'sagas':[{'id':slug+'-saga','nome':'Saga','ordem':1,'volumes':[{'id':slug+'-volume','nome':'Volume','ordem':1,'arcos':[{'id':slug+'-arco','nome':'Arco','ordem':1,'capitulos':caps},{'id':slug+'-arco-vazio','nome':'Outro arco','ordem':2,'capitulos':[]}]}]}]}
  _,rev=p.ler(f'{slug}/dados/editorial.json');p.salvar(f'{slug}/dados/editorial.json',arvore,rev)
 # Fixtures não contam como backups produzidos pela operação sob teste.
 shutil.rmtree(root/'.literature-backups',ignore_errors=True)

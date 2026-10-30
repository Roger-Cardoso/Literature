"""Resolução de identidades e comparação entre cadastro, base salva e autoria."""
import copy
import uuid
from personagens import validar_catalogo,remapear_meta
from contrato_semantico import normalizar_atributos,REFERENCIAS

def ficha_entidade(p):
 return {'id':p['id'],'name':p['nome'],'type':p.get('tipo_semantico','character'),'aliases':list(p.get('aliases',[]))}

def ids_referenciados(data):
 metas=[data.get('section',{}),*[x.get('meta',{}) for x in data.get('sections',[])],*[x.get('meta',{}) for x in data.get('semantic',[])]]
 return set(x for meta in metas for k,v in normalizar_atributos(meta).items() if k in REFERENCIAS for x in (v if isinstance(v,list) else str(v or '').split()))

def sincronizar(entidades,info,estado):
 catalogo=validar_catalogo(info);atuais=copy.deepcopy(entidades);novo=copy.deepcopy(estado or {})
 if novo.get('obra_id') not in (None,info['id_obra']):raise ValueError('A autoria pertence a outra obra. Importe e confira suas identidades.')
 novo.setdefault('versao',1);novo['obra_id']=info['id_obra'];bases=novo.setdefault('bases',{});conflitos={}
 for ident,p in catalogo.items():
  canon=ficha_entidade(p);local=atuais.get(ident);base=bases.get(ident)
  if local is None:atuais[ident]=canon;bases[ident]=copy.deepcopy(canon);continue
  campos=('name','type','aliases');problemas=[]
  for campo in campos:
   l=local.get(campo,[] if campo=='aliases' else None);c=canon[campo];b=base.get(campo,[] if campo=='aliases' else None) if base else None
   if l==c:continue
   if base and l==b:continue  # somente o cadastro mudou
   if base and c==b:problemas.append(campo)  # alteração local exige proposta explícita
   elif not base and campo=='aliases' and not l:continue
   else:problemas.append(campo)
  if problemas:conflitos[ident]={'cadastro':canon,'autoria':copy.deepcopy(local),'base':copy.deepcopy(base),'campos':problemas};continue
  atuais[ident]={**local,**canon};bases[ident]=copy.deepcopy(canon)
 novo['conflitos']=conflitos
 return atuais,novo

def preparar_importacao(data,info,origem):
 novo=copy.deepcopy(data);entidades=novo.get('entities',[])
 if not isinstance(entidades,list) or any(not isinstance(e,dict) or not isinstance(e.get('id'),str) or not e['id'] or not isinstance(e.get('name'),str) for e in entidades):raise ValueError('Entidades importadas devem ter ID e nome.')
 if len({e['id'] for e in entidades})!=len(entidades):raise ValueError('A autoria importada contém IDs de entidade repetidos.')
 estado=novo.get('integracao_entidades',{})
 if estado.get('obra_id')==info['id_obra']:return novo
 catalogo=validar_catalogo(info);mapeamento={};ocupados=set(catalogo)|{e['id'] for e in novo.get('entities',[])}
 for e in novo.get('entities',[]):
  if e['id'] in catalogo:
   antigo=e['id'];ident='importada-'+uuid.uuid4().hex
   while ident in ocupados:ident='importada-'+uuid.uuid4().hex
   ocupados.add(ident);mapeamento[antigo]=ident;e['id']=ident
 for antigo,ident in mapeamento.items():
  # Remapeamento de importação preserva o tipo original do alvo.
  for meta in [novo.get('section',{}),*[x.get('meta',{}) for x in novo.get('sections',[])],*[x.get('meta',{}) for x in novo.get('semantic',[])]]:
   alvo=meta.get('data-target-type');resultado=remapear_meta(meta,antigo,ident)
   if alvo is not None:resultado['data-target-type']=alvo
   meta.clear();meta.update(resultado)
 novo['integracao_entidades']={'versao':1,'obra_id':info['id_obra'],'bases':{},'conflitos':{},'importacoes':[*copy.deepcopy(estado.get('importacoes',[])),{'origem':origem,'obra_origem':estado.get('obra_id'),'obra_destino':info['id_obra'],'ids':mapeamento}],'vinculos_anteriores':[*copy.deepcopy(estado.get('vinculos_anteriores',[])),*([{'obra_id':estado.get('obra_id'),'vinculos':copy.deepcopy(estado['vinculos'])}] if estado.get('vinculos') else [])]}
 return novo

def ocorrencias(data,personagem_id):
 resultado=[]
 for meta,ident,inicio,fim in [(data.get('section',{}),'capítulo',None,None),*[(s.get('meta',{}),s.get('id'),s.get('start'),s.get('end')) for s in data.get('sections',[])],*[(s.get('meta',{}),s.get('id'),s.get('start'),s.get('end')) for s in data.get('semantic',[])]]:
  for campo,valor in normalizar_atributos(meta).items():
   if campo in REFERENCIAS and personagem_id in (valor if isinstance(valor,list) else str(valor or '').split()):resultado.append({'id':ident,'funcao':campo,'inicio':inicio,'fim':fim})
 return resultado

def ocorrencias_html(html,personagem_id):
 from html.parser import HTMLParser
 class Parser(HTMLParser):
  def __init__(self):super().__init__();self.resultado=[]
  def handle_starttag(self,tag,attrs):
   meta=normalizar_atributos(attrs)
   for campo,valor in meta.items():
    if campo in REFERENCIAS and personagem_id in str(valor or '').split():self.resultado.append({'funcao':campo,'id':meta.get('data-text-id',meta.get('id','trecho marcado')),'inicio':None,'fim':None})
 p=Parser();p.feed(html);return p.resultado

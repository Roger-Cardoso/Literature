"""Converte o HTML editorial suportado em autoria, preservando IDs de cenas."""
from html.parser import HTMLParser
import json
import re
import uuid
from contrato_semantico import normalizar_atributos
from editor_semantico.editor_semantico import INLINE_ELEMENTS

def importar_html(html,capitulo,section_meta,schema):
 class Importador(HTMLParser):
  def __init__(self):
   super().__init__();self.texto='';self.stack=[];self.sections=[];self.semantic=[];self.formatting={};self.inline=[];self.hrs=[];self.lists=[];self.elements={};self.entities=[];self.glossary={};self.report=[];self.especial=None;self.buffer=[];self.script=None;self.skip=0;self.raiz=None
  def quebra(self):
   if self.texto and not self.texto.endswith('\n'):self.texto+='\n'
  def handle_starttag(self,t,attrs):
   a=normalizar_atributos(attrs)
   if t in ('script','style'):
    self.skip+=1;self.script=a.get('id') if t=='script' and a.get('type')=='application/json' else None;self.buffer=[];return
   if self.skip:return
   if t=='details':
    tipo='anteriormente' if 'recaptulation' in a.get('class','') or 'story-previous' in a.get('class','') else 'previa' if 'preview' in a.get('class','') or 'story-preview' in a.get('class','') else None
    if tipo:self.quebra();self.especial=tipo;self.buffer=[]
   if self.especial:
    self.stack.append((t,{'especial':True,'summary':t=='summary'},len(self.texto)));return
   if t in ('p','h1','h2','h3','li','section') or t=='div' and 'scene' in a.get('class','').split():self.quebra()
   inicio=len(self.texto);meta={}
   if t in ('strong','b','em','i','u'):meta['fmt']={'strong':'fmt_bold','b':'fmt_bold','em':'fmt_italic','i':'fmt_italic','u':'fmt_underline'}[t]
   if a.get('id') and (t=='section' or 'scene' in a.get('class','').split() or any(c.get('ancora')==a['id'] for c in capitulo.get('cenas',[]))):meta['section']={'id':a['id'],'data-scope':a.get('data-scope','scene'),**{k:v for k,v in a.items() if k.startswith('data-pov-')}}
   role=a.get('data-role')
   if t in ('h1','h2','h3') and not role:role='title';a.update({'data-role':'title','data-title-level':'chapter' if t=='h1' else 'scene'})
   if role in schema.get('roles',{}):meta['semantic']={k:v for k,v in a.items() if k.startswith('data-') and k not in ('data-text-id','data-structure-id')};meta['semantic']['data-role']=role
   elif role:self.report.append('Função não representada: '+role)
   if t in INLINE_ELEMENTS:
    allowed=set(INLINE_ELEMENTS[t]['attrs']) | {'data-glossary-term','data-verbete-id'} if t=='span' else set(INLINE_ELEMENTS[t]['attrs'])
    meta['inline']={'element':t,'attrs':{k:v for k,v in a.items() if k in allowed}}
   preservados={'data-role','data-text-id','data-structure-id'}
   if 'semantic' in meta:preservados.update(meta['semantic'])
   if 'section' in meta:preservados.update(meta['section'])
   if 'inline' in meta:preservados.update(meta['inline']['attrs'])
   for k in a:
    if k.startswith('data-') and k not in preservados:self.report.append('Marcação sem reconstrução: '+k)
   if any(k.startswith('on') for k in a):self.report.append('Interações JavaScript do HTML não são importadas.')
   if t not in ('p','h1','h2','h3','div','section','strong','b','em','i','u','hr','br','ul','ol','li','span') and t not in INLINE_ELEMENTS:self.report.append('Elemento sem reconstrução específica: '+t)
   if t in ('ul','ol'):meta['list']=t
   if t=='hr':self.quebra();self.hrs.append({'id':a.get('id','hr-'+uuid.uuid4().hex),'offset':len(self.texto)});return
   if t=='br':self.texto+='\n';return
   self.stack.append((t,meta,inicio))
  def handle_endtag(self,t):
   if t in ('script','style'):
    if self.script:
     try:
      valor=json.loads(''.join(self.buffer))
      if self.script=='story-entities':
       if isinstance(valor,list) and all(isinstance(x,dict) and x.get('id') and x.get('name') for x in valor):self.entities=valor
       else:self.report.append('Registro de entidades sem reconstrução: esperado lista com id e name.')
      if self.script=='story-glossary':
       if isinstance(valor,dict) and all(isinstance(x,str) for x in valor.values()):self.glossary=valor
       else:self.report.append('Registro de glossário sem reconstrução: esperado objeto de definições textuais.')
     except ValueError:self.report.append('Registro JSON inválido: '+self.script)
    self.skip=max(0,self.skip-1);self.script=None;return
   if self.skip:return
   if self.especial:
    if t=='details':self.elements[self.especial]=' '.join(''.join(self.buffer).split());self.especial=None;self.buffer=[]
    if self.stack and self.stack[-1][0]==t:self.stack.pop()
    return
   pos=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i][0]==t),None)
   if pos is None:return
   _,meta,inicio=self.stack.pop(pos);fim=len(self.texto.rstrip('\n '))
   if fim>inicio:
    if 'inline'in meta:self.inline.append({'id':'inline-'+uuid.uuid4().hex,'start':inicio,'end':fim,**meta['inline']})
    if 'fmt'in meta:self.formatting.setdefault(meta['fmt'],[]).append([inicio,fim])
    if 'section'in meta:
     sec=meta['section']
     if sec.get('data-scope')=='chapter' and self.raiz is None:self.raiz=sec
     else:self.sections.append({'id':sec['id'],'start':inicio,'end':fim,'meta':sec})
    if 'semantic'in meta:self.semantic.append({'id':'text-'+uuid.uuid4().hex,'start':inicio,'end':fim,'meta':meta['semantic']})
    if 'list'in meta:self.lists.append({'id':'list-'+uuid.uuid4().hex,'type':meta['list'],'start':inicio,'end':fim})
   if t in ('p','h1','h2','h3','li','section'):self.quebra()
  def handle_data(self,d):
   if self.skip:
    if self.script:self.buffer.append(d)
    return
   if self.especial:
    if not any(m.get('summary') for _,m,_ in self.stack):self.buffer.append(d)
    return
   # Indentação do código HTML fora dos parágrafos não vira texto de autoria.
   if not d.strip():
    if self.stack and self.stack[-1][0] in ('strong','b','em','i','u','span') and self.texto and not self.texto.endswith((' ','\n')):self.texto+=' '
    return
   texto=re.sub(r'\s+',' ',d)
   if self.texto.endswith(('\n',' ')) or not self.texto:texto=texto.lstrip()
   self.texto+=texto
 p=Importador();p.feed(html);p.close()
 data={'version':5,'text':p.texto.rstrip(),'section':p.raiz or section_meta,'sections':p.sections,'semantic':p.semantic,'formatting':p.formatting,'inline_structures':p.inline,'horizontal_rules':p.hrs,'lists':p.lists,'elements':p.elements,'entities':p.entities,'glossary':p.glossary}
 resumo=f"Importação: {len(p.sections)} cenas/seções; {len(p.semantic)} marcações narrativas; {sum('data-glossary-term' in x['attrs'] or 'data-verbete-id' in x['attrs'] for x in p.inline)} ligações de glossário preservadas."
 return data,[resumo,*sorted(set(p.report))]

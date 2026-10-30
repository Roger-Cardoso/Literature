"""Ponte explícita entre autoria .narrproj e o capítulo publicado do Literature."""
from rolagem import TextoRolavel
import argparse
import hashlib
import difflib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import copy
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from importar_autoria import importar_html
from contrato_semantico import validar_referencias
from personagens import validar_catalogo,personagens_marcados,vincular_entidade,remapear_meta
from seletor_personagens import SeletorPersonagens
from gestao_projeto import Projeto,ROOT,hash_arquivo
from editor_componente import SemanticWidget, OverlayPanel
from identidade_semantica import sincronizar,preparar_importacao,ids_referenciados,ficha_entidade
from entidades_visual import EntidadesMixin,instalar
instalar()

class TextoHTML(HTMLParser):
 def __init__(self):super().__init__();self.partes=[];self.ignorar=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.ignorar+=1
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.ignorar=max(0,self.ignorar-1)
  elif tag in ('p','h1','h2','h3','li','summary'):self.partes.append('\n')
 def handle_data(self,d):
  if not self.ignorar:self.partes.append(d)
 def texto(self):return '\n'.join(' '.join(linha.split()) for linha in ''.join(self.partes).splitlines() if linha.strip())

def sem_runtime(html):
 return re.sub(r'<script(?![^>]*type=["\']application/json["\'])[^>]*>[\s\S]*?</script>','',html,flags=re.I)

def validar_ancoras(html,cenas):
 class IDs(HTMLParser):
  def __init__(self):super().__init__();self.ids=[]
  def handle_starttag(self,t,attrs):self.ids.extend(v for k,v in attrs if k=='id')
 p=IDs();p.feed(html)
 if len(p.ids)!=len(set(p.ids)):raise ValueError('O HTML exportado tem IDs duplicados.')
 indices=[]
 for c in cenas:
  if c.get('visibilidade')!='publica':continue
  if c.get('ancora') not in p.ids:raise ValueError('A cena do guia perdeu sua âncora: '+str(c.get('ancora'))+'. Recrie a seção com essa identidade no editor antes de aplicar.')
  indices.append(p.ids.index(c['ancora']))
 if indices!=sorted(indices):raise ValueError('A ordem das cenas mudou. Revise o guia no gerenciador antes de aplicar.')

class EditorLiterature(EntidadesMixin,SemanticWidget):
 def __init__(self,parent,slug=None,capid=None,ao_aplicar=None):
  self.projeto_lit=Projeto();self.vinculo=None;self.rev_projeto=None
  self.ao_aplicar=ao_aplicar;self._nomes_canonicos={};self.estado_entidades={};self._cadastro_personagens={}
  super().__init__(parent)
  if self._initialization_failed:return
  self.title('Literature Studio — Editor semântico')
  primeiro=next(w for w in self.winfo_children() if w.winfo_manager()=='pack')
  barra=ttk.Frame(self,padding=(10,6));barra.pack(side='top',fill='x',before=primeiro)
  barra.columnconfigure(0,weight=1);barra.columnconfigure(1,weight=1)
  ttk.Button(barra,text='Revisar e aplicar ao capítulo…',style='Accent.TButton',command=self.revisar).grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,5))
  ttk.Button(barra,text='Entidades e identidades…',command=self.gerenciar_identidades).grid(row=2,column=0,sticky='ew',padx=(0,5),pady=(5,0))
  ttk.Button(barra,text='Participações do capítulo…',command=self.participacoes_capitulo).grid(row=2,column=1,sticky='ew',pady=(5,0))
  ttk.Button(barra,text='Recursos da obra…',command=self.compartilhar_recursos).grid(row=1,column=0,sticky='ew',padx=(0,5))
  ttk.Button(barra,text='Reabrir HTML do capítulo…',command=self.importar_texto).grid(row=1,column=1,sticky='ew')
  if slug and capid:
   arvore,_=self.projeto_lit.ler(f'{slug}/dados/editorial.json')
   cap=next((c for _,c in self.projeto_lit.capitulos(arvore) if c['id']==capid),None)
   if not cap:raise ValueError('Capítulo não encontrado.')
   alvo=f'{slug}/{cap["arquivo"]}';self.vinculo={'slug':slug,'capitulo':capid,'alvo':alvo,'base':hash_arquivo(self.projeto_lit.caminho(alvo))}
   pasta=ROOT/slug/'autoria';pasta.mkdir(exist_ok=True)
   self.project_path=pasta/(capid+'.narrproj')
   if self.project_path.exists():
    data=json.loads(self.project_path.read_text(encoding='utf-8'));self.abrir_autoria(data)
    antigo=data.get('literature')
    if antigo and antigo.get('alvo')==alvo:self.vinculo=antigo
    self.rev_projeto=hash_arquivo(self.project_path)
    self.recuperar_cenas_exatas(cap)
   else:
    self.carregar_html_capitulo(cap)
   self.refresh_project_identity()
   self.update_status();self.sincronizar_recursos()
 def sincronizar_recursos(self):
  if not self.vinculo:return
  info,_=self.projeto_lit.ler(self.vinculo['slug']+'/dados/info-obra.json')
  self._cadastro_personagens=validar_catalogo(info)
  entidades,estado=sincronizar(self.entities,info,self.estado_entidades)
  if entidades!=self.entities or estado!=self.estado_entidades:self.dirty=True
  self.entities=entidades;self.estado_entidades=estado
  # Definições públicas da obra ficam disponíveis para marcação, sem inferência.
  for v in info.get('lore',[]):self.glossary.setdefault(v['titulo'],v['descricao'])
  if hasattr(self,'refresh_entities'):self.refresh_entities()
  self.update_status()
 def vincular_personagens(self):
  if not self.vinculo:self.notify('Vincular personagens','Abra um capítulo da obra.','info');return
  path=self.vinculo['slug']+'/dados/info-obra.json';info,rev=self.projeto_lit.ler(path);catalogo=validar_catalogo(info)
  origens=[e for e in self.entities.values() if e.get('type') in {'character','creature'} and e['id'] not in catalogo]
  painel=OverlayPanel(self,'Vincular personagem da autoria ao cadastro',width=850,height=690)
  ttk.Label(painel.body,text='Escolha uma entidade importada e o personagem que ela representa no cadastro da obra. O vínculo substituirá suas referências de fala, pensamento, destinatário, alvo e POV. Texto, intervalos, formatação e histórico de escrita serão preservados.',wraplength=730).pack(anchor='w',pady=8)
  if not origens or not catalogo:
   ttk.Label(painel.body,text='Não há personagens da autoria sem vínculo, ou ainda não há personagens cadastrados na obra. Cadastre o personagem no Studio antes de vinculá-lo.',wraplength=730).pack();return
  ttk.Label(painel.body,text='Personagem da autoria ainda não vinculado').pack(anchor='w',pady=6)
  origens.sort(key=lambda e:(e.get('name',''),e['id']));origem=ttk.Combobox(painel.body,state='readonly',values=[e.get('name','')+' — '+e['id'] for e in origens]);origem.pack(fill='x');origem.current(0)
  ttk.Label(painel.body,text='Personagem existente na obra — busque por nome ou apelido').pack(anchor='w',pady=6)
  destino=SeletorPersonagens(painel.body,info['personagens'],multiplo=False);destino.pack(fill='x')
  resumo=tk.StringVar();ttk.Label(painel.body,textvariable=resumo,wraplength=730).pack(anchor='w',pady=12);proposta={}
  def revisar():
   try:
    ident=destino.get();de=origens[origem.current()]['id'];antes=self.project_data();novo=vincular_entidade(antes,de,ident,info)
    proposta.update(antes=antes,de=de,para=ident)
    alteracoes=sum(x.get('meta')!=y.get('meta') for campo in ('sections','semantic') for x,y in zip(antes.get(campo,[]),novo.get(campo,[])))+int(antes.get('section')!=novo.get('section'))
    resumo.set('Vincular '+origens[origem.current()].get('name',de)+' → '+catalogo[ident]['nome']+' ('+ident+f'). {alteracoes} marcação(ões)/seção(ões) serão atualizadas. A entidade da autoria usará o ID do cadastro. Depois, revise a aplicação ao capítulo.')
    aplicar.configure(state='normal')
   except Exception as e:painel.set_error(str(e))
  def gravar():
   try:
    if destino.get()!=proposta.get('para') or origens[origem.current()]['id']!=proposta.get('de') or self.project_data()!=proposta.get('antes'):raise ValueError('A seleção ou a autoria mudou. Confira o vínculo novamente.')
    if hash_arquivo(self.projeto_lit.caminho(path))!=rev:raise ValueError('O cadastro mudou. Reabra este painel antes de vincular.')
    novo=vincular_entidade(self.project_data(),proposta['de'],proposta['para'],info)
    self.entities={e['id']:e for e in novo['entities']};self.section_meta=novo['section']
    for item in self.subsections.values():item['meta']=remapear_meta(item['meta'],proposta['de'],proposta['para'],catalogo[proposta['para']].get('tipo_semantico','character'))
    for item in self.marks.values():item['meta']=remapear_meta(item['meta'],proposta['de'],proposta['para'],catalogo[proposta['para']].get('tipo_semantico','character'))
    pessoa=catalogo[proposta['para']];self.estado_entidades.setdefault('bases',{})[proposta['para']]=ficha_entidade(pessoa)
    self.estado_entidades.setdefault('vinculos',[]).append({'entidade_origem':proposta['de'],'personagem':proposta['para']})
    for ident in (proposta['de'],proposta['para']):self.estado_entidades.get('conflitos',{}).pop(ident,None)
    self.dirty=True;self.update_status();painel.close()
   except Exception as e:painel.set_error(str(e))
  ttk.Button(painel.footer,text='Conferir vínculo',command=revisar).pack(side='left',padx=6)
  aplicar=ttk.Button(painel.footer,text='Aplicar vínculo à autoria',command=gravar,state='disabled');aplicar.pack(side='left',padx=6)
  self._vinculo_personagens_ui=(origem,destino)
 def participacoes_capitulo(self):
  if not self.vinculo:self.notify('Participações','Abra um capítulo da obra.','info');return
  slug=self.vinculo['slug'];info,_=self.projeto_lit.ler(slug+'/dados/info-obra.json');path=slug+'/dados/editorial.json';arvore,rev=self.projeto_lit.ler(path)
  cap=next(c for _,c in self.projeto_lit.capitulos(arvore) if c['id']==self.vinculo['capitulo'])
  marcados=personagens_marcados(self.project_data(),info);iniciais=list(dict.fromkeys([*cap.get('personagens_ids',[]),*marcados]))
  painel=OverlayPanel(self,'Participações — '+cap['titulo'],width=800,height=570)
  ttk.Label(painel.body,text='A seleção inicial reúne as participações cadastradas e os personagens do cadastro referenciados nas marcações da autoria atual. Revise a seleção antes de aplicar. Esta associação editorial não afirma presença física nem modifica o texto.',wraplength=680).pack(anchor='w',pady=10)
  seletor=SeletorPersonagens(painel.body,info.get('personagens',[]),iniciais);seletor.pack(fill='both',expand=True)
  def aplicar():
   try:
    cap['personagens_ids']=seletor.ids();self.projeto_lit.organizar(slug,arvore,rev);painel.close()
    if self.ao_aplicar:self.ao_aplicar(self.vinculo)
   except Exception as e:painel.set_error(str(e))
  ttk.Button(painel.footer,text='Aplicar participações ao capítulo com backup',command=aplicar).pack(pady=8)
  self._participacoes_ui=seletor
 def compartilhar_recursos(self):
  if not self.vinculo:self.notify('Recursos','Selecione um capítulo no Studio.','info');return
  path=self.vinculo['slug']+'/dados/info-obra.json';info,rev=self.projeto_lit.ler(path);novo=copy.deepcopy(info)
  # Personagens são administrados no cadastro ou por propostas individuais.
  for termo,definicao in self.glossary.items():
   v=next((v for v in novo.get('lore',[]) if v['titulo']==termo),None)
   if v:v['descricao']=definicao
   else:novo.setdefault('lore',[]).append({'id':'verbete-'+uuid.uuid4().hex,'titulo':termo,'descricao':definicao,'categoria':'glossario'})
  painel=OverlayPanel(self,'Revisar recursos da obra',width=850,height=600)
  texto=TextoRolavel(painel.body,wrap='word');texto.pack(fill='both',expand=True)
  texto.insert('1.0',''.join(difflib.unified_diff(json.dumps(info,ensure_ascii=False,indent=2).splitlines(True),json.dumps(novo,ensure_ascii=False,indent=2).splitlines(True),fromfile='Recursos atuais',tofile='Proposta do editor')) or 'Nenhuma alteração.');texto.configure(state='disabled')
  def aplicar():
   try:
    self.projeto_lit.salvar(path,novo,rev);painel.close()
    if self.ao_aplicar:self.ao_aplicar(self.vinculo)
   except Exception as e:self.notify('Recursos',str(e),'error')
  ttk.Button(painel.footer,text='Aplicar recursos revisados',command=aplicar).pack()
 def abrir_autoria(self,data):
  self.estado_entidades=copy.deepcopy(data.get('integracao_entidades',{}))
  super().abrir_autoria(data)
 def project_data(self):
  data=super().project_data();usados=ids_referenciados(data)|set(self.estado_entidades.get('conflitos',{}))
  data['entities']=[e for e in data['entities'] if e['id'] not in self._cadastro_personagens or e['id'] in usados]
  estado=copy.deepcopy(self.estado_entidades);estado['bases']={k:v for k,v in estado.get('bases',{}).items() if k in usados}
  data['integracao_entidades']=estado
  if self.vinculo:data['literature']=copy.deepcopy(self.vinculo)
  return data
 def build_html(self):
  html=super().build_html();data=self.project_data();usados=ids_referenciados(data)
  entidades=[e for e in data['entities'] if e['id'] in usados]
  registro=json.dumps(entidades,ensure_ascii=False,indent=2).replace('<','\\u003c')
  return re.sub(r'(<script id="story-entities" type="application/json">)[\s\S]*?(</script>)',lambda m:m[1]+'\n'+registro+'\n'+m[2],html)
 def validate_document(self):
  if self.vinculo:self.sincronizar_recursos()
  problemas=super().validate_document()
  if self.estado_entidades.get('conflitos'):problemas.append('Concilie as divergências em Entidades e identidades antes de aplicar ou exportar.')
  return problemas
 def save_project(self):
  if self.project_path is None:return self.save_project_as()
  try:
   rel=self.project_path.resolve().relative_to(ROOT)
   revisao=self.rev_projeto
   # Salvar como escolheu um destino novo: não sobrescreve arquivo existente sem abri-lo.
   if self.project_path.exists() and revisao is None:raise ValueError('Abra o projeto existente antes de sobrescrevê-lo, ou escolha outro nome.')
   self.rev_projeto=self.projeto_lit.salvar(rel,self.project_data(),revisao)
  except Exception as e:self.notify('Salvar autoria',str(e),'error');return False
  self.dirty=False;self.refresh_project_identity();self.update_status();return True
 def save_project_as(self):
  path=filedialog.asksaveasfilename(parent=self,title='Salvar autoria no projeto Literature',initialdir=str(ROOT),defaultextension='.narrproj',filetypes=[('Autoria narrativa','*.narrproj')])
  if not path:return False
  anterior,rev=self.project_path,self.rev_projeto
  self.project_path=Path(path);self.rev_projeto=None
  if self.project_path==anterior:self.rev_projeto=rev
  if self.save_project():return True
  self.project_path,self.rev_projeto=anterior,rev;return False
 def export_html(self):
  problemas=self.validate_document()
  if problemas:self.notify('Exportação','Corrija as marcações antes de exportar:\n'+'\n'.join(problemas),'error');return
  pasta=ROOT/'exports';pasta.mkdir(exist_ok=True)
  path=filedialog.asksaveasfilename(parent=self,title='Exportar cópia HTML para exports/',initialdir=str(pasta),defaultextension='.html',filetypes=[('HTML','*.html')])
  if not path:return
  try:
   p=Path(path).resolve()
   if not p.is_relative_to(pasta.resolve()):raise ValueError('Salve a cópia em exports/. Para atualizar o capítulo use Revisar e aplicar.')
   self.projeto_lit.salvar(p.relative_to(ROOT),sem_runtime(self.exportar_capitulo()),hash_arquivo(p));self.notify('Exportado',str(p),'success')
  except Exception as e:self.notify('Exportar',str(e),'error')
 def new_project(self):
  if not self.confirm_discard():return
  self.dirty=False;super().new_project();self.vinculo=None;self.rev_projeto=None;self.estado_entidades={};self._cadastro_personagens={}
 def open_project(self):
  if not self.confirm_discard():return
  path=filedialog.askopenfilename(parent=self,title='Abrir autoria semântica',filetypes=[('Projeto narrativo','*.narrproj'),('JSON','*.json')])
  if not path:return
  try:
   data=json.loads(Path(path).read_text(encoding='utf-8'))
   if not isinstance(data,dict) or not isinstance(data.get('text'),str):raise ValueError('O arquivo não é um projeto de autoria válido.')
   vinculo=copy.deepcopy(self.vinculo)
   if vinculo:
    info,_=self.projeto_lit.ler(vinculo['slug']+'/dados/info-obra.json')
    data=preparar_importacao(data,info,hashlib.sha256(Path(path).read_bytes()).hexdigest())
   self.abrir_autoria(data)
   # Abrir autoria externa não desconecta o capítulo ativo da sessão.
   if vinculo:
    self.vinculo=vinculo
    self.project_path=self.projeto_lit.root/vinculo['slug']/'autoria'/(vinculo['capitulo']+'.narrproj')
    self.rev_projeto=hash_arquivo(self.project_path);self.dirty=True
    tree,_=self.projeto_lit.ler(vinculo['slug']+'/dados/editorial.json');cap=next(c for _,c in self.projeto_lit.capitulos(tree) if c['id']==vinculo['capitulo'])
    self.recuperar_cenas_exatas(cap);self.sincronizar_recursos()
   else:
    self.project_path=Path(path);self.rev_projeto=hash_arquivo(self.project_path);self.vinculo=None;self._cadastro_personagens={};self.dirty=False
   self.refresh_project_identity();self.update_status()
  except Exception as e:self.notify('Abrir autoria',str(e),'error')
 def recuperar_cenas_exatas(self,cap):
  origem,_=importar_html(self.projeto_lit.caminho(self.vinculo['alvo']).read_text(encoding='utf-8'),cap,self.default_section_meta(scope='chapter'),self.schema)
  autoria=self.project_data();existentes={s['id'] for s in autoria.get('sections',[])};mudou=False
  for sec in origem['sections']:
   if sec['id'] in existentes:continue
   trecho=origem['text'][sec['start']:sec['end']]
   if trecho and autoria['text'].count(trecho)==1:
    nova=copy.deepcopy(sec);nova['start']=autoria['text'].index(trecho);nova['end']=nova['start']+len(trecho)
    autoria.setdefault('sections',[]).append(nova);mudou=True
  if mudou:self.abrir_autoria(autoria);self.dirty=True
 def conciliar_cenas(self,cap):
  dados=self.project_data();ids={s['id'] for s in dados.get('sections',[])}|{dados['section'].get('id')}
  faltam=[c for c in cap.get('cenas',[]) if c.get('visibilidade')=='publica' and c['ancora'] not in ids]
  if not faltam:return False
  painel=OverlayPanel(self,'Conciliar cenas do capítulo',subtitle='Selecione o trecho no editor, depois associe-o à cena. As avaliações do guia serão preservadas.',width=800,height=520)
  ttk.Label(painel.body,text='Há cenas sem seção correspondente na autoria. Feche este painel, selecione o texto de uma cena e reabra Revisar e aplicar.',wraplength=700).pack(pady=12)
  for cena in faltam:
   def associar(c=cena):
    try:
     inicio=self.index_to_offset(self.text.index('sel.first'));fim=self.index_to_offset(self.text.index('sel.last'))
     if inicio>=fim:raise ValueError('Selecione um trecho no editor.')
     dados=self.project_data();dados.setdefault('sections',[]).append({'id':c['ancora'],'start':inicio,'end':fim,'meta':{'id':c['ancora'],'data-scope':'scene'}})
     self.abrir_autoria(dados);self.dirty=True;painel.close()
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.body,text='Associar seleção a '+cena['titulo_cena'],command=associar).pack(fill='x',pady=5)
  return True
 def carregar_html_capitulo(self,cap):
  data,avisos=importar_html(self.projeto_lit.caminho(self.vinculo['alvo']).read_text(encoding='utf-8'),cap,self.default_section_meta(scope='chapter'),self.schema)
  self.abrir_autoria(data);self.relatorio_importacao=avisos;self.vinculo['base']=hash_arquivo(self.projeto_lit.caminho(self.vinculo['alvo']));self.dirty=True
 def importar_texto(self):
  if not self.vinculo:self.notify('Importar','Selecione um capítulo no Studio.','info');return
  if not self.ask_confirmation('Reabrir capítulo','Recarregar o HTML atual substitui a autoria em edição. As cenas e marcações suportadas serão preservadas; diferenças restantes aparecem na revisão antes de aplicar. Continuar?'):return
  tree,_=self.projeto_lit.ler(self.vinculo['slug']+'/dados/editorial.json');cap=next(c for _,c in self.projeto_lit.capitulos(tree) if c['id']==self.vinculo['capitulo'])
  self.carregar_html_capitulo(cap);self.sincronizar_recursos();self.update_status()
 def revisar(self):
  if not self.vinculo:self.notify('Aplicar','Abra o editor a partir de um capítulo no Literature Studio.','info');return
  problemas=self.validate_document()
  if problemas:self.notify('Revisar marcações','\n'.join(problemas),'error');return
  try:
   alvo=self.projeto_lit.caminho(self.vinculo['alvo'])
   revisao_html=hash_arquivo(alvo)
   alterado_externamente=revisao_html!=self.vinculo['base']
   tree,rev_tree=self.projeto_lit.ler(self.vinculo['slug']+'/dados/editorial.json');cap=next(c for _,c in self.projeto_lit.capitulos(tree) if c['id']==self.vinculo['capitulo'])
   if self.vinculo['alvo']!=f'{self.vinculo["slug"]}/{cap["arquivo"]}':raise ValueError('O arquivo do capítulo mudou. Reabra o vínculo pelo gerenciador.')
   self.recuperar_cenas_exatas(cap)
   if self.conciliar_cenas(cap):return
   novo=sem_runtime(self.exportar_capitulo());validar_ancoras(novo,cap.get('cenas',[]))
   info,rev_info=self.projeto_lit.ler(self.vinculo['slug']+'/dados/info-obra.json')
   validar_referencias(novo,{p['id'] for p in info.get('personagens',[])},{v['id'] for v in info.get('lore',[])},{p['id']:p.get('tipo_semantico','character') for p in info.get('personagens',[])})
   antes_tree=copy.deepcopy(tree)
   for sec in self.project_data().get('sections',[]):
    if sec.get('meta',{}).get('data-scope')!='scene':continue
    if any(c.get('ancora')==sec['id'] for c in cap.get('cenas',[])):continue
    cap.setdefault('cenas',[]).append({'id':'guia-'+uuid.uuid4().hex,'ancora':sec['id'],'titulo_cena':'Cena '+str(len(cap.get('cenas',[]))+1),'visibilidade':'publica','relevancia':'nao_avaliada','avaliacao_conteudo':'pendente','avisos_conteudo':[]})
   # A ordem segue as seções realmente exportadas; avaliações existentes são preservadas.
   cap['cenas']=sorted(cap.get('cenas',[]),key=lambda c:novo.find('id="'+c.get('ancora','')+'"') if c.get('visibilidade')=='publica' else len(novo))
   validar_ancoras(novo,cap.get('cenas',[]))
   if not self.text.get('1.0','end-1c').strip():raise ValueError('O texto de autoria está vazio.')
  except Exception as e:self.notify('Aplicação bloqueada',str(e),'error');return
  janela=OverlayPanel(self,'Revisar substituição do capítulo',width=950,height=650)
  ttk.Label(janela.body,text='Compare a alteração. Aplicar salva a autoria e substitui somente o HTML, com backup. Não publica o site.').pack(pady=12)
  texto=TextoRolavel(janela.body,wrap='none');texto.pack(fill='both',expand=True)
  texto.insert('1.0',('ATENÇÃO: o HTML mudou desde a abertura. Compare a autoria com a versão atual abaixo.\n\n' if alterado_externamente else '')+'\n'.join(getattr(self,'relatorio_importacao',[]))+'\n'+''.join(difflib.unified_diff(alvo.read_text(encoding='utf-8').splitlines(True),novo.splitlines(True),fromfile='Capítulo atual',tofile='Exportação semântica')))
  texto.insert('end','\n\nGUIA DE CENAS — proposta preservando avaliações:\n'+''.join(difflib.unified_diff(json.dumps(antes_tree,ensure_ascii=False,indent=2).splitlines(True),json.dumps(tree,ensure_ascii=False,indent=2).splitlines(True))));texto.configure(state='disabled')
  def aplicar():
   if self.save_project():
    try:
     path_tree=self.vinculo['slug']+'/dados/editorial.json'
     if hash_arquivo(self.projeto_lit.caminho(path_tree))!=rev_tree:raise ValueError('O guia foi alterado durante a revisão. Abra a revisão novamente.')
     if hash_arquivo(self.projeto_lit.caminho(self.vinculo['slug']+'/dados/info-obra.json'))!=rev_info:raise ValueError('Os recursos da obra mudaram durante a revisão. Abra a revisão novamente.')
     antigo_html=alvo.read_text(encoding='utf-8')
     nova_base=self.projeto_lit.salvar(self.vinculo['alvo'],novo,revisao_html)
     try:
      if tree!=antes_tree:self.projeto_lit.salvar(path_tree,tree,rev_tree)
     except Exception:
      self.vinculo['base']=self.projeto_lit.salvar(self.vinculo['alvo'],antigo_html,nova_base)
      raise
     self.vinculo['base']=nova_base;self.save_project();janela.destroy();
     if self.ao_aplicar:self.ao_aplicar(self.vinculo)
     self.notify('Aplicado','Capítulo e sessão atualizados com backup. Revise os metadados, valide e gere o site.','success')
    except Exception as e:self.notify('Aplicar',str(e),'error')
  ttk.Button(janela.footer,text='Aplicar esta versão ao capítulo',style='Accent.TButton',command=aplicar).pack(pady=12)

if __name__=='__main__':
 from gerenciador_visual import main
 main()

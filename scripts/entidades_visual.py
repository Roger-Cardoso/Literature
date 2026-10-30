"""Gestão de entidades que distingue o cadastro canônico da autoria local."""
import copy
from tkinter import ttk
from editor_componente import modulo,OverlayPanel
from identidade_semantica import ficha_entidade,ocorrencias
from rolagem import TextoRolavel

OriginalEntityManager=modulo.EntityManager
def instalar():
 def abrir(app):
  if getattr(app,'vinculo',None):return app.gerenciar_identidades()
  return OriginalEntityManager(app)
 modulo.EntityManager=abrir

class EntidadesMixin:
 def conciliar_entidades(self):
  self.sincronizar_recursos();conflitos=self.estado_entidades.get('conflitos',{})
  painel=OverlayPanel(self,'Identidades — cadastro e autoria',width=900,height=680,scrollable=True)
  if not conflitos:
   ttk.Label(painel.body,text='Não há conflitos de identidade. Personagens vinculados usam o cadastro da obra. Entidades locais podem ser vinculadas ou cadastradas explicitamente.',wraplength=750).pack(pady=12)
  for ident,conflito in conflitos.items():
   quadro=ttk.LabelFrame(painel.body,text=ident,padding=10);quadro.pack(fill='x',pady=6)
   ttk.Label(quadro,text='Cadastro: '+str(conflito['cadastro'])+'\nAutoria: '+str(conflito['autoria'])+'\nCampos divergentes: '+', '.join(conflito['campos']),wraplength=740).pack(anchor='w')
   def usar(i=ident):
    self.entities[i]={**self.entities[i],**conflitos[i]['cadastro']};self.estado_entidades.setdefault('bases',{})[i]=copy.deepcopy(conflitos[i]['cadastro']);self.estado_entidades['conflitos'].pop(i,None);self.dirty=True;self.update_status();painel.close()
   def propor(i=ident):
    painel.close();self.propor_personagem(i)
   ttk.Button(quadro,text='Usar dados do cadastro',command=usar).pack(side='left',padx=4)
   ttk.Button(quadro,text='Revisar proposta para o cadastro…',command=propor).pack(side='left',padx=4)
  ttk.Label(painel.body,text='Alterar nome ou tipo exige revisão. Homônimos e IDs importados sem origem confirmada não são associados automaticamente.',wraplength=740).pack(anchor='w',pady=12)
 def propor_personagem(self,ident):
  path=self.vinculo['slug']+'/dados/info-obra.json';info,rev=self.projeto_lit.ler(path);ent=self.entities[ident];p=next((p for p in info.get('personagens',[]) if p['id']==ident),None)
  novo=copy.deepcopy(info)
  if ent.get('type') not in {'character','creature'}:self.notify('Cadastro','Somente personagens/criaturas podem ser cadastrados nesta biblioteca.','error');return
  if p:
   alvo=next(x for x in novo['personagens'] if x['id']==ident);alvo.update(nome=ent['name'],tipo_semantico=ent['type'],aliases=list(ent.get('aliases',alvo.get('aliases',[]))))
  else:novo.setdefault('personagens',[]).append({'id':ident,'nome':ent['name'],'tipo_semantico':ent['type'],'aliases':list(ent.get('aliases',[])),'descricao_curta':'','imagem':'','imagem_alt':''})
  painel=OverlayPanel(self,'Revisar cadastro do personagem',width=850,height=580)
  import difflib,json
  ttk.Label(painel.body,text='Confira a proposta. Mudanças de tipo podem exigir revisão das marcações e reexportação dos capítulos que usam o personagem.',wraplength=720).pack(anchor='w',pady=8)
  texto=TextoRolavel(painel.body,wrap='word');texto.pack(fill='both',expand=True);texto.insert('1.0',''.join(difflib.unified_diff(json.dumps(info,ensure_ascii=False,indent=2).splitlines(True),json.dumps(novo,ensure_ascii=False,indent=2).splitlines(True))));texto.configure(state='disabled')
  def aplicar():
   try:
    self.projeto_lit.salvar(path,novo,rev);pessoa=next(x for x in novo['personagens'] if x['id']==ident);self.estado_entidades.setdefault('bases',{})[ident]=ficha_entidade(pessoa);self.estado_entidades.get('conflitos',{}).pop(ident,None);self.sincronizar_recursos();self.dirty=True;painel.close()
    if self.ao_aplicar:self.ao_aplicar(self.vinculo)
   except Exception as e:painel.set_error(str(e))
  ttk.Button(painel.footer,text='Aplicar proposta ao cadastro com backup',command=aplicar).pack(pady=8)
 def consultar_ocorrencias(self):
  painel=OverlayPanel(self,'Personagens e ocorrências na autoria atual',width=900,height=650)
  ttk.Label(painel.body,text='Ocorrências são marcações explícitas, não prova de presença física. Esta consulta usa a autoria em edição, que pode diferir do capítulo aplicado.',wraplength=740).pack(anchor='w',pady=10)
  lista=ttk.Treeview(painel.body,columns=('funcao','marca'),show='tree headings',height=12);lista.heading('#0',text='Personagem');lista.heading('funcao',text='Função');lista.heading('marca',text='Marcação/seção');lista.pack(fill='both',expand=True)
  itens={}
  for ident,p in self._cadastro_personagens.items():
   for ref in ocorrencias(self.project_data(),ident):
    iid=str(len(itens));itens[iid]=ref;lista.insert('','end',iid=iid,text=p['nome'],values=(ref['funcao'],ref['id']))
  def ir():
   sel=lista.selection()
   if not sel:return
   ref=itens[sel[0]]
   if ref['inicio'] is None:self.text.see('1.0')
   else:
    inicio=self.offset_to_index(ref['inicio']);fim=self.offset_to_index(ref['fim']);self.text.tag_remove('sel','1.0','end');self.text.tag_add('sel',inicio,fim);self.text.mark_set('insert',inicio);self.text.see(inicio)
   painel.close();self.text.focus_set()
  ttk.Button(painel.footer,text='Ir ao trecho selecionado',command=ir).pack(pady=8)
 def gerenciar_identidades(self):
  self.sincronizar_recursos();painel=OverlayPanel(self,'Entidades da obra e da autoria',width=900,height=650,scrollable=True)
  lista=ttk.Treeview(painel.body,columns=('tipo','estado','id'),show='tree headings',height=7)
  for coluna,texto in [('#0','Nome'),('tipo','Tipo'),('estado','Origem/estado'),('id','Identidade')]:lista.heading(coluna,text=texto)
  lista.pack(fill='both',expand=True)
  for ident,e in sorted(self.entities.items(),key=lambda p:p[1].get('name','')):
   estado='Conflito' if ident in self.estado_entidades.get('conflitos',{}) else 'Cadastro da obra' if ident in self._cadastro_personagens else 'Local à autoria'
   lista.insert('','end',iid=ident,text=e['name'],values=(e['type'],estado,ident))
  def executar(acao):
   sel=lista.selection()
   if not sel:return
   ident=sel[0];painel.close()
   if acao=='ficha' and ident in self._cadastro_personagens:self.winfo_toplevel().abrir_personagem(self.vinculo['slug'],ident)
   elif acao=='cadastrar':self.propor_personagem(ident)
   else:self.vincular_personagens()
  def editar_local():
   sel=lista.selection()
   if not sel:return
   ident=sel[0]
   if ident in self._cadastro_personagens:painel.set_error('Abra a ficha para editar um personagem do cadastro.');return
   entidade=dict(self.entities[ident]);painel.close();dlg=modulo.EntityDialog(self,self,entidade)
   if dlg.result:
    novo_id=self.change_entity_type(ident,dlg.result['type']) if dlg.result['type']!=entidade['type'] else ident
    self.entities[novo_id]['name']=dlg.result['name'];self.dirty=True;self.update_status()
    if novo_id!=ident:self.estado_entidades.setdefault('historico_local',[]).append({'operacao':'tipo','origem':ident,'destino':novo_id})
   self.gerenciar_identidades()
  def remover_local():
   sel=lista.selection()
   if not sel:return
   ident=sel[0]
   if ident in self._cadastro_personagens:painel.set_error('A exclusão de personagens é feita na biblioteca, com verificação de uso.');return
   painel.close();revisao=OverlayPanel(self,'Remover entidade local',width=740,height=470)
   ttk.Label(revisao.body,text='Remover '+self.entities[ident]['name']+f'? {len(ocorrencias(self.project_data(),ident))} referência(s) na autoria atual serão retiradas. O texto escrito será preservado. Esta ação não exclui personagens do cadastro.',wraplength=620).pack(pady=20)
   def aplicar():
    self.remove_entity_references(ident);self.entities.pop(ident,None);self.dirty=True;self.update_status();revisao.close()
   ttk.Button(revisao.footer,text='Remover entidade e referências locais',command=aplicar).pack(pady=10)
  ttk.Button(painel.body,text='Editar entidade local…',command=editar_local).pack(anchor='w',pady=4)
  ttk.Button(painel.body,text='Remover entidade local…',command=remover_local).pack(anchor='w',pady=4)
  def nova_local():
   painel.close();dlg=modulo.EntityDialog(self,self)
   if dlg.result:
    ident=self.next_entity_id(dlg.result['type']);self.entities[ident]={'id':ident,**dlg.result};self.dirty=True;self.update_status()
   self.gerenciar_identidades()
  def novo_personagem():
   painel.close();self.winfo_toplevel().novo_personagem(self.vinculo['slug'])
  ttk.Button(painel.body,text='Novo personagem no cadastro da obra…',command=novo_personagem).pack(anchor='w',pady=4)
  ttk.Button(painel.body,text='Nova entidade local à autoria…',command=nova_local).pack(anchor='w',pady=4)
  for texto,acao in [('Abrir ficha','ficha'),('Cadastrar/revisar proposta…','cadastrar'),('Vincular importada…','vincular')]:ttk.Button(painel.footer,text=texto,command=lambda a=acao:executar(a)).pack(side='left',padx=4)
  ttk.Button(painel.body,text='Ocorrências na autoria…',command=lambda:(painel.close(),self.consultar_ocorrencias())).pack(anchor='w',pady=4)
  ttk.Button(painel.body,text='Conciliar conflitos…',command=lambda:(painel.close(),self.conciliar_entidades())).pack(anchor='w',pady=8)

OriginalFieldEditor=modulo.FieldEditor
class CampoEntidadeIntegrado(OriginalFieldEditor):
 def __init__(self,parent,app,name,spec,initial=None):
  self.seletor=None
  if spec.get('kind')!='entity_ref' or not getattr(app,'vinculo',None):
   super().__init__(parent,app,name,spec,initial)
   if name in {'data-display-name','data-pov-display-name'}:
    rotulo='Nome apresentado neste trecho' if name=='data-display-name' else 'Nome apresentado no indicador de POV'
    self.frame.winfo_children()[0].configure(text=rotulo)
   return
  from seletor_personagens import SeletorPersonagens
  self.frame=ttk.Frame(parent);self.frame.pack(fill='x',padx=10,pady=5)
  nomes={'data-speaker':'Quem fala','data-thinker':'Quem pensa','data-addressee':'Destinatários','data-target':'Alvos','data-pov-character':'Ponto de vista'}
  ttk.Label(self.frame,text=nomes.get(name,name)+(' *' if spec.get('required') else '')).pack(anchor='w')
  tipos=set(spec.get('entity_types',[]));itens=[{'id':e['id'],'nome':e['name'],'aliases':list(e.get('aliases',[]))} for e in app.entities.values() if not tipos or e.get('type') in tipos]
  self.seletor=SeletorPersonagens(self.frame,itens,modulo.split_tokens(initial),multiplo=bool(spec.get('multiple')));self.seletor.lista.configure(height=3);self.seletor.pack(fill='x')
 def get(self):
  return ' '.join(self.seletor.ids()) if self.seletor is not None else super().get()

# Configura somente o componente em execução; os arquivos de origem ficam intactos.
modulo.FieldEditor=CampoEntidadeIntegrado

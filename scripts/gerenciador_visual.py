"""Literature Studio: interface local em Tkinter (Python padrão)."""
from rolagem import TextoRolavel, instalar
from arvore_editorial import ArvoreEditorial
from organizacao_visual import OrganizacaoMixin
from obras_visual import ObrasMixin
from site_visual import SiteMixin
from publicacao_visual import PublicacaoMixin
import hierarquia as hier
from seletor_personagens import SeletorPersonagens
from personagens_visual import PersonagensMixin,SeletorMarco
import copy
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
from pathlib import Path
import queue
import sys
from editor_semantico.editor_semantico import COLORS, SemanticEditor
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import uuid
import webbrowser
from gestao_projeto import Projeto, ROOT, hash_arquivo
from gerar_site import preparar, gerar
from estado_publicacao import assinatura_fontes, assinatura_gerada
from integracao_semantica import EditorLiterature
from editor_componente import OverlayPanel

ENUMS={'reacoes':['herdar','ativado','desativado'],'comentarios':['herdar','ativado','desativado'],'tipo_semantico':['character','creature'],'estado_publicacao':['rascunho','publicado','arquivado'],'estado_obra':['planejamento','em_andamento','pausada','concluida'],'relevancia':['nao_avaliada','essencial','complementar','opcional','alta','media','baixa'],'avaliacao_conteudo':['pendente','revisada'],'visibilidade':['publica','privada']}
NOMES={'reacoes':'Reações — herdar a configuração, ativar ou desativar','comentarios':'Comentários — herdar a configuração, ativar ou desativar','tipo_semantico':'Tipo semântico (character ou creature)','id':'Identidade permanente','id_obra':'Identidade permanente','titulo':'Título','titulo_cena':'Identificação pública da cena','estado_publicacao':'Publicação','estado_obra':'Andamento da obra','publicado_em':'Primeira publicação (AAAA-MM-DD)','atualizado_em':'Atualização (AAAA-MM-DD)','avisos_conteudo':'Avisos de conteúdo — um por linha','sinopse':'Sinopse','ancora':'Âncora no texto','relevancia':'Relevância narrativa','avaliacao_conteudo':'Avaliação de conteúdo','consequencia_pular':'Consequência de pular — spoiler','resumo_alternativo':'Resumo alternativo — spoiler','descricao':'Descrição — spoiler quando for cena','tratamento':'Como o conteúdo é apresentado','ordem':'Ordem no grupo — altere em Organizar capítulos','src':'Arquivo ou endereço da imagem','alt':'Descrição alternativa da imagem','disponivel_apos_capitulo':'Disponível após concluir (ID do capítulo)','verbetes_ids':'Verbetes associados — um ID por linha','personagens_ids':'Participações — selecione personagens cadastrados na obra'}
LISTAS={'tags','temas','generos','avisos_conteudo','aliases','verbetes_ids','personagens_ids'}
LONGOS={'sinopse','descricao','descricao_curta','texto','consequencia_pular','resumo_alternativo','tratamento'}
class Studio(PublicacaoMixin,SiteMixin,ObrasMixin,PersonagensMixin,OrganizacaoMixin,tk.Tk):
 def __init__(self):
  super().__init__();self.title('Literature Studio — gestão local');self.geometry('1180x800');self.minsize(850,600)
  self.projeto=Projeto();self.atual=None;self.widgets={};self.base=None;self.server=None;self.eventos=queue.Queue();self.ocupado=False;self.itens={};self.editor=None;self.editor_chave=None;self.overlay_stack=[]
  SemanticEditor.configure_styles(self)
  self.configure(bg=COLORS['app_bg'])
  style=ttk.Style(self);style.configure('Treeview',rowheight=30,background=COLORS['surface'],foreground=COLORS['text'],fieldbackground=COLORS['surface']);style.map('Treeview',background=[('selected','#E8E8FF')],foreground=[('selected',COLORS['primary'])])
  topo=ttk.Frame(self,padding=15);topo.pack(fill='x');ttk.Label(topo,text='Literature Studio',font=('Georgia',23)).pack(side='left')
  for texto,cmd in [('Validar',lambda:self.tarefa('Validar',lambda:preparar(ROOT))),('Gerar site',lambda:self.tarefa('Gerar',lambda:gerar(ROOT))),('Prévia',self.previa),('Pacote de publicação',self.pacote)]:ttk.Button(topo,text=texto,command=cmd).pack(side='left',padx=5)
  barra=ttk.Frame(self,padding=(15,0));barra.pack(fill='x')
  botoes=[]
  for texto,cmd in [('Publicar no GitHub',self.gerenciar_publicacao),('Site e comentários',self.configurar_site),('Obras',self.gerenciar_obras),('Nova obra',self.nova_obra),('Novo capítulo',self.novo_capitulo),('Organizar capítulos',self.organizar_estrutura),('Personagens',self.gerenciar_personagens),('Novo recurso',self.novo_recurso),('Editor semântico',self.editor_semantico),('Salvar',self.salvar_sessao),('Recarregar',self.recarregar),('Estrutura avançada',self.avancado),('Backups',self.backups)]:botoes.append(ttk.Button(barra,text=texto,command=cmd))
  def distribuir(event=None):
   colunas=max(1,min(len(botoes),(event.width if event else 1100)//150))
   for i,botao in enumerate(botoes):botao.grid(row=i//colunas,column=i%colunas,sticky='ew',padx=3,pady=3)
  barra.bind('<Configure>',distribuir);distribuir()
  corpo=ttk.Panedwindow(self,orient='horizontal');corpo.pack(fill='both',expand=True,padx=15,pady=12)
  self.corpo=corpo
  self.after_idle(lambda:corpo.sashpos(0,max(280,min(420,self.winfo_width()//3))))
  lateral=ttk.Frame(corpo);self.navegacao=ArvoreEditorial(lateral,self.projeto,self.inventario,lambda:self.deslocar(-1),lambda:self.deslocar(1),self.localizar_atual);self.navegacao.pack(fill='both',expand=True);self.tree=self.navegacao.tree;corpo.add(lateral,weight=1)
  self.abas=ttk.Notebook(corpo);corpo.add(self.abas,weight=4)
  direita=ttk.Frame(self.abas);self.aba_dados=direita;self.abas.add(direita,text='Gestão e metadados')
  self.aba_editor=ttk.Frame(self.abas);self.abas.add(self.aba_editor,text='Texto e semântica')
  ttk.Label(self.aba_editor,text='Selecione um capítulo e abra o editor semântico.',padding=25).pack()
  self.abas.bind('<<NotebookTabChanged>>',self.mudar_aba)
  self.cabecalho=ttk.Label(direita,text='Selecione uma obra ou capítulo',font=('Georgia',18));self.cabecalho.pack(anchor='w',pady=8)
  self.caminho_atual=tk.StringVar();ttk.Label(direita,textvariable=self.caminho_atual,wraplength=650).pack(anchor='w',pady=(0,8))
  self.canvas=tk.Canvas(direita,background=COLORS['surface'],highlightthickness=0);scroll=ttk.Scrollbar(direita,orient='vertical',command=self.canvas.yview);self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(fill='both',expand=True)
  self.form=ttk.Frame(self.canvas,padding=15);self.janela=self.canvas.create_window((0,0),window=self.form,anchor='nw')
  self.form.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')));self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.janela,width=e.width))
  self.validacao_assinatura=None;self.validacao_erro=None
  self.estado_texto=tk.StringVar(value='Conferindo estado das fontes…')
  estado_label=ttk.Label(self,textvariable=self.estado_texto,wraplength=1000,padding=(15,6));estado_label.pack(fill='x')
  estado_label.bind('<Configure>',lambda e:estado_label.configure(wraplength=max(200,e.width-30)))
  self.after(500,self.atualizar_estado)
  self.log=TextoRolavel(self,height=5,bg=COLORS['header'],fg='#D5D9F7',font=('DejaVu Sans Mono',10),state='disabled');self.log.pack(fill='x',padx=15,pady=(0,10))
  self.tree.bind('<<TreeviewSelect>>',self.selecionar);self.tree.bind('<ButtonRelease-1>',self.clicar_arvore);self.tree.bind('<Return>',self.ativar_arvore);self.protocol('WM_DELETE_WINDOW',self.sair);self.bind('<Control-s>',lambda e:self.salvar_sessao());self.after(100,self.receber);self.inventario();instalar(self)
  self.anotar('Edite fontes à esquerda. Validar e gerar não enviam arquivos ao GitHub. Backups em .literature-backups/.')
 def atualizar_estado(self):
  try:
   assinatura=assinatura_fontes(ROOT);gerada=assinatura_gerada(ROOT)
   autoria='não aberta';aplicacao='selecione um capítulo'
   if self.editor and self.editor.vinculo:
    from integracao_semantica import sem_runtime
    autoria='alterações não salvas' if self.editor.dirty else 'salva'
    alvo=self.projeto.caminho(self.editor.vinculo['alvo'])
    aplicacao='atualizado' if sem_runtime(self.editor.exportar_capitulo())==alvo.read_text(encoding='utf-8') else 'aguarda revisão e aplicação'
   site='atualizado' if gerada==assinatura else ('desatualizado — gere novamente' if gerada else 'ainda não gerado nesta versão')
   validacao='aprovada' if self.validacao_assinatura==assinatura or gerada==assinatura else ('pendências — consulte o registro' if self.validacao_erro==assinatura else 'aguarda validação das fontes atuais')
   self.estado_texto.set(f'Autoria: {autoria}  |  Capítulo: {aplicacao}  |  Site: {site}  |  Validação: {validacao}')
  except (OSError,ValueError,KeyError,tk.TclError) as e:self.estado_texto.set('Estado indisponível: '+str(e))
  self.after(2500,self.atualizar_estado)
 def _register_overlay(self,overlay):self.overlay_stack.append(overlay);overlay.lift()
 def _unregister_overlay(self,overlay):
  if overlay in self.overlay_stack:self.overlay_stack.remove(overlay)
 def anotar(self,texto):
  self.log.configure(state='normal');self.log.insert('end',texto+'\n');self.log.see('end');self.log.configure(state='disabled')
 def inventario(self,foco=None):
  self._programando_arvore=True;self.after_idle(lambda:setattr(self,'_programando_arvore',False))
  anterior=getattr(self,'_iid_atual',None) if self.atual else None
  try:self.navegacao.montar(foco or anterior)
  except (OSError,ValueError,KeyError,TypeError) as e:
   self.anotar('Não foi possível atualizar a árvore: '+str(e));messagebox.showerror('Verifique a estrutura editorial',str(e),parent=self);return
  self.itens=self.navegacao.itens
  if anterior in self.navegacao.referencias:self.atual=self.navegacao.referencias[anterior]
  if foco and foco in self.navegacao.referencias:
   self.navegacao.revelar(foco);self.carregar(self.navegacao.referencias[foco])
   if ':personagens:' in foco:self.abas.select(self.aba_dados)
 def valor(self):return {k:(w.get('1.0','end-1c') if isinstance(w,tk.Text) else w.get()) for k,w in self.widgets.items()}
 def continuar(self):
  if self.editor and self.editor.overlay_stack:
   self.anotar('Feche o painel do editor antes de mudar a sessão.');return False
  if self.ocupado:
   messagebox.showinfo('Aguarde','Aguarde a operação em andamento antes de editar.',parent=self);return False
  if self.atual and self.valor()!=self.base:
   resposta=messagebox.askyesnocancel('Alterações não salvas','Salvar as alterações antes de continuar?',parent=self)
   if resposta is None:return False
   if resposta and not self.salvar():return False
  return True
 def clicar_arvore(self,event):
  iid=self.tree.identify_row(event.y)
  if iid.endswith(':personagens') and self.tree.identify_region(event.x,event.y) in {'tree','cell'}:self.ativar_arvore()
 def ativar_arvore(self,event=None):
  sel=self.tree.selection()
  if sel and sel[0].endswith(':personagens'):
   if hasattr(self,'biblioteca_personagens') and self.abas.select()==str(self.biblioteca_personagens) and self.biblioteca_personagens.slug==self.itens[sel[0]][0]:return
   self.selecionar()
 def selecionar(self,event=None):
  if getattr(self,'_programando_arvore',False):return
  sel=self.tree.selection()
  if not sel or sel[0] not in self.itens:return
  descr=self.itens[sel[0]]
  if sel[0].endswith(':personagens'):
   if not self.continuar():
    anterior=getattr(self,'_iid_atual',None)
    if anterior and not self.tree.exists(anterior):anterior=self.navegacao.pais.get(anterior)
    if anterior and self.tree.exists(anterior):
     self._programando_arvore=True;self.after_idle(lambda:setattr(self,'_programando_arvore',False));self.tree.selection_set(anterior)
    return
   self.carregar(descr);self._iid_atual=sel[0];self.gerenciar_personagens(descr[0]);return
  if descr==self.atual:
   self._iid_atual=sel[0];self.caminho_atual.set(self.navegacao.caminhos.get(sel[0],''));return
  if not self.continuar():
   anterior=getattr(self,'_iid_atual',None)
   if anterior and self.tree.exists(anterior):self.tree.selection_set(anterior)
   return
  try:
   self.carregar(descr);self._iid_atual=sel[0];self.caminho_atual.set(self.navegacao.caminhos.get(sel[0],''));self.abas.select(self.aba_dados)
  except Exception as e:messagebox.showerror('Não foi possível abrir',str(e),parent=self)
 def carregar(self,descr):
  self._iid_atual=next((iid for iid,ref in self.navegacao.referencias.items() if ref==descr),None)
  self.caminho_atual.set(self.navegacao.caminhos.get(self._iid_atual,''))
  self.atual=descr;slug,path,chaves=descr;p=self.projeto.caminho(path);self.revisao=hash_arquivo(p)
  self.documento=json.loads(p.read_text()) if chaves is not None else None;self.obj=self.documento
  if chaves is not None:
   for k in chaves:self.obj=self.obj[k]
  for w in self.form.winfo_children():w.destroy()
  self.widgets={};self.tipos={};self.cabecalho.configure(text=path if chaves is None else self.obj.get('titulo_cena',self.obj.get('titulo',self.obj.get('nome','Metadados'))));self.canvas.yview_moveto(0)
  if chaves is None:self.campo('html',p.read_text(encoding='utf-8'),True)
  else:
   extras={}
   if 'arquivo'in self.obj:extras={'reacoes':'herdar','comentarios':'herdar','atualizado_em':None,'verbetes_ids':[],'personagens_ids':[]}
   if 'ancora'in self.obj:extras={'personagens_ids':[],'tratamento':'','consequencia_pular':'','resumo_alternativo':'','descricao':''}
   if 'categoria'in self.obj:extras={'disponivel_apos_capitulo':None}
   if chaves==():extras={'reacoes':'herdar','comentarios':'herdar'}
   if chaves and chaves[0]=='personagens':extras={'tipo_semantico':'character','nome':'','aliases':[],'descricao_curta':'','descricao':'','imagem':'','imagem_alt':'','disponivel_apos_capitulo':None}
   for key,value in {**extras,**self.obj}.items():
    if isinstance(value,dict) or isinstance(value,list) and key not in LISTAS:continue
    self.campo(key,value)
   if chaves and chaves[0]=='personagens':
    ttk.Button(self.form,text='Importar imagem do personagem…',command=self.imagem_personagem).pack(anchor='w',pady=8)
    ttk.Button(self.form,text='Ocorrências semânticas deste personagem…',command=self.consultar_ocorrencias_personagem).pack(anchor='w',pady=8)
    ttk.Button(self.form,text='Consultar participações deste personagem…',command=self.consultar_participacoes).pack(anchor='w',pady=8)
    ttk.Button(self.form,text='Voltar à biblioteca de personagens',command=self.gerenciar_personagens).pack(anchor='w',pady=8)
    ttk.Button(self.form,text='Excluir este personagem…',command=self.excluir_personagem).pack(anchor='w',pady=8)
   if chaves==():ttk.Button(self.form,text='Voltar à biblioteca de obras',command=self.gerenciar_obras).pack(anchor='w',pady=10)
   if chaves==('capa',):ttk.Button(self.form,text='Importar imagem local…',command=self.imagem).pack(anchor='w',pady=10)
  self.base=self.valor()
 def campo(self,key,value,longo=False):
  self.tipos[key]=type(value);rotulo=NOMES.get(key,key.replace('_',' ').capitalize())
  if self.atual[2] and self.atual[2][0]=='personagens':rotulo={'nome':'Nome do personagem','descricao_curta':'Apresentação curta','descricao':'Descrição do personagem','aliases':'Apelidos e nomes alternativos — um por linha','imagem':'Imagem do personagem','imagem_alt':'Descrição alternativa da imagem'}.get(key,rotulo)
  ttk.Label(self.form,text=rotulo).pack(anchor='w',pady=(12,4))
  texto='\n'.join(value) if key in LISTAS else '' if value is None else str(value)
  if key=='personagens_ids':
   info,_=self.projeto.ler(f'{self.atual[0]}/dados/info-obra.json');w=SeletorPersonagens(self.form,info.get('personagens',[]),value or []);w.pack(fill='x')
  elif key=='disponivel_apos_capitulo':
   arvore,_=self.projeto.ler(f'{self.atual[0]}/dados/editorial.json');w=SeletorMarco(self.form,arvore,value);w.pack(fill='x')
  elif longo or key in LONGOS or key in LISTAS:
   w=TextoRolavel(self.form,height=22 if longo else 5,wrap='none' if longo else 'word',undo=True,bg=COLORS['editor'],fg=COLORS['text'],insertbackground=COLORS['primary'],font=('DejaVu Sans Mono',11) if longo else ('Segoe UI',11));w.insert('1.0',texto);w.pack(fill='both',expand=longo)
  elif key in ENUMS:
   w=ttk.Combobox(self.form,values=ENUMS[key],state='readonly');w.set(texto);w.pack(fill='x')
  else:
   w=ttk.Entry(self.form);w.insert(0,texto);w.pack(fill='x')
   if key in ('id','id_obra','slug','schema_version','id_legado','arquivo','ordem'):w.configure(state='readonly')
  self.widgets[key]=w
 def salvar(self):
  if self.ocupado:return False
  if not self.atual:return True
  try:
   if self.atual[2] is None:conteudo=self.widgets['html'].get('1.0','end-1c')
   else:
    novo=copy.deepcopy(self.obj)
    for k,v in self.valor().items():
     if k in LISTAS:novo[k]=[x.strip() for x in v.splitlines() if x.strip()]
     elif self.tipos[k] is int:novo[k]=int(v)
     elif not v and (self.tipos[k] is type(None) or k.endswith('_em') or k=='disponivel_apos_capitulo'):novo[k]=None
     else:novo[k]=v
    if self.atual[1].endswith('/dados/info-obra.json') and self.atual[2]==():self.projeto.validar_ficha_obra(novo)
    self.obj.clear();self.obj.update(novo);conteudo=self.documento
   if self.atual[1].endswith('/editorial.json'):hier.validar(conteudo)
   self.revisao=self.projeto.salvar(self.atual[1],conteudo,self.revisao);self.base=self.valor();self.anotar('Salvo com backup: '+self.atual[1]);self.inventario();return True
  except Exception as e:messagebox.showerror('Não foi possível salvar',str(e),parent=self);return False
 def recarregar(self):
  if not self.continuar():return
  iid=getattr(self,'_iid_atual',None);self.inventario()
  if iid in self.navegacao.referencias:self.carregar(self.navegacao.referencias[iid]);self.navegacao.revelar(iid)
  else:
   self.atual=None;self._iid_atual=None;self.widgets={};self.base=None
   for w in self.form.winfo_children():w.destroy()
   self.cabecalho.configure(text='Selecione uma obra ou capítulo');self.caminho_atual.set('O item anterior não está mais na estrutura.')
 def contexto(self):
  if not self.atual:raise ValueError('Selecione uma obra ou um capítulo na árvore.')
  return self.atual[0]
 def novo_recurso(self):
  if not self.continuar():return
  try:
   slug=self.contexto();tipo=simpledialog.askstring('Novo recurso','Digite: personagem, verbete, cena ou nota. Para cena/nota selecione primeiro o capítulo.',parent=self)
   if not tipo:return
   if tipo=='personagem':self.novo_personagem();return
   ident=tipo+'-'+uuid.uuid4().hex
   if tipo in ('personagem','verbete'):
    path=f'{slug}/dados/info-obra.json';doc,rev=self.projeto.ler(path);campo='personagens' if tipo=='personagem' else 'lore'
    item={'id':ident,'nome':'Novo personagem','descricao_curta':'','imagem':'','imagem_alt':'','aliases':[]} if tipo=='personagem' else {'id':ident,'titulo':'Novo verbete','descricao':'','categoria':'universo'}
    doc.setdefault(campo,[]).append(item)
   elif tipo in ('cena','nota'):
    if not self.obj or 'arquivo'not in self.obj:raise ValueError('Selecione o capítulo, não o texto ou uma cena.')
    path=self.atual[1];doc,rev=self.projeto.ler(path);cap=doc
    for k in self.atual[2]:cap=cap[k]
    if tipo=='nota':cap.setdefault('notas',[]).append({'id':ident,'titulo':'Nova nota','texto':''})
    else:
     ancora=simpledialog.askstring('Âncora da cena','ID existente no HTML do capítulo (ex.: cena-chegada):',parent=self)
     if not ancora:return
     cap.setdefault('cenas',[]).append({'id':ident,'ancora':ancora,'titulo_cena':'Nova cena','visibilidade':'publica','relevancia':'nao_avaliada','avaliacao_conteudo':'pendente','avisos_conteudo':[]})
   else:raise ValueError('Tipo não reconhecido.')
   self.projeto.salvar(path,doc,rev);self.atual=None;self.inventario();self.anotar('Recurso criado. Preencha os campos antes de gerar.')
  except Exception as e:messagebox.showerror('Novo recurso',str(e),parent=self)
 def mudar_aba(self,event=None):
  if getattr(self,'_ativando_editor',False):return
  if self.editor and self.editor.overlay_stack and self.abas.select()!=str(self.aba_editor):
   self.abas.select(self.aba_editor);return
  if hasattr(self,'biblioteca_obras') and self.abas.select()==str(self.biblioteca_obras):
   if not self.continuar():self.abas.select(self.aba_dados);return
   try:self.biblioteca_obras.atualizar()
   except Exception as e:self.anotar('Biblioteca de obras: '+str(e))
  if hasattr(self,'biblioteca_personagens') and self.abas.select()==str(self.biblioteca_personagens):
   if not self.continuar():self.abas.select(self.aba_dados);return
   slug=self.biblioteca_personagens.slug
   if slug and (not self.atual or self.atual[0]!=slug):self.carregar(self.navegacao.referencias['obra:'+slug+':personagens']);self._iid_atual='obra:'+slug+':personagens'
   self.biblioteca_personagens.atualizar()
  if self.abas.select()==str(self.aba_editor):
   if self.atual and self.valor()!=self.base and not self.continuar():
    self.abas.select(self.aba_dados);return
   try:
    slug,cap=self.capitulo_ativo()
    if cap and self.editor_chave!=(slug,cap['id']):
     self.editor_semantico();return
   except ValueError:pass
   if self.editor:self.configure(menu=self.editor.menu_documento);self.editor.sincronizar_recursos()
   else:self.configure(menu='')
  else:self.configure(menu='')
 def exibir_editor(self,editor):
  if editor is not self.editor:return
  self._ativando_editor=True
  try:self.abas.select(self.aba_editor);self.configure(menu=editor.menu_documento);self.update_idletasks()
  finally:self._ativando_editor=False
 def salvar_sessao(self):
  if self.editor and self.editor.overlay_stack:return False
  if self.editor and self.abas.select()==str(self.aba_editor):return self.editor.save_project()
  return self.salvar()
 def salvar_autoria(self):
  if self.editor and self.editor.dirty:
   resposta=messagebox.askyesnocancel('Autoria em edição','Salvar a autoria semântica antes de continuar?',parent=self)
   if resposta is None:return False
   if resposta and not self.editor.save_project():return False
   if not resposta:self.editor.dirty=False
  return True
 def capitulo_ativo(self):
  slug=self.contexto();tree,_=self.projeto.ler(f'{slug}/dados/editorial.json')
  return slug,next((c for _,c in self.projeto.capitulos(tree) if (self.obj and c['id']==self.obj.get('id')) or self.atual[1]==f'{slug}/{c["arquivo"]}' or (self.obj and any(x.get('id')==self.obj.get('id') for x in c.get('cenas',[])+c.get('notas',[])))),None)
 def editor_semantico(self):
  if not self.continuar():return
  try:
   slug,cap=self.capitulo_ativo()
   if not cap:raise ValueError('Selecione um capítulo, seu texto ou uma cena para abrir a edição.')
   chave=(slug,cap['id'])
   if self.editor_chave!=chave:
    if not self.salvar_autoria():return
    if self.editor:self.editor.destroy()
    for w in self.aba_editor.winfo_children():w.destroy()
    self.editor=EditorLiterature(self.aba_editor,slug,cap['id'],ao_aplicar=self.capitulo_aplicado);self.editor.pack(fill='both',expand=True);self.editor_chave=chave
   self.abas.select(self.aba_editor);self.mudar_aba();self.editor.text.focus_set()
  except Exception as e:messagebox.showerror('Editor semântico',str(e),parent=self)
 def capitulo_aplicado(self,vinculo):
  self.inventario()
  if self.atual:self.carregar(self.atual)
  self.anotar('Capítulo ou recursos atualizados na sessão: '+vinculo['alvo']+'. Valide e gere a publicação.')
 def imagem(self):
  origem=filedialog.askopenfilename(title='Selecionar imagem',filetypes=[('Imagens','*.png *.jpg *.jpeg *.webp *.gif *.svg')])
  if origem:
   try:
    path=self.projeto.importar_imagem(origem);w=self.widgets['src'];w.delete(0,'end');w.insert(0,path);self.anotar('Imagem importada. Salve a capa para associá-la.')
   except Exception as e:messagebox.showerror('Importar imagem',str(e),parent=self)
 def avancado(self):
  if not self.continuar():return
  try:
   slug=self.contexto();path=f'{slug}/dados/editorial.json';doc,rev=self.projeto.ler(path)
   win=OverlayPanel(self,'Estrutura avançada — '+slug,width=850,height=650);ttk.Label(win.body,text='Edite agrupamentos e ordem. A validação completa ocorre em Validar.').pack()
   texto=TextoRolavel(win.body,undo=True);texto.insert('1.0',json.dumps(doc,ensure_ascii=False,indent=2));texto.pack(fill='both',expand=True)
   def gravar():
    try:self.projeto.organizar(slug,json.loads(texto.get('1.0','end-1c')),rev);win.destroy();self.atual=None;self.inventario()
    except Exception as e:messagebox.showerror('Estrutura',str(e),parent=win)
   ttk.Button(win.footer,text='Salvar estrutura com backup',command=gravar).pack()
  except Exception as e:messagebox.showerror('Estrutura',str(e),parent=self)
 def backups(self):
  if not self.continuar():return
  base=ROOT/'.literature-backups';arquivos=sorted([p for p in base.rglob('*') if p.is_file()],reverse=True) if base.exists() else []
  win=OverlayPanel(self,'Cópias de segurança',width=900,height=650)
  ttk.Label(win.body,text='Selecione uma cópia para conferir. Restaurar preserva o arquivo atual em um novo backup.').pack(pady=10)
  lista=tk.Listbox(win.body,height=10);lista.pack(fill='x',padx=10)
  for p in arquivos:lista.insert('end',str(p.relative_to(base)))
  preview=TextoRolavel(win.body,wrap='word');preview.pack(fill='both',expand=True,padx=10,pady=10)
  def exibir(event=None):
   sel=lista.curselection()
   if sel:preview.delete('1.0','end');preview.insert('1.0',arquivos[sel[0]].read_text(encoding='utf-8'))
  lista.bind('<<ListboxSelect>>',exibir)
  def restaurar():
   sel=lista.curselection()
   if not sel:return
   p=arquivos[sel[0]];rel=Path(*p.relative_to(base).parts[1:])
   if not messagebox.askyesno('Restaurar cópia','Restaurar '+str(rel)+' a partir desta cópia?',parent=win):return
   try:
    destino=self.projeto.caminho(rel);self.projeto.salvar(rel,p.read_text(encoding='utf-8'),hash_arquivo(destino));self.atual=None;self.inventario();self.anotar('Backup restaurado: '+str(rel));win.destroy()
   except Exception as e:messagebox.showerror('Restaurar',str(e),parent=win)
  ttk.Button(win.footer,text='Restaurar cópia selecionada',command=restaurar).pack(pady=10)
 def tarefa(self,nome,func):
  if self.ocupado:return
  if not self.continuar() or not self.salvar_autoria():return
  if nome.startswith('Gerar') and self.editor and self.editor.vinculo and self.editor.text.get('1.0','end-1c').strip():
   from integracao_semantica import sem_runtime
   html=self.projeto.caminho(self.editor.vinculo['alvo']).read_text(encoding='utf-8')
   if sem_runtime(self.editor.build_html())!=html:
    self.exibir_editor(self.editor);self.anotar('Revise e aplique a autoria ao capítulo antes de gerar. A operação de publicação aguardará essa revisão.');self.editor.revisar();return
  self.tarefa_nome=nome;self.assinatura_em_execucao=assinatura_fontes(ROOT)
  self.ocupado=True;self.anotar(nome+' em andamento…')
  def worker():
   try:resultado=func();self.eventos.put((True,nome+' concluído.',resultado))
   except Exception as e:self.eventos.put((False,str(e),None))
  threading.Thread(target=worker,daemon=True).start()
 def receber(self):
  try:
   while True:
    ok,texto,_=self.eventos.get_nowait();self.ocupado=False;self.anotar(texto)
    if getattr(self,'tarefa_nome','').startswith(('Validar','Gerar')):
     if ok:self.validacao_assinatura=self.assinatura_em_execucao;self.validacao_erro=None
     else:self.validacao_assinatura=None;self.validacao_erro=self.assinatura_em_execucao
    if not ok:messagebox.showerror('Verifique o projeto',texto,parent=self)
  except queue.Empty:pass
  self.after(100,self.receber)
 def previa(self):
  if not (ROOT/'site/index.html').exists():messagebox.showinfo('Prévia','Gere o site antes de abrir a prévia.',parent=self);return
  from previa_interna import Previa
  if not hasattr(self,'aba_previa') or not self.aba_previa.winfo_exists():
   self.aba_previa=Previa(self.abas,ROOT,self.previa_navegador);self.abas.add(self.aba_previa,text='Prévia da publicação')
  else:self.aba_previa.atualizar()
  self.abas.select(self.aba_previa)
 def previa_navegador(self):
  if not (ROOT/'site/index.html').exists():messagebox.showinfo('Prévia','Gere o site antes de abrir a prévia.',parent=self);return
  try:
   if not self.server:
    handler=partial(SimpleHTTPRequestHandler,directory=str(ROOT/'site'));self.server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=self.server.serve_forever,daemon=True).start()
   url=f'http://127.0.0.1:{self.server.server_port}/home/';webbrowser.open(url);self.anotar('Prévia da última geração: '+url)
  except Exception as e:messagebox.showerror('Prévia',str(e),parent=self)
 def pacote(self):
  if not self.continuar():return
  destino=filedialog.asksaveasfilename(title='Salvar pacote público',defaultextension='.zip',initialfile='literature-publicacao.zip',filetypes=[('ZIP','*.zip')])
  if destino:self.tarefa('Gerar e empacotar publicação',lambda:(gerar(ROOT),self.projeto.exportar(destino)))
 def sair(self):
  if self.overlay_stack:self.overlay_stack[-1].close();return
  if self.editor and self.editor.overlay_stack:self.editor.close_active_overlay();return
  if not self.salvar_autoria():return
  if self.ocupado:messagebox.showinfo('Aguarde','Aguarde a operação em andamento.',parent=self);return
  if not self.continuar():return
  if hasattr(self,'pagina_publicacao'):
   self.pagina_publicacao.cancelar_auth()
   if self.pagina_publicacao.pacote:self.pagina_publicacao.pacote.fechar()
  if self.server:threading.Thread(target=self.server.shutdown,daemon=True).start()
  self.destroy()

def main():
 try:Studio().mainloop()
 except tk.TclError as e:raise SystemExit('Não foi possível abrir a interface gráfica. Execute em uma sessão de desktop com Tkinter disponível.\n'+str(e))
if __name__=='__main__':main()

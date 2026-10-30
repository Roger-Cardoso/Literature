"""Cadastro e consulta de participações na mesma janela do Studio."""
import tkinter as tk
from tkinter import ttk,messagebox
import uuid
from editor_componente import OverlayPanel
from personagens import indice_participacoes,validar_participacoes,validar_catalogo,personagem_referenciado_na_autoria
from biblioteca_personagens import BibliotecaPersonagens
from hierarquia import normalizar,nos
from rolagem import TextoRolavel

class SeletorMarco(ttk.Combobox):
 def __init__(self,parent,arvore,atual):
  self.opcoes={'Disponível desde o início':''}
  for n in nos(arvore):
   if n.tipo=='capitulo':self.opcoes[n.endereco+' · '+' / '.join(n.nomes)+' — '+n.id]=n.id
  if atual and atual not in self.opcoes.values():self.opcoes['Capítulo ausente — '+atual]=atual
  super().__init__(parent,state='readonly',values=list(self.opcoes))
  self.set(next(label for label,ident in self.opcoes.items() if ident==(atual or '')))
 def get(self):return self.opcoes.get(super().get(),'')

class PersonagensMixin:
 def novo_personagem(self,slug=None):
  if not self.continuar():return
  try:
   slug=slug or self.contexto();info,rev=self.projeto.ler(f'{slug}/dados/info-obra.json')
   painel=OverlayPanel(self,'Novo personagem',width=700,height=510)
   ttk.Label(painel.body,text='Nome do personagem').pack(anchor='w',pady=5);nome=ttk.Entry(painel.body);nome.pack(fill='x');nome.focus_set()
   ttk.Label(painel.body,text='Apelidos — um por linha').pack(anchor='w',pady=5);aliases=TextoRolavel(painel.body,height=3);aliases.pack(fill='x')
   ttk.Label(painel.body,text='Descrição curta').pack(anchor='w',pady=5);descricao=TextoRolavel(painel.body,height=3,wrap='word');descricao.pack(fill='x')
   ttk.Label(painel.body,text='O personagem receberá uma identidade permanente. Homônimos permanecem cadastros distintos.',wraplength=600).pack(anchor='w',pady=12)
   def criar():
    try:
     ident='personagem-'+uuid.uuid4().hex
     info.setdefault('personagens',[]).append({'id':ident,'nome':nome.get().strip(),'aliases':[x.strip() for x in aliases.get('1.0','end-1c').splitlines() if x.strip()],'descricao_curta':descricao.get('1.0','end-1c'),'descricao':'','imagem':'','imagem_alt':'','disponivel_apos_capitulo':None})
     try:self.projeto.salvar(f'{slug}/dados/info-obra.json',info,rev)
     except Exception:info['personagens'].pop();raise
     painel.close();self.inventario(foco='obra:'+slug+':personagens:'+ident)
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Criar personagem e abrir ficha',command=criar).pack(pady=8)
  except Exception as e:messagebox.showerror('Personagens',str(e),parent=self)
 def imagem_personagem(self):
  from tkinter import filedialog
  origem=filedialog.askopenfilename(parent=self,title='Imagem do personagem',filetypes=[('Imagens','*.png *.jpg *.jpeg *.webp *.gif *.svg')])
  if not origem:return
  try:
   caminho=self.projeto.importar_imagem(origem);campo=self.widgets['imagem'];campo.delete(0,'end');campo.insert(0,caminho)
   self.anotar('Imagem importada. Salve a ficha para associá-la ao personagem.')
  except Exception as e:messagebox.showerror('Imagem do personagem',str(e),parent=self)
 def abrir_personagem(self,slug,ident):
  if not self.continuar():return
  try:
   info,_=self.projeto.ler(f'{slug}/dados/info-obra.json')
   if ident not in validar_catalogo(info):raise ValueError('O personagem não está mais no cadastro. Atualize a biblioteca.')
   iid='obra:'+slug+':personagens:'+ident;self.inventario(foco=iid)
   if iid not in self.navegacao.referencias or self.obj.get('id')!=ident:raise ValueError('O cadastro mudou durante a abertura. Atualize a biblioteca.')
   self.abas.select(self.aba_dados)
  except Exception as e:
   if hasattr(self,'biblioteca_personagens'):self.biblioteca_personagens.atualizar(slug);self.abas.select(self.biblioteca_personagens)
   messagebox.showerror('Abrir personagem',str(e),parent=self)
 def gerenciar_personagens(self,slug=None):
  if not self.continuar():return
  try:
   slug=slug or self.contexto()
   if not hasattr(self,'biblioteca_personagens') or not self.biblioteca_personagens.winfo_exists():
    self.biblioteca_personagens=BibliotecaPersonagens(self.abas,self.projeto,self.abrir_personagem,lambda:self.novo_personagem(self.biblioteca_personagens.slug),self.excluir_personagem)
    self.abas.add(self.biblioteca_personagens,text='Biblioteca de personagens')
   self.biblioteca_personagens.atualizar(slug)
   if not self.atual or self.atual[0]!=slug:self.carregar(self.navegacao.referencias['obra:'+slug+':personagens']);self._iid_atual='obra:'+slug+':personagens'
   self.abas.select(self.biblioteca_personagens);self.configure(menu='')
  except Exception as e:messagebox.showerror('Biblioteca de personagens',str(e),parent=self)
 def excluir_personagem(self,slug=None,ident=None):
  if not self.continuar():return
  try:
   slug=slug or self.contexto();ident=ident or self.obj.get('id');info,rev=self.projeto.ler(f'{slug}/dados/info-obra.json');personagem=next(p for p in info.get('personagens',[]) if p['id']==ident)
   usos=self.projeto.usos_personagem(slug,ident)
   if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug and personagem_referenciado_na_autoria(self.editor.project_data(),ident):usos.append('Marcações na autoria atualmente aberta')
   painel=OverlayPanel(self,'Excluir personagem — '+personagem['nome'],width=760,height=540)
   ttk.Label(painel.body,text=personagem['nome']+' — '+ident,wraplength=650).pack(anchor='w',pady=12)
   if usos:
    ttk.Label(painel.body,text='Este personagem está em uso. Remova ou substitua seus vínculos antes de excluir.',wraplength=650).pack(anchor='w')
    texto=TextoRolavel(painel.body,height=10,wrap='word');texto.pack(fill='both',expand=True,pady=10);texto.insert('1.0','\n'.join(dict.fromkeys(usos)));texto.configure(state='disabled');return
   ttk.Label(painel.body,text='O personagem não tem participações ou marcações detectadas nos capítulos e autorias desta obra. A exclusão remove sua ficha do cadastro e cria um backup. Os arquivos de imagem e os textos são preservados.',wraplength=650).pack(anchor='w',pady=10)
   def excluir():
    try:
     if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug and personagem_referenciado_na_autoria(self.editor.project_data(),ident):raise ValueError('O personagem passou a ser usado na autoria aberta. Reabra esta revisão.')
     self.projeto.excluir_personagem(slug,ident,rev)
     if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug:
      if ident in self.editor.entities:self.editor.entities.pop(ident);self.editor.dirty=True;self.editor.update_status()
     painel.close();self.atual=None;self.inventario();grupo='obra:'+slug+':personagens'
     self.carregar(self.navegacao.referencias[grupo]);self._iid_atual=grupo;self.gerenciar_personagens(slug)
     self.anotar('Personagem excluído com backup: '+personagem['nome'])
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Excluir personagem com backup',command=excluir).pack(pady=10)
  except Exception as e:messagebox.showerror('Excluir personagem',str(e),parent=self)
 def consultar_ocorrencias_personagem(self):
  if not self.continuar():return
  try:
   from identidade_semantica import ocorrencias
   slug=self.contexto();ident=self.obj['id'];registros=self.projeto.ocorrencias_personagem(slug,ident)
   if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug:
    registros.extend({**r,'capitulo':self.editor.vinculo['capitulo'],'titulo':'Capítulo da sessão aberta','origem':'Autoria aberta — estado atual'} for r in ocorrencias(self.editor.project_data(),ident))
   painel=OverlayPanel(self,'Ocorrências semânticas — '+self.obj['nome'],width=1000,height=660)
   ttk.Label(painel.body,text='Marcações explícitas por função. Capítulo aplicado, autoria salva e sessão aberta são versões separadas; podem conter a mesma marcação. Participação declarada continua independente.',wraplength=850).pack(anchor='w',pady=10)
   quadro=ttk.Frame(painel.body);quadro.pack(fill='both',expand=True)
   lista=ttk.Treeview(quadro,columns=('origem','funcao','marca'),show='tree headings',selectmode='browse')
   for chave,nome in [('#0','Capítulo'),('origem','Versão consultada'),('funcao','Função'),('marca','Marcação/seção')]:lista.heading(chave,text=nome)
   y=ttk.Scrollbar(quadro,orient='vertical',command=lista.yview);x=ttk.Scrollbar(quadro,orient='horizontal',command=lista.xview);lista.configure(yscrollcommand=y.set,xscrollcommand=x.set);y.pack(side='right',fill='y');x.pack(side='bottom',fill='x');lista.pack(fill='both',expand=True)
   for i,r in enumerate(registros):lista.insert('','end',iid=str(i),text=r['titulo'],values=(r['origem'],r['funcao'],r['id']))
   ttk.Label(painel.body,text=f'{len(registros)} ocorrência(s) nas versões consultadas. A ausência de marcações não elimina uma participação declarada.',wraplength=850).pack(anchor='w',pady=8)
   def abrir():
    sel=lista.selection()
    if not sel:return
    ref=registros[int(sel[0])]
    if not ref['capitulo']:painel.set_error('Esta autoria não possui um capítulo atual associado.');return
    painel.close();self.inventario(foco='editorial:'+slug+':'+ref['capitulo']);self.abas.select(self.aba_dados)
   ttk.Button(painel.footer,text='Abrir capítulo selecionado',command=abrir).pack(pady=8)
  except Exception as e:messagebox.showerror('Ocorrências semânticas',str(e),parent=self)
 def consultar_participacoes(self):
  if not self.continuar():return
  try:
   slug=self.contexto();ident=self.obj['id'];info,_=self.projeto.ler(f'{slug}/dados/info-obra.json');arvore,_=self.projeto.ler(f'{slug}/dados/editorial.json');validar_participacoes(info,arvore)
   personagem=next(p for p in info.get('personagens',[]) if p['id']==ident);registros=indice_participacoes(arvore).get(ident,[])
   painel=OverlayPanel(self,'Participações — '+personagem['nome'],width=950,height=620)
   ttk.Label(painel.body,text=personagem['nome']+' — '+ident+'\nParticipações editoriais locais, incluindo rascunhos e cenas privadas.',wraplength=800).pack(anchor='w',pady=10)
   quadro=ttk.Frame(painel.body);quadro.pack(fill='both',expand=True)
   lista=ttk.Treeview(quadro,columns=('tipo','publicacao'),show='tree headings',selectmode='browse');lista.heading('#0',text='Posição e caminho');lista.heading('tipo',text='Vínculo');lista.heading('publicacao',text='Publicação')
   y=ttk.Scrollbar(quadro,orient='vertical',command=lista.yview);x=ttk.Scrollbar(quadro,orient='horizontal',command=lista.xview);lista.configure(yscrollcommand=y.set,xscrollcommand=x.set);y.pack(side='right',fill='y');x.pack(side='bottom',fill='x');lista.pack(fill='both',expand=True)
   for i,ref in enumerate(registros):lista.insert('','end',iid=str(i),text=ref['caminho'],values=('Cena' if ref['cena'] else 'Capítulo',ref['estado']))
   if not registros:ttk.Label(painel.body,text='Nenhuma participação editorial associada.').pack(anchor='w',pady=8)
   def abrir():
    sel=lista.selection()
    if not sel:painel.set_error('Selecione uma participação.');return
    ref=registros[int(sel[0])];iid='editorial:'+slug+':'+ref['capitulo']
    if ref['cena']:iid+=':cenas:'+ref['cena']
    painel.close();self.inventario(foco=iid);self.abas.select(self.aba_dados)
   ttk.Button(painel.footer,text='Abrir capítulo ou cena selecionado',command=abrir).pack(pady=8);lista.bind('<Double-1>',lambda e:abrir());self._participacoes_personagem_ui=lista
  except Exception as e:messagebox.showerror('Participações',str(e),parent=self)

"""Fluxos de gestão de obras integrados ao Studio."""
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from editor_componente import OverlayPanel
from biblioteca_obras import BibliotecaObras

class ObrasMixin:
 def _continuar_obras(self):
  if not self.continuar():return False
  # A resposta "não salvar" descarta de fato o formulário antes da operação.
  if self.atual and self.valor()!=self.base:self.carregar(self.atual)
  return True
 def gerenciar_obras(self):
  if not self._continuar_obras():return
  try:
   if not hasattr(self,'biblioteca_obras'):
    self.biblioteca_obras=BibliotecaObras(self.abas,self.projeto,{'nova':self.nova_obra,'abrir':self.abrir_obra,'estado':self.estado_obra,'exportar':self.exportar_fontes_obra,'excluir':self.excluir_obra,'restaurar':self.restaurar_obra})
    self.abas.add(self.biblioteca_obras,text='Biblioteca de obras')
   self.biblioteca_obras.atualizar();self.abas.select(self.biblioteca_obras);self.configure(menu='')
  except Exception as e:messagebox.showerror('Obras',str(e),parent=self)
 def abrir_obra(self,slug):
  if not self._continuar_obras():return
  try:
   self.projeto._pasta_obra(slug)
   self.inventario(foco='obra:'+slug)
   if not self.atual or self.atual!=(slug,f'{slug}/dados/info-obra.json',()):raise ValueError('A obra não está disponível. Atualize a biblioteca.')
   self.abas.select(self.aba_dados)
  except Exception as e:messagebox.showerror('Abrir obra',str(e),parent=self)
 def nova_obra(self):
  if not self._continuar_obras():return
  painel=OverlayPanel(self,'Nova obra',width=720,height=530,scrollable=True);campos={}
  for chave,texto in [('titulo','Título'),('autor','Autor'),('slug','Endereço da obra — letras minúsculas, números e hífens')]:
   ttk.Label(painel.body,text=texto).pack(anchor='w',pady=(12,4));w=ttk.Entry(painel.body);w.pack(fill='x');campos[chave]=w
  ttk.Label(painel.body,text='A obra será criada como rascunho, com identidade própria e estrutura vazia. O endereço é permanente; o título poderá mudar.',wraplength=600).pack(anchor='w',pady=15)
  campos['titulo'].focus_set()
  def criar():
   try:
    slug=self.projeto.nova_obra(campos['slug'].get().strip(),campos['titulo'].get(),campos['autor'].get());painel.close();self.abrir_obra(slug);self.anotar('Obra criada como rascunho: '+slug)
    if hasattr(self,'biblioteca_obras'):self.biblioteca_obras.atualizar()
   except Exception as e:painel.set_error(str(e))
  ttk.Button(painel.footer,text='Criar obra',command=criar).pack(pady=10)
 def estado_obra(self,slug):
  if not self._continuar_obras():return
  try:
   path=f'{slug}/dados/info-obra.json';info,rev=self.projeto.ler(path);estado='rascunho' if info['estado_publicacao']=='arquivado' else 'arquivado'
   painel=OverlayPanel(self,'Alterar publicação da obra',width=720,height=430)
   ttk.Label(painel.body,text=f"{info['titulo']}\n\nPublicação: {info['estado_publicacao']} → {estado}\n\nA obra e suas autorias continuam no projeto. O próximo site gerado refletirá essa mudança. Publicar exige editar a ficha e validar o conteúdo.",wraplength=600).pack(anchor='w',pady=20)
   def aplicar():
    try:
     self.projeto.editar_obra(slug,{'estado_publicacao':estado},rev);painel.close();self.inventario()
     if self.atual and self.atual[0]==slug:self.carregar(self.atual)
     self.gerenciar_obras()
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Confirmar com backup',command=aplicar).pack(pady=10)
  except Exception as e:messagebox.showerror('Obras',str(e),parent=self)
 def exportar_fontes_obra(self,slug):
  if not self._continuar_obras():return
  if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug and not self.salvar_autoria():return
  destino=filedialog.asksaveasfilename(parent=self,title='Exportar fontes da obra — inclui autorias privadas',initialfile=slug+'-fontes.zip',defaultextension='.zip',filetypes=[('Pacote de fontes','*.zip')])
  if not destino:return
  try:self.projeto.exportar_obra(slug,destino);self.anotar('Fontes da obra exportadas: '+destino+' (inclui autoria; recursos compartilhados não incluídos).')
  except Exception as e:messagebox.showerror('Exportar fontes',str(e),parent=self)
 def excluir_obra(self,slug):
  if not self._continuar_obras():return
  try:
   if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug and not self.salvar_autoria():return
   proposta=self.projeto.preparar_exclusao_obra(slug);painel=OverlayPanel(self,'Excluir obra com recuperação',width=760,height=510)
   ttk.Label(painel.body,text=f"{proposta['titulo']}\nEndereço: {slug}\n\nA obra será retirada do cadastro. Sua pasta completa, incluindo capítulos e autorias salvas, ficará na recuperação local. Recursos compartilhados continuarão no projeto. O editor aberto desta obra será fechado. O site gerado anteriormente só muda ao gerar novamente.\n\nDigite o endereço da obra para confirmar:",wraplength=640).pack(anchor='w',pady=15)
   confirmar=ttk.Entry(painel.body);confirmar.pack(fill='x')
   def aplicar():
    if confirmar.get()!=slug:painel.set_error('Digite exatamente o endereço da obra.');return
    try:
     if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug and self.editor.dirty:
      painel.set_error('A autoria mudou. Feche esta revisão e salve antes de excluir.');return
     self.projeto.excluir_obra(proposta);painel.close();self.limpar_obra_removida(slug);self.inventario();self.gerenciar_obras();self.anotar('Obra retirada do cadastro e guardada para recuperação: '+slug)
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Excluir e guardar para recuperação',command=aplicar).pack(pady=10)
  except Exception as e:messagebox.showerror('Excluir obra',str(e),parent=self)
 def limpar_obra_removida(self,slug):
  if self.editor and self.editor.vinculo and self.editor.vinculo['slug']==slug:
   self.editor.destroy();self.editor=None;self.editor_chave=None;self.configure(menu='')
   ttk.Label(self.aba_editor,text='Selecione um capítulo e abra o editor semântico.',padding=25).pack()
  if self.atual and self.atual[0]==slug:
   self.atual=None;self._iid_atual=None;self.widgets={};self.base=None;self.obj=None
   for w in self.form.winfo_children():w.destroy()
   self.cabecalho.configure(text='Selecione uma obra');self.caminho_atual.set('')
  if hasattr(self,'biblioteca_personagens') and self.biblioteca_personagens.slug==slug:
   self.biblioteca_personagens.slug=None;self.biblioteca_personagens.catalogo={};self.biblioteca_personagens.contagens={};self.biblioteca_personagens.titulo.set('Biblioteca de personagens');self.biblioteca_personagens.filtrar()
 def restaurar_obra(self):
  if not self._continuar_obras():return
  try:
   excluidas=self.projeto.obras_excluidas();painel=OverlayPanel(self,'Restaurar obra excluída',width=780,height=560,scrollable=True)
   ttk.Label(painel.body,text='A restauração conserva identidades, capítulos e autorias. A obra volta como rascunho para revisão antes da publicação.',wraplength=650).pack(anchor='w',pady=15)
   if not excluidas:ttk.Label(painel.body,text='Nenhuma obra disponível para restauração.').pack(anchor='w')
   for item in excluidas:
    quadro=ttk.LabelFrame(painel.body,text=item['titulo'],padding=10);quadro.pack(fill='x',pady=6)
    ttk.Label(quadro,text=item['slug']+' — '+item['id_obra'],wraplength=600).pack(anchor='w')
    def restaurar(token=item['token']):
     try:
      slug=self.projeto.restaurar_obra(token);painel.close();self.abrir_obra(slug);self.anotar('Obra restaurada como rascunho: '+slug)
      if hasattr(self,'biblioteca_obras'):self.biblioteca_obras.atualizar()
     except Exception as e:painel.set_error(str(e))
    ttk.Button(quadro,text='Restaurar como rascunho',command=restaurar).pack(anchor='w',pady=5)
  except Exception as e:messagebox.showerror('Restaurar obra',str(e),parent=self)

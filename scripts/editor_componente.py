"""Adapta o editor fornecido a um componente Tk, sem alterar a cópia de origem."""
import tkinter as tk
from tkinter import ttk
import html
import copy
from editor_semantico import editor_semantico as modulo
# Vocabulário do componente é próprio; a distribuição recebida fica intacta.
INLINE_ELEMENTS = {k:dict(v) for k,v in modulo.INLINE_ELEMENTS.items()}
INLINE_ELEMENTS['span']['attrs'] += ('data-glossary-term','data-verbete-id')
# A roda é gerida por um único roteador do Studio, inclusive sobre filhos.
modulo.ScrollableFrame._bind_wheel=lambda self,event=None:None
modulo.ScrollableFrame._unbind_wheel=lambda self,event=None:None
class SemanticWidget(tk.Frame, modulo.SemanticEditor):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent,bg=modulo.COLORS['app_bg'])
        modulo.INLINE_ELEMENTS.update(INLINE_ELEMENTS)
        self.overlay_stack = []
        self._metrics_job = None
        self._initialization_failed = False
        self.configure_styles()

        schema_candidates = [modulo.script_dir() / "schema.json", modulo.script_dir() / "schema(1).json"]
        self.schema_path = next((path for path in schema_candidates if path.exists()), schema_candidates[0])
        try:
            self.schema = self.carregar_schema_integrado()
        except Exception as exc:
            self._initialization_failed = True
            tk.Label(
                self, text="Não foi possível iniciar o editor.", bg=modulo.COLORS["app_bg"],
                fg=modulo.COLORS["danger"], font=("TkDefaultFont", 14, "bold")
            ).pack(expand=True)
            self.after_idle(
                lambda erro=str(exc): self.notify("Schema", f"Não foi possível abrir schema.json:\n{erro}", "error")
            )
            return

        self.project_path = None
        self.dirty = False
        self.entities = {}
        self.marks = {}
        self.chapter_elements = {"anteriormente": "", "previa": ""}
        self.glossary = {}
        self.section_meta = self.default_section_meta(scope="chapter")
        self.subsections = {}
        self.lists = {}
        self.inline_structures = {}
        self.horizontal_rules = {}
        self.tags_visible = tk.BooleanVar(self, True)

        self.build_ui()
        self.configure_text_tags()
        self.bind_shortcuts()
        self.update_status()
        self.update_document_metrics()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.text.configure(exportselection=False)
    def carregar_schema_integrado(self):
        schema=copy.deepcopy(modulo.load_schema(self.schema_path))
        atributos=[*schema['section']['attributes'].values(),*[a for role in schema['roles'].values() for a in role.get('attributes',{}).values()]]
        for spec in atributos:
            if spec.get('kind')=='entity_ref' and 'character' in spec.get('entity_types',[]) and 'creature' not in spec['entity_types']:
                spec['entity_types'].append('creature')
        schema['section']['attributes']['data-pov-display-name']={'kind':'text','required':False}
        for role in ('dialogue','thought','quotation'):
            schema['roles'][role]['attributes']['data-display-name']={'kind':'text','required':False}
        return schema
    def reload_schema(self):
        try:
            schema=self.carregar_schema_integrado()
        except Exception as exc:
            self.notify('Schema',f'Erro ao recarregar schema.json:\n{exc}','error')
            return
        self.schema=schema
        self.notify('Schema','Schema recarregado. Marcações existentes foram preservadas; a exportação validará os valores.','success')
    def build_ui(self):
        modulo.SemanticEditor.build_ui(self)
        workspace=next(w for w in self.winfo_children() if w.grid_slaves(row=0,column=1))
        self._workspace=workspace
        self._painel_ferramentas=workspace.grid_slaves(row=0,column=0)[0]
        self._painel_propriedades=workspace.grid_slaves(row=0,column=2)[0]
        self._largura_layout=None;self._painel_compacto='auto'
        self._barra_compacta=ttk.Frame(self,padding=(12,3))
        self._botao_ferramentas=ttk.Button(self._barra_compacta,text='Ferramentas',command=lambda:self.alternar_painel('ferramentas'))
        self._botao_ferramentas.pack(side='left',padx=3)
        self._botao_propriedades=ttk.Button(self._barra_compacta,text='Propriedades semânticas',command=lambda:self.alternar_painel('propriedades'))
        self._botao_propriedades.pack(side='left',padx=3)
        workspace.bind('<Configure>',self.layout_responsivo,add='+')
    def alternar_painel(self,nome):
        atual=self._painel_compacto
        if atual=='auto':atual='ferramentas' if self._workspace.winfo_width()>=620 else None
        self._painel_compacto=None if atual==nome else nome
        self.layout_responsivo(forcar=True)
    def layout_responsivo(self,event=None,forcar=False):
        largura=self._workspace.winfo_width()
        if largura==self._largura_layout and not forcar:return
        self._largura_layout=largura
        if largura>=1000:
            self._barra_compacta.pack_forget();self._painel_ferramentas.grid();self._painel_propriedades.grid();self._painel_compacto='auto'
        else:
            self._barra_compacta.pack(before=self._workspace,fill='x')
            ativo=self._painel_compacto
            if ativo=='auto':ativo='ferramentas' if largura>=620 else None
            self._painel_ferramentas.grid_remove();self._painel_propriedades.grid_remove()
            if ativo=='ferramentas':self._painel_ferramentas.grid()
            if ativo=='propriedades':self._painel_propriedades.grid()
            self._botao_ferramentas.configure(text=('Ocultar ferramentas' if ativo=='ferramentas' else 'Ferramentas'))
            self._botao_propriedades.configure(text=('Ocultar propriedades' if ativo=='propriedades' else 'Propriedades semânticas'))
    def abrir_autoria(self,data):
        self.load_project_data(data)
    def exportar_capitulo(self):
        return self.build_html()
    def render_glossary_text(self,value):
        # Marcações explícitas prevalecem sobre a busca automática de palavras.
        if any('data-glossary-term' in item.get('attrs',{}) for item in self.inline_structures.values()):
            return html.escape(str(value or ''))
        return modulo.SemanticEditor.render_glossary_text(self,value)
    def title(self,text=None):
        if text is not None:self.titulo_documento=text
        return getattr(self,'titulo_documento','Editor semântico')
    def geometry(self,*args):pass
    def minsize(self,*args):pass
    def protocol(self,*args):pass
    def configure(self,cnf=None,**kw):
        if 'menu' in kw:self.menu_documento=kw.pop('menu')
        return super().configure(cnf,**kw)
    config=configure
    def bind_shortcuts(self):
        comandos={'<Control-n>':self.new_project,'<Control-o>':self.open_project,'<Control-s>':self.save_project,'<Control-Shift-S>':self.export_html,'<Control-b>':lambda:self.toggle_format('fmt_bold'),'<Control-i>':lambda:self.toggle_format('fmt_italic'),'<Control-u>':lambda:self.toggle_format('fmt_underline'),'<Control-m>':self.mark_selection,'<Escape>':self.close_active_overlay}
        for tecla,comando in comandos.items():
            def executar(event,cmd=comando):cmd();return 'break'
            self.text.bind(tecla,executar)
    def notify(self,*args,**kwargs):
        host=self.winfo_toplevel()
        if hasattr(host,'exibir_editor'):host.exibir_editor(self)
        return super().notify(*args,**kwargs)
    def ask_confirmation(self,*args,**kwargs):
        host=self.winfo_toplevel()
        if hasattr(host,'exibir_editor'):host.exibir_editor(self)
        return super().ask_confirmation(*args,**kwargs)
    def on_close(self):
        # A sessão é propriedade do Studio. Fechar painéis não destrói a aplicação.
        if self.overlay_stack:self.close_active_overlay()
        elif hasattr(self.winfo_toplevel(),'sair'):self.winfo_toplevel().sair()
OverlayPanel=modulo.OverlayPanel

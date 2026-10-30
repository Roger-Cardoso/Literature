"""Configuração de publicação e comentários próprios na janela do Studio."""
import tkinter as tk
from tkinter import ttk,messagebox
from configuracao_site import carregar,validar
from editor_componente import OverlayPanel
from gerar_site import preparar
from moderacao_visual import ModeracaoMixin

class SiteMixin(ModeracaoMixin):
 def configurar_site(self):
  if not self.continuar():return
  try:
   config=carregar(self.projeto.root);_,rev=(self.projeto.ler('configuracao-site.json') if (self.projeto.root/'configuracao-site.json').exists() else (None,None));c=config['comentarios']
   painel=OverlayPanel(self,'Site e comentários',width=800,height=730,scrollable=True)
   ttk.Label(painel.body,text='Comentários do Literature',font=('Georgia',19)).pack(anchor='w',pady=10)
   campos={}
   for key,label,value in [('url','Endereço HTTPS público — deve corresponder ao CNAME',config['url_publica']),('api','Endereço HTTPS do serviço de comentários — Worker',c['api_url']),('sitekey','Chave pública do Cloudflare Turnstile',c['turnstile_site_key'])]:
    ttk.Label(painel.body,text=label).pack(anchor='w');w=ttk.Entry(painel.body);w.insert(0,value);w.pack(fill='x',pady=5);campos[key]=w
   ativo=tk.BooleanVar(value=c['ativado']);obras=tk.BooleanVar(value=c['obras']);capitulos=tk.BooleanVar(value=c['capitulos'])
   for label,var in [('Ativar comentários próprios',ativo),('Comentários nas páginas das obras, por padrão',obras),('Comentários nos capítulos, por padrão',capitulos)]:ttk.Checkbutton(painel.body,text=label,variable=var).pack(anchor='w',pady=5)
   ttk.Label(painel.body,text='Os visitantes enviam nome e texto, sem conta externa. Cada mensagem depende de aprovação. Obras e capítulos podem herdar, ativar ou desativar comentários na ficha. A prévia local e a edição offline não enviam comentários reais.',wraplength=650).pack(anchor='w',pady=12)
   ttk.Label(painel.body,text='Aqui entram apenas endereços e chave pública. A credencial de moderação, a chave secreta do Turnstile e o segredo de proteção de IP ficam no serviço Cloudflare; nunca os coloque nestes campos. Depois de salvar, gere e publique o site e sincronize as discussões na moderação.',wraplength=650).pack(anchor='w',pady=10)
   estado=tk.StringVar();ttk.Label(painel.body,textvariable=estado,wraplength=650).pack(anchor='w',pady=10)
   try:
    publicas=preparar(self.projeto.root);estado.set(f'Fontes válidas: {len(self.projeto.obras())} obra(s) cadastrada(s), {len(publicas)} pública(s). '+('O catálogo público está vazio.' if not publicas else ''))
   except Exception as e:estado.set('Pendências nas fontes: '+str(e))
   def salvar():
    try:
     novo=validar({'schema_version':2,'url_publica':campos['url'].get().strip(),'comentarios':{'ativado':ativo.get(),'api_url':campos['api'].get().strip(),'turnstile_site_key':campos['sitekey'].get().strip(),'obras':obras.get(),'capitulos':capitulos.get()}},(self.projeto.root/'CNAME').read_text().strip())
     self.projeto.salvar('configuracao-site.json',novo,rev);painel.close();self.anotar('Configuração salva. Gere e publique o site e sincronize as discussões para ativar os comentários.')
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Salvar configuração com backup',command=salvar).pack(side='left',padx=5,pady=10)
   def moderar():painel.close();self.moderar_comentarios()
   ttk.Button(painel.footer,text='Abrir moderação…',command=moderar).pack(side='left',padx=5,pady=10)
  except Exception as e:messagebox.showerror('Site e comentários',str(e),parent=self)

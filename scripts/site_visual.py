"""Configuração de publicação e comentários na janela do Studio."""
import copy
import tkinter as tk
from tkinter import ttk,messagebox
from configuracao_site import carregar,validar
from editor_componente import OverlayPanel
from gerar_site import preparar

class SiteMixin:
 def configurar_site(self):
  if not self.continuar():return
  try:
   config=carregar(self.projeto.root);_,rev=(self.projeto.ler('configuracao-site.json') if (self.projeto.root/'configuracao-site.json').exists() else (None,None))
   painel=OverlayPanel(self,'Site e comentários',width=800,height=690,scrollable=True)
   ttk.Label(painel.body,text='Publicação estática e comentários externos',font=('Georgia',19)).pack(anchor='w',pady=10)
   ttk.Label(painel.body,text='Endereço HTTPS público — deve corresponder ao CNAME').pack(anchor='w');url=ttk.Entry(painel.body);url.insert(0,config['url_publica']);url.pack(fill='x',pady=5)
   ativo=tk.BooleanVar(value=config['disqus']['ativado']);obras=tk.BooleanVar(value=config['disqus']['obras']);capitulos=tk.BooleanVar(value=config['disqus']['capitulos'])
   ttk.Checkbutton(painel.body,text='Ativar integração com o Disqus',variable=ativo).pack(anchor='w',pady=10)
   ttk.Label(painel.body,text='Shortname do Disqus — somente o nome antes de .disqus.com').pack(anchor='w');short=ttk.Entry(painel.body);short.insert(0,config['disqus']['shortname']);short.pack(fill='x',pady=5)
   ttk.Checkbutton(painel.body,text='Comentários nas páginas das obras, por padrão',variable=obras).pack(anchor='w',pady=5)
   ttk.Checkbutton(painel.body,text='Comentários nos capítulos, por padrão',variable=capitulos).pack(anchor='w',pady=5)
   ttk.Label(painel.body,text='Cada obra e capítulo pode herdar a configuração, ativar ou desativar comentários na ficha. Desativar na obra também bloqueia seus capítulos. O serviço só carrega após o leitor clicar; prévias locais e versões offline não carregam o Disqus. O plano gratuito pode exibir anúncios.',wraplength=650).pack(anchor='w',pady=12)
   ttk.Label(painel.body,text='Cadastre o domínio literatura.roger.cardoso.nom.br no Disqus, informe-o nos domínios confiáveis e use o shortname fornecido. Este formulário não cria contas nem altera DNS. Depois de salvar, gere o site novamente.',wraplength=650).pack(anchor='w',pady=10)
   estado=tk.StringVar(value='Conferindo preparação local…');ttk.Label(painel.body,textvariable=estado,wraplength=650).pack(anchor='w',pady=10)
   try:
    publicas=preparar(self.projeto.root);estado.set(f'Fontes válidas: {len(self.projeto.obras())} obra(s) cadastrada(s), {len(publicas)} pública(s). '+('O catálogo público está vazio.' if not publicas else ''))
   except Exception as e:estado.set('Pendências nas fontes: '+str(e))
   def salvar():
    try:
     novo=validar({'schema_version':1,'url_publica':url.get().strip(),'disqus':{'ativado':ativo.get(),'shortname':short.get().strip(),'obras':obras.get(),'capitulos':capitulos.get()}},(self.projeto.root/'CNAME').read_text().strip())
     self.projeto.salvar('configuracao-site.json',novo,rev);painel.close();self.anotar('Configuração do site salva. Gere o site para publicar as alterações de comentários.')
    except Exception as e:painel.set_error(str(e))
   ttk.Button(painel.footer,text='Salvar configuração com backup',command=salvar).pack(pady=10)
  except Exception as e:messagebox.showerror('Site e comentários',str(e),parent=self)

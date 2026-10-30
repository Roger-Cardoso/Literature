"""Implanta o serviço autorizado, com credenciais fora do projeto e sem imprimi-las."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import tomllib
from urllib import request,error
from urllib.parse import urlsplit
import uuid
from configuracao_site import carregar
from gestao_projeto import Projeto,ROOT

PRIVADO=Path.home()/'.config/literature/comments-admin.json'

def gravar_privado(path,dados):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 if path.is_symlink():raise ValueError('Arquivo privado não pode ser um vínculo simbólico.')
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.credencial-')
 try:
  os.chmod(tmp,0o600)
  with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(dados,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if Path(tmp).exists():Path(tmp).unlink()

def token_oauth():
 token=os.getenv('CLOUDFLARE_API_TOKEN')
 if token:return token
 arquivo=Path.home()/'.config/.wrangler/config/default.toml'
 try:token=tomllib.loads(arquivo.read_text(encoding='utf-8')).get('oauth_token')
 except (OSError,ValueError):token=None
 if not token:raise ValueError('Autentique com npx wrangler login antes de implantar.')
 return token

class Cloudflare:
 def __init__(self,token):self.token=token
 def api(self,path,method='GET',data=None):
  req=request.Request('https://api.cloudflare.com/client/v4'+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json','User-Agent':'LiteratureStudio/1.0'})
  try:
   with request.urlopen(req,timeout=30) as r:res=json.load(r)
  except error.HTTPError as e:raise ValueError(f'Cloudflare recusou {method} {path} (HTTP {e.code}). Nenhuma credencial foi exibida.') from None
  if not res.get('success'):raise ValueError('Cloudflare não confirmou a operação. Confira permissões e cotas no painel.')
  return res['result']

def wrangler(root,args,account,input_data=None):
 env=dict(os.environ,CLOUDFLARE_ACCOUNT_ID=account)
 comando=['npx','--no-install','wrangler',*args]
 r=subprocess.run(comando,cwd=root/'backend/comentarios',env=env,input=input_data,text=True,capture_output=True)
 if r.returncode:raise ValueError('Falha no Wrangler: '+args[0]+'. Confira autenticação, banco e configuração; os segredos não foram exibidos.')

def implantar(root=ROOT,account_id=None,arquivo_privado=PRIVADO):
 root=Path(root).resolve();arquivo_privado=Path(arquivo_privado).expanduser()
 if arquivo_privado.is_symlink():raise ValueError('Arquivo privado não pode ser um vínculo simbólico.')
 arquivo_privado=arquivo_privado.resolve()
 if arquivo_privado.is_relative_to(root):raise ValueError('Guarde as credenciais fora da pasta do projeto.')
 config=carregar(root);origem=config['url_publica'];cf=Cloudflare(token_oauth());contas=cf.api('/accounts')
 if account_id:
  if account_id not in {c['id'] for c in contas}:raise ValueError('Conta não encontrada entre as contas autorizadas.')
 elif len(contas)==1:account_id=contas[0]['id']
 else:
  print(json.dumps([{'id':c['id'],'nome':c['name']} for c in contas],ensure_ascii=False));raise ValueError('Escolha a conta com --account-id antes de criar recursos.')
 base='/accounts/'+account_id
 estado=json.loads(arquivo_privado.read_text()) if arquivo_privado.exists() else None
 if estado and (estado.get('account_id')!=account_id or estado.get('site_origin')!=origem):raise ValueError('O arquivo privado pertence a outra conta ou site. Escolha outro destino.')
 if not estado:
  scripts=cf.api(base+'/workers/scripts');bancos=cf.api(base+'/d1/database?per_page=100');nome='literature-comments'
  if nome in {s['id'] for s in scripts} or nome in {b['name'] for b in bancos}:nome+='-'+uuid.uuid4().hex[:8]
  estado={'account_id':account_id,'site_origin':origem,'worker_name':nome,'database_name':nome,'admin_token':secrets.token_hex(32),'ip_hash_secret':secrets.token_hex(32)}
  gravar_privado(arquivo_privado,estado)
 if not estado.get('database_id'):
  banco=cf.api(base+'/d1/database','POST',{'name':estado['database_name']});estado['database_id']=banco['uuid'];gravar_privado(arquivo_privado,estado)
 if not estado.get('turnstile_site_key'):
  widget=cf.api(base+'/challenges/widgets','POST',{'name':'Literature comentários','domains':[urlsplit(origem).hostname],'mode':'managed'})
  estado['turnstile_site_key']=widget['sitekey'];estado['turnstile_secret_key']=widget['secret'];gravar_privado(arquivo_privado,estado)
 print('Recursos do serviço preparados. Aplicando migração e implantação…',flush=True)
 wrangler_path=root/'backend/comentarios/wrangler.jsonc';w=json.loads(wrangler_path.read_text());w['name']=estado['worker_name'];w['vars']['SITE_ORIGIN']=origem;w['d1_databases'][0].update(database_name=estado['database_name'],database_id=estado['database_id']);wrangler_path.write_text(json.dumps(w,ensure_ascii=False,indent=2)+'\n')
 wrangler(root,['d1','migrations','apply',estado['database_name'],'--remote'],account_id)
 wrangler(root,['deploy'],account_id)
 valores={'ADMIN_TOKEN':estado['admin_token'],'IP_HASH_SECRET':estado['ip_hash_secret'],'TURNSTILE_SECRET_KEY':estado['turnstile_secret_key']}
 wrangler(root,['secret','bulk'],account_id,json.dumps(valores))
 subdominio=cf.api(base+'/workers/subdomain')['subdomain']
 estado['api_url']='https://'+estado['worker_name']+'.'+subdominio+'.workers.dev';gravar_privado(arquivo_privado,estado)
 return conectar_servico(root,estado,arquivo_privado)

def conectar_servico(root,estado,arquivo_privado=PRIVADO):
 root=Path(root);config=carregar(root)
 with request.urlopen(request.Request(estado['api_url']+'/v1/health',headers={'User-Agent':'LiteratureStudio/1.0'}),timeout=30) as r:saude=json.load(r)
 if not saude.get('ready'):raise ValueError('Serviço implantado, mas ainda não pronto. Confira os segredos na Cloudflare.')
 projeto=Projeto(root);path='configuracao-site.json';_,rev=projeto.ler(path);config['comentarios'].update(ativado=True,api_url=estado['api_url'],turnstile_site_key=estado['turnstile_site_key']);projeto.salvar(path,config,rev)
 from gerar_site import gerar
 from cliente_comentarios import ClienteComentarios
 gerar(root);manifesto=json.loads((root/'site/comentarios-manifesto.json').read_text());ClienteComentarios(estado['api_url'],estado['admin_token']).sincronizar(manifesto)
 print(json.dumps({'servico':estado['api_url'],'pronto':True,'discussoes':len(manifesto['threads']),'credencial_local':str(arquivo_privado),'proximo_passo':'Publicar a versão gerada do site. Nenhum plano pago foi contratado.'},ensure_ascii=False))
 return estado['api_url']

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--account-id');parser.add_argument('--concluir',action='store_true',help='Somente verificar o serviço e conectar o site já implantado');parser.add_argument('--credencial',type=Path,default=PRIVADO);a=parser.parse_args()
 try:
  if a.concluir:conectar_servico(ROOT,json.loads(a.credencial.read_text()),a.credencial)
  else:implantar(account_id=a.account_id,arquivo_privado=a.credencial)
 except (ValueError,OSError,error.URLError) as e:parser.exit(1,'Implantação interrompida: '+str(e)+'\n')
if __name__=='__main__':main()

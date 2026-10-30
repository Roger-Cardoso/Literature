"""Publicação por API autenticada pelo GitHub CLI, sem depender do Git local."""
import base64
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote
from pacote_publicacao import MARCADOR,git_blob

PREFIXO='publicado/'
PROTOCOLO='literature-studio-snapshot-v1'
PADRAO={'schema_version':1,'repositorio':'Roger-Cardoso/Literature','branch':'main','sincronizar_comentarios':True}
class ErroPublicacao(ValueError):pass

def destino(repo,branch):
 repo=repo.strip().removeprefix('https://github.com/').removesuffix('/').removesuffix('.git')
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+',repo):raise ValueError('Informe o repositório como proprietário/nome ou URL do GitHub.')
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]{0,100}',branch) or any(x in branch for x in ('..','//','@{')) or any(not p or p.startswith('.') or p.endswith(('.','.lock')) for p in branch.split('/')):raise ValueError('Nome de branch inválido.')
 return repo,branch

def configuracao(root):
 path=Path(root)/'.literature-studio.json'
 d=json.loads(path.read_text()) if path.exists() else dict(PADRAO)
 repo,branch=destino(d['repositorio'],d['branch'])
 return {**PADRAO,**d,'repositorio':repo,'branch':branch}

def ambiente():
 env=dict(os.environ);env.pop('GH_DEBUG',None);env['GH_PROMPT_DISABLED']='1';return env

def limpar_erro(text):return re.sub(r'(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]+','[credencial omitida]',str(text))[:1800]

class GitHub:
 def chamar(self,path,metodo='GET',dados=None):
  if not shutil.which('gh'):raise ErroPublicacao('Instale o GitHub CLI e conecte sua conta para publicar pelo Studio.')
  args=['gh','api','--hostname','github.com','--method',metodo,path]
  if dados is not None:args+=['--input','-']
  try:r=subprocess.run(args,input=json.dumps(dados,ensure_ascii=False) if dados is not None else None,capture_output=True,text=True,encoding='utf-8',timeout=90,env=ambiente())
  except subprocess.TimeoutExpired:raise ErroPublicacao('O GitHub demorou a responder. Consulte o último envio antes de tentar novamente.') from None
  if r.returncode:raise ErroPublicacao(limpar_erro(r.stderr or r.stdout or 'O GitHub recusou a operação.'))
  return json.loads(r.stdout) if r.stdout.strip() else None
 def usuario(self):return self.chamar('user')['login']

def base_remota(gh,repo,branch):
 repo,branch=destino(repo,branch);api='repos/'+repo;ref=gh.chamar(api+'/git/ref/heads/'+quote(branch,safe=''))
 sha=ref['object']['sha'];commit=gh.chamar(api+'/git/commits/'+sha)
 tree=gh.chamar(api+'/git/trees/'+commit['tree']['sha']+'?recursive=1')
 if tree.get('truncated'):raise ErroPublicacao('A árvore remota está incompleta. Não é seguro preparar este envio.')
 rows={x['path']:x for x in tree['tree']}
 if 'publicado' in rows and rows['publicado']['type']!='tree':raise ErroPublicacao('Já existe um arquivo no endereço reservado publicado/.')
 publicos={p:row for p,row in rows.items() if p.startswith(PREFIXO) and row['type']!='tree'}
 if publicos and PREFIXO+MARCADOR not in publicos:raise ErroPublicacao('A pasta publicado/ já existe sem identificação do Studio. Confira o repositório antes de continuar.')
 if any(row.get('mode') not in {'100644','100755'} or row['type']!='blob' for row in publicos.values()):raise ErroPublicacao('A publicação remota contém vínculos ou entradas não suportadas.')
 workflow=gh.chamar(api+'/contents/.github/workflows/pages.yml?ref='+quote(branch,safe=''))
 codigo=base64.b64decode(workflow['content']).decode('utf-8')
 if PROTOCOLO not in codigo:raise ErroPublicacao('O fluxo do repositório precisa da integração de publicação do Studio antes do primeiro envio.')
 return {'repositorio':repo,'branch':branch,'head':sha,'tree':commit['tree']['sha'],'arquivos':publicos}

def preparar_revisao(pacote,gh,repo,branch):
 pacote.conferir();base=base_remota(gh,repo,branch);mudancas=[]
 locais={PREFIXO+r:r for r in pacote.arquivos()}
 for path,rel in locais.items():
  data=pacote.ler(rel)
  if len(data)>50*1024*1024:raise ErroPublicacao('Arquivo acima de 50 MB: '+rel)
  old=base['arquivos'].get(path)
  if old and old['sha']==git_blob(data):continue
  mudancas.append({'path':path,'rel':rel,'acao':'alterar' if old else 'criar','bytes':len(data)})
 for path in base['arquivos']:
  if path not in locais:mudancas.append({'path':path,'rel':path[len(PREFIXO):],'acao':'remover','bytes':0})
 if sum(x['bytes'] for x in mudancas)>150*1024*1024:raise ErroPublicacao('Envio acima de 150 MB. Reduza o tamanho dos recursos desta publicação.')
 return {**base,'mudancas':sorted(mudancas,key=lambda x:x['path']),'conteudo_sha256':pacote.meta['conteudo_sha256']}

def enviar(pacote,revisao,gh,mensagem):
 pacote.conferir();repo,branch=destino(revisao['repositorio'],revisao['branch']);api='repos/'+repo
 if not mensagem.strip():raise ValueError('Escreva uma descrição para esta atualização.')
 if len(mensagem)>500:raise ValueError('Use até 500 caracteres na descrição.')
 refpath=api+'/git/refs/heads/'+quote(branch,safe='')
 def conferir_remoto():
  atual=gh.chamar(api+'/git/ref/heads/'+quote(branch,safe=''))['object']['sha']
  if atual!=revisao['head']:raise ErroPublicacao('O repositório mudou após a revisão. Prepare novamente para preservar essas alterações.')
 conferir_remoto()
 if not revisao['mudancas']:return {'commit':revisao['head'],'sem_alteracoes':True,'repositorio':repo,'branch':branch}
 # Árvores intermediárias mantêm os pedidos pequenos; nada é publicado antes do commit final.
 tree=revisao['tree'];lote=[];tamanho=0
 def gravar_lote():
  nonlocal tree,lote,tamanho
  if lote:tree=gh.chamar(api+'/git/trees','POST',{'base_tree':tree,'tree':lote})['sha'];lote=[];tamanho=0
 for item in revisao['mudancas']:
  path=item['path']
  if not path.startswith(PREFIXO) or path!=PREFIXO+item['rel']:raise ErroPublicacao('Caminho fora da publicação revisada.')
  entry={'path':path,'mode':'100644','type':'blob'}
  if item['acao']=='remover':entry['sha']=None
  else:
   data=pacote.ler(item['rel'])
   try:text=data.decode('utf-8') if len(data)<=128*1024 else None
   except UnicodeDecodeError:text=None
   if text is not None:entry['content']=text
   else:entry['sha']=gh.chamar(api+'/git/blobs','POST',{'content':base64.b64encode(data).decode(),'encoding':'base64'})['sha']
  size=len(json.dumps(entry,ensure_ascii=False).encode())
  if tamanho+size>1_000_000:gravar_lote()
  lote.append(entry);tamanho+=size
 gravar_lote();pacote.conferir();conferir_remoto()
 commit=gh.chamar(api+'/git/commits','POST',{'message':mensagem.strip(),'tree':tree,'parents':[revisao['head']]})['sha']
 conferir_remoto()
 try:gh.chamar(refpath,'PATCH',{'sha':commit,'force':False})
 except Exception:
  # Uma resposta perdida pode acontecer depois de o GitHub aceitar o envio.
  if gh.chamar(api+'/git/ref/heads/'+quote(branch,safe=''))['object']['sha']!=commit:raise
 return {'commit':commit,'repositorio':repo,'branch':branch,'url':'https://github.com/'+repo+'/commit/'+commit,'conteudo_sha256':pacote.meta['conteudo_sha256'],'manifesto_comentarios':pacote.manifesto_comentarios,'config_comentarios':pacote.config['comentarios'],'criado_em':datetime.now(timezone.utc).isoformat(),'sincronizado':False}

def salvar_recibo(root,recibo):
 from gestao_projeto import Projeto
 p=Projeto(root);path='.literature-publicacoes/ultimo.json';_,rev=p.ler(path) if p.caminho(path).exists() else ({},None);p.salvar(path,recibo,rev)

def ultimo_recibo(root):
 p=Path(root)/'.literature-publicacoes/ultimo.json';return json.loads(p.read_text()) if p.exists() else None

def acompanhar(gh,recibo):
 repo,branch=destino(recibo['repositorio'],recibo['branch']);query='?head_sha='+recibo['commit']+'&branch='+quote(branch,safe='')+'&event=push&per_page=10'
 runs=gh.chamar('repos/'+repo+'/actions/workflows/pages.yml/runs'+query)['workflow_runs']
 runs=[r for r in runs if r['head_sha']==recibo['commit'] and r.get('event','push')=='push']
 if not runs:return {'status':'aguardando','conclusion':None}
 run=max(runs,key=lambda r:(r.get('run_attempt',1),r['id']))
 return {'status':run['status'],'conclusion':run.get('conclusion'),'url':run['html_url'],'id':run['id']}

def sincronizar_comentarios(gh,recibo,arquivo_privado):
 if acompanhar(gh,recibo).get('conclusion')!='success':raise ErroPublicacao('Aguarde a implantação ser aprovada antes de sincronizar comentários.')
 repo,branch=destino(recibo['repositorio'],recibo['branch'])
 atual=gh.chamar('repos/'+repo+'/git/ref/heads/'+quote(branch,safe=''))['object']['sha']
 if atual!=recibo['commit']:
  # Atualizações de código/documentação podem conservar exatamente o pacote publicado.
  if acompanhar(gh,{**recibo,'commit':atual}).get('conclusion')!='success':raise ErroPublicacao('A atualização mais recente ainda não foi aprovada. Aguarde antes de sincronizar.')
  dado=gh.chamar('repos/'+repo+'/contents/'+PREFIXO+MARCADOR+'?ref='+atual)
  try:meta=json.loads(base64.b64decode(dado['content']))
  except (KeyError,ValueError):raise ErroPublicacao('Não foi possível conferir a publicação atual.') from None
  if meta.get('conteudo_sha256')!=recibo.get('conteudo_sha256'):raise ErroPublicacao('Há uma publicação diferente no repositório. Prepare novamente antes de sincronizar.')
 from cliente_comentarios import ClienteComentarios
 c=recibo['config_comentarios']
 if not c.get('api_url'):return {'total':0,'desativado':True}
 cred=json.loads(Path(arquivo_privado).read_text())
 if cred.get('api_url')!=c['api_url']:raise ErroPublicacao('A credencial local pertence a outro serviço.')
 return ClienteComentarios(c['api_url'],cred['admin_token']).sincronizar(recibo['manifesto_comentarios'])

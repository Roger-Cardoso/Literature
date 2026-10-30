"""Cliente administrativo HTTPS. A credencial só vive na sessão em memória."""
import json
from urllib import request,error,parse
import uuid
from configuracao_site import origem_https

class SemRedirecionamento(request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError('O serviço redirecionou a solicitação. Confira o endereço antes de enviar credenciais.')

class ClienteComentarios:
 def __init__(self,api_url,token):
  self.api_url=origem_https(api_url)
  if not isinstance(token,str) or len(token)<32:raise ValueError('Informe a credencial completa de moderação.')
  self._token=token;self._http=request.build_opener(SemRedirecionamento())
 def chamar(self,path,metodo='GET',dados=None):
  if not path.startswith('/v1/admin/'):raise ValueError('Rota administrativa inválida.')
  req=request.Request(self.api_url+path,data=json.dumps(dados,ensure_ascii=False).encode() if dados is not None else None,method=metodo,headers={'Authorization':'Bearer '+self._token,'Content-Type':'application/json','User-Agent':'LiteratureStudio/1.0'})
  try:
   with self._http.open(req,timeout=20) as r:conteudo=r.read(2_000_001)
  except error.HTTPError as e:
   try:mensagem=json.loads(e.read(10000)).get('error','Solicitação recusada.')
   except (ValueError,AttributeError):mensagem='O serviço recusou a solicitação.'
   raise ValueError(str(mensagem)) from None
  except error.URLError:raise ValueError('Não foi possível conectar ao serviço de comentários.') from None
  if len(conteudo)>2_000_000:raise ValueError('Resposta muito grande. Use uma página menor.')
  return json.loads(conteudo)
 def listar(self,estado='pending',depois=0,*,busca='',discussao=''):
  if len(busca)>100:raise ValueError('Use até 100 caracteres na busca.')
  return self.chamar('/v1/admin/comments?'+parse.urlencode({'status':estado,'after':depois,'limit':50,'q':busca,'thread':discussao}))
 def classificar_spoiler(self,ident,spoiler):
  uuid.UUID(ident)
  if not isinstance(spoiler,bool):raise ValueError('Classificação inválida.')
  return self.chamar('/v1/admin/comments/'+ident,'PATCH',{'spoiler':spoiler})
 def alterar(self,ident,estado):
  uuid.UUID(ident)
  return self.chamar('/v1/admin/comments/'+ident,'PATCH',{'status':estado})
 def excluir(self,ident):
  uuid.UUID(ident)
  return self.chamar('/v1/admin/comments/'+ident,'DELETE')
 def sincronizar(self,manifesto):
  if manifesto.get('schema_version')!=1 or not isinstance(manifesto.get('threads'),list):raise ValueError('Manifesto inválido. Gere o site novamente.')
  generation=str(uuid.uuid4());threads=manifesto['threads']
  for start in range(0,max(1,len(threads)),20):self.chamar('/v1/admin/threads','POST',{'generation':generation,'threads':threads[start:start+20]})
  return self.chamar('/v1/admin/threads/commit','POST',{'generation':generation,'total':len(threads)})
 def exportar(self):
  itens=[];after=0
  while True:
   pagina=self.listar('all',after);itens.extend(pagina['items']);seguinte=pagina.get('next')
   if seguinte is None:break
   if seguinte<=after:raise ValueError('Paginação inválida no serviço.')
   after=seguinte
  return {'schema_version':1,'comentarios':itens}

 def reacoes(self,depois='',busca=''):
  if len(busca)>100:raise ValueError('Use até 100 caracteres na busca.')
  return self.chamar('/v1/admin/reactions?'+parse.urlencode({'cursor':depois,'q':busca,'limit':50}))
 def pausar_reacoes(self,thread,pausado):
  if type(pausado) is not bool:raise ValueError('Informe se deseja pausar.')
  return self.chamar('/v1/admin/reactions','PATCH',{'thread':thread,'paused':pausado})
 def exportar_reacoes(self):
  itens=[];after=''
  while True:
   pagina=self.reacoes(after);itens.extend(pagina['items']);seguinte=pagina.get('next')
   if seguinte is None:break
   if not isinstance(seguinte,str) or seguinte<=after:raise ValueError('Paginação inválida no serviço.')
   after=seguinte
  return {'schema_version':1,'escopo':'catalogo_sincronizado','reacoes':itens}

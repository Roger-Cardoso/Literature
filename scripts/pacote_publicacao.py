"""Cópia pública imutável para revisão, envio e verificação no GitHub Actions."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import tempfile

MARCADOR='.literature-publicacao.json'
EXTENSOES={'.html','.css','.js','.json','.svg','.png','.jpg','.jpeg','.webp','.gif','.ico','.woff','.woff2','.txt'}
OBRIGATORIOS={'index.html','privacidade.html','home/index.html','catalogo.json','configuracao-site.json','CNAME','geracao.json','comentarios-manifesto.json'}

def permitido(rel):
 p=PurePosixPath(rel)
 if not rel or p.is_absolute() or '..' in p.parts or '\\' in rel or str(p)!=rel:return False
 if rel in {'CNAME','.nojekyll',MARCADOR}:return True
 if any(x.startswith('.') or x in {'autoria','node_modules','__pycache__','backend','scripts','tests','exports'} for x in p.parts):return False
 if p.name in {'editorial.json','comments-admin.json','publicacao-studio.json'}:return False
 return p.suffix.lower() in EXTENSOES

def git_blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def digest(files):return hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def inventariar(pasta):
 pasta=Path(pasta);files={}
 if not pasta.is_dir() or pasta.is_symlink():raise ValueError('Pasta de publicação inválida.')
 for p in sorted(pasta.rglob('*')):
  rel=p.relative_to(pasta).as_posix()
  if p.is_symlink():raise ValueError('A publicação contém um vínculo simbólico: '+rel)
  if not p.is_file():continue
  if not permitido(rel):raise ValueError('Arquivo não permitido na publicação: '+rel)
  if rel!=MARCADOR:files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
 if not OBRIGATORIOS.issubset(files):raise ValueError('Publicação incompleta: faltam arquivos obrigatórios.')
 return files

def verificar(pasta):
 pasta=Path(pasta);files=inventariar(pasta)
 try:meta=json.loads((pasta/MARCADOR).read_text(encoding='utf-8'))
 except (OSError,ValueError):raise ValueError('Manifesto da publicação inválido.') from None
 if meta.get('schema_version')!=1 or meta.get('arquivos')!=files or meta.get('conteudo_sha256')!=digest(files):raise ValueError('Os arquivos mudaram após a revisão. Prepare a publicação novamente.')
 from configuracao_site import carregar
 carregar(pasta)
 return meta

class PacotePublicacao:
 def __init__(self,root):
  from gerar_site import gerar
  from estado_publicacao import assinatura_fontes
  self.root=Path(root).resolve();gerar(self.root);self.assinatura=assinatura_fontes(self.root)
  self._temp=tempfile.TemporaryDirectory(prefix='literature-envio-');self.pasta=Path(self._temp.name)/'site'
  try:
   shutil.copytree(self.root/'site',self.pasta,symlinks=True)
   files=inventariar(self.pasta)
   if assinatura_fontes(self.root)!=self.assinatura:raise ValueError('As fontes mudaram durante a preparação.')
   self.meta={'schema_version':1,'arquivos':files,'conteudo_sha256':digest(files)}
   (self.pasta/MARCADOR).write_text(json.dumps(self.meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
   self.manifesto_comentarios=json.loads((self.pasta/'comentarios-manifesto.json').read_text())
   self.config=json.loads((self.pasta/'configuracao-site.json').read_text())
  except Exception:self.fechar();raise
 def conferir(self):
  from estado_publicacao import assinatura_fontes
  if assinatura_fontes(self.root)!=self.assinatura:raise ValueError('As fontes locais mudaram. Prepare e revise novamente antes de enviar.')
  if verificar(self.pasta)!=self.meta:raise ValueError('O pacote revisado foi alterado. Prepare novamente.')
 def arquivos(self):return sorted([*self.meta['arquivos'],MARCADOR])
 def ler(self,rel):
  if rel not in self.arquivos():raise ValueError('Arquivo fora do pacote revisado.')
  data=(self.pasta/rel).read_bytes()
  if rel==MARCADOR:
   if json.loads(data)!=self.meta:raise ValueError('Manifesto revisado alterado.')
  elif hashlib.sha256(data).hexdigest()!=self.meta['arquivos'][rel]:raise ValueError('Arquivo revisado alterado: '+rel)
  return data
 def fechar(self):self._temp.cleanup()

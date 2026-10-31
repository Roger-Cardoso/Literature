"""Operações locais do gerenciador; não envia alterações ao GitHub."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
import zipfile
import hierarquia as hier
import enderecos
from personagens import validar_catalogo,validar_participacoes,participacoes,referencias_em_html,personagem_referenciado_na_autoria

ROOT=Path(__file__).resolve().parents[1]
class ConflitoEdicao(ValueError):pass

def hash_arquivo(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

from obras_projeto import ObrasProjeto

class Projeto(ObrasProjeto):
    def __init__(self,root=ROOT):self.root=Path(root).resolve()
    def caminho(self,rel):
        p=(self.root/rel).resolve()
        if not p.is_relative_to(self.root) or p.is_relative_to(self.root/'site'):raise ValueError('Selecione um arquivo de origem dentro do projeto.')
        return p
    def ler(self,rel):
        p=self.caminho(rel);return json.loads(p.read_text(encoding='utf-8')),hash_arquivo(p)
    def salvar(self,rel,conteudo,revisao):
        p=self.caminho(rel)
        if hash_arquivo(p)!=revisao:raise ConflitoEdicao('O arquivo mudou fora do gerenciador. Recarregue antes de salvar para não perder alterações.')
        validando=conteudo
        if p.parent.name=='dados' and p.name in {'info-obra.json','editorial.json'} and isinstance(conteudo,str):validando=json.loads(conteudo)
        if p.parent.name=='dados' and p.name in {'info-obra.json','editorial.json'} and not isinstance(validando,dict):raise ValueError('Metadados da obra devem ser um objeto JSON.')
        if isinstance(validando,dict):
            pasta=p.parent
            if pasta.name=='dados' and p.name in {'info-obra.json','editorial.json'}:
                anterior=json.loads(p.read_text()) if p.exists() else None
                normalizado=enderecos.obra(validando,anterior) if p.name=='info-obra.json' else enderecos.numerar(validando,anterior)
                if isinstance(conteudo,dict):
                    if p.name=='info-obra.json':
                        for key in ('endereco_publico','enderecos_anteriores'):conteudo[key]=normalizado[key]
                    else:
                        conteudo['proximo_numero_url']=normalizado['proximo_numero_url'];numeros={n.id:n.item['numero_url'] for n in hier.nos(normalizado) if n.tipo=='capitulo'}
                        for n in hier.nos(conteudo):
                            if n.tipo=='capitulo':n.item['numero_url']=numeros[n.id]
                    validando=conteudo
                else:conteudo=json.dumps(normalizado,ensure_ascii=False,indent=2)+'\n';validando=normalizado
            if p.name=='info-obra.json' and pasta.name=='dados':
                enderecos.validar_catalogo([(slug,enderecos.obra(validando if slug==pasta.parent.name else self.ler(f'{slug}/dados/info-obra.json')[0])) for slug in dict.fromkeys([*(self.obras() if (self.root/'obras.json').exists() else []),pasta.parent.name])])
                validar_catalogo(validando)
                if (pasta/'editorial.json').exists():validar_participacoes(validando,json.loads((pasta/'editorial.json').read_text(encoding='utf-8')))
            if p.name=='editorial.json' and pasta.name=='dados' and (pasta/'info-obra.json').exists():validar_participacoes(json.loads((pasta/'info-obra.json').read_text(encoding='utf-8')),validando)
        dados=conteudo.encode('utf-8') if isinstance(conteudo,str) else (json.dumps(conteudo,ensure_ascii=False,indent=2)+'\n').encode()
        if p.exists():
            backup=self.root/'.literature-backups'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')/p.relative_to(self.root)
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup)
        p.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.edicao-')
        try:
            with os.fdopen(fd,'wb') as f:f.write(dados);f.flush();os.fsync(f.fileno())
            os.replace(tmp,p)
        finally:
            if Path(tmp).exists():Path(tmp).unlink()
        return hash_arquivo(p)
    def usos_personagem(self,slug,ident):
        info,_=self.ler(f'{slug}/dados/info-obra.json');arvore,_=self.ler(f'{slug}/dados/editorial.json')
        if ident not in validar_catalogo(info):raise ValueError('O personagem não existe mais no cadastro.')
        usos=[r['caminho'] for r in participacoes(arvore,ident)]
        for _,cap in self.capitulos(arvore):
            arquivo=self.caminho(f'{slug}/{cap["arquivo"]}')
            if not arquivo.is_file():raise ValueError('Não foi possível conferir o texto: '+cap['arquivo'])
            if referencias_em_html(arquivo.read_text(encoding='utf-8'),ident):usos.append('Marcações no texto: '+cap['titulo'])
        pasta=self.caminho(f'{slug}/autoria')
        if pasta.exists():
            for arquivo in pasta.rglob('*.narrproj'):
                if not arquivo.resolve().is_relative_to(self.root):raise ValueError('Autoria fora do projeto.')
                data=json.loads(arquivo.read_text(encoding='utf-8'))
                if not isinstance(data,dict):raise ValueError('Não foi possível conferir a autoria: '+arquivo.name)
                if personagem_referenciado_na_autoria(data,ident):usos.append('Marcações na autoria: '+arquivo.name)
        return list(dict.fromkeys(usos))
    def ocorrencias_personagem(self,slug,ident):
        from identidade_semantica import ocorrencias,ocorrencias_html
        info,_=self.ler(f'{slug}/dados/info-obra.json');arvore,_=self.ler(f'{slug}/dados/editorial.json')
        if ident not in validar_catalogo(info):raise ValueError('Personagem não encontrado no cadastro.')
        resultado=[];capitulos={c['id']:c for _,c in self.capitulos(arvore)}
        for cap in capitulos.values():
            html=self.caminho(f'{slug}/{cap["arquivo"]}').read_text(encoding='utf-8')
            for ref in ocorrencias_html(html,ident):resultado.append({**ref,'capitulo':cap['id'],'titulo':cap['titulo'],'origem':'Capítulo aplicado'})
        pasta=self.caminho(f'{slug}/autoria')
        if pasta.exists():
            for arquivo in pasta.rglob('*.narrproj'):
                if not arquivo.resolve().is_relative_to(self.root):raise ValueError('Autoria fora do projeto.')
                data=json.loads(arquivo.read_text(encoding='utf-8'));capid=data.get('literature',{}).get('capitulo',arquivo.stem)
                for ref in ocorrencias(data,ident):resultado.append({**ref,'capitulo':capid if capid in capitulos else None,'titulo':capitulos[capid]['titulo'] if capid in capitulos else arquivo.name,'origem':'Autoria salva — '+arquivo.name})
        return resultado
    def excluir_personagem(self,slug,ident,revisao):
        path=f'{slug}/dados/info-obra.json';info,atual=self.ler(path)
        if atual!=revisao:raise ConflitoEdicao('O cadastro mudou. Reabra a exclusão antes de continuar.')
        usos=self.usos_personagem(slug,ident)
        if usos:raise ValueError('Remova ou substitua as participações e marcações antes de excluir: '+'; '.join(usos))
        info['personagens']=[p for p in info.get('personagens',[]) if p['id']!=ident]
        return self.salvar(path,info,revisao)
    def obras(self):return self.ler('obras.json')[0]['obras']
    def capitulos(self,arvore):
        indice={no.id:no for no in hier.nos(arvore)}
        return [(indice[no.pai].item if no.pai else None,no.item) for no in indice.values() if no.tipo=='capitulo']
    def organizar(self,slug,arvore,revisao):
        hier.validar(arvore)
        return self.salvar(f'{slug}/dados/editorial.json',arvore,revisao)
    def nova_obra(self,slug,titulo,autor):
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):raise ValueError('Use letras minúsculas, números e hífens no endereço.')
        if not titulo.strip() or not autor.strip():raise ValueError('Preencha título e autor.')
        registro,rev=self.ler('obras.json');dest=self.caminho(slug)
        if dest.exists() or dest.is_symlink() or slug in registro['obras']:raise ValueError('Esse endereço já existe.')
        modelo=Path(__file__).resolve().parent/'modelos/obra'
        try:
            (dest/'dados').mkdir(parents=True);(dest/'writed').mkdir()
            for nome in ('index-obra.html','leitor.html'):shutil.copy2(modelo/nome,dest/nome)
            info={'schema_version':2,'id_obra':str(uuid.uuid4()),'slug':slug,'titulo':titulo.strip(),'autor':autor.strip(),'idioma':'pt-BR','sinopse':'','estado_obra':'planejamento','estado_publicacao':'rascunho','ordem_catalogo':len(registro['obras'])+1,'formato':'publicacao_seriada','generos':[],'temas':[],'tags':[],'avisos_conteudo':[],'capa':{'src':'/assets/imagens/literature-mark.svg','alt':'Capa de '+titulo},'personagens':[],'lore':[]}
            self.salvar(f'{slug}/dados/info-obra.json',info,None)
            self.salvar(f'{slug}/dados/editorial.json',{'schema_version':2,'capitulos':[]},None)
            registro['obras'].append(slug);self.salvar('obras.json',registro,rev)
        except Exception:
            shutil.rmtree(dest);raise
        return slug
    def novo_capitulo(self,slug,titulo,arvore,rev,referencia=None,destino=None,posicao=None):
        if not titulo.strip():raise ValueError('Preencha o título.')
        hier.validar(arvore)
        if 'capitulos' not in arvore and destino is None:
            ref=hier.encontrar(arvore,referencia)
            destino=ref.pai if ref and ref.tipo=='capitulo' else next((no.id for no in hier.nos(arvore) if no.tipo=='arco'),None)
        lista=hier.lista_destino(arvore,'capitulo',destino)
        if posicao is None:posicao=len(lista)+1
        ident='cap-'+uuid.uuid4().hex
        cap={'id':ident,'titulo':titulo.strip(),'numero':'','ordem':max([c['ordem'] for c in lista],default=0)+1,'arquivo':f'writed/{ident}.html','estado_publicacao':'rascunho','publicado_em':None,'sinopse':'','avisos_conteudo':[],'cenas':[]}
        arquivo=f'{slug}/{cap["arquivo"]}'
        novo=hier.inserir(arvore,cap,'capitulo',destino,posicao)
        self.salvar(arquivo,'<p></p>\n',None)
        try:self.organizar(slug,novo,rev)
        except Exception:
            self.caminho(arquivo).unlink();raise
        arvore.clear();arvore.update(novo)
        return ident
    def exportar(self,destino):
        site=self.root/'site'
        if not site.is_dir():raise ValueError('Gere o site antes de empacotar.')
        destino=Path(destino).resolve()
        if destino.suffix.lower()!='.zip':raise ValueError('O pacote deve usar a extensão .zip.')
        if destino.is_relative_to(site):raise ValueError('Salve o pacote fora da pasta site.')
        with zipfile.ZipFile(destino,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(site.rglob('*')):
                if p.is_file():z.write(p,p.relative_to(site))
        return destino
    def importar_imagem(self,origem):
        origem=Path(origem)
        if origem.suffix.lower() not in {'.png','.jpg','.jpeg','.webp','.gif','.svg'}:raise ValueError('Escolha uma imagem PNG, JPG, WebP, GIF ou SVG.')
        nome=uuid.uuid4().hex[:12]+origem.suffix.lower()
        dest=self.caminho('assets/imagens/'+nome);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origem,dest)
        return '/assets/imagens/'+nome

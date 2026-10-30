"""Biblioteca local e operações reversíveis sobre pastas completas de obras."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid
import zipfile

class ObrasProjeto:
    def _pasta_obra(self, slug, registrada=True):
        if not isinstance(slug,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):
            raise ValueError('Endereço de obra inválido.')
        if registrada and slug not in self.obras():raise ValueError('Obra não cadastrada.')
        pasta=self.caminho(slug)
        if pasta!=self.root/slug or (self.root/slug).is_symlink():raise ValueError('A pasta da obra não pode ser um vínculo simbólico.')
        return pasta

    def biblioteca_obras(self):
        resultado=[]
        for slug in self.obras():
            self._pasta_obra(slug)
            info,rev=self.ler(f'{slug}/dados/info-obra.json')
            arvore,_=self.ler(f'{slug}/dados/editorial.json')
            caps=[c for _,c in self.capitulos(arvore)]
            resultado.append({'slug':slug,'info':info,'revisao':rev,'capitulos':len(caps),
                'publicados':sum(c.get('estado_publicacao')=='publicado' for c in caps),
                'personagens':len(info.get('personagens',[]))})
        return sorted(resultado,key=lambda x:(x['info'].get('ordem_catalogo',0),x['info']['titulo'].casefold(),x['slug']))

    def editar_obra(self,slug,alteracoes,revisao):
        self._pasta_obra(slug)
        permitidos={'titulo','autor','idioma','sinopse','estado_obra','estado_publicacao'}
        if set(alteracoes)-permitidos:raise ValueError('Essa operação não altera identidades ou endereços.')
        info,_=self.ler(f'{slug}/dados/info-obra.json');info.update(alteracoes)
        self.validar_ficha_obra(info)
        return self.salvar(f'{slug}/dados/info-obra.json',info,revisao)

    def validar_ficha_obra(self,info):
        if any(not isinstance(info.get(c),str) or not info[c].strip() for c in ('titulo','autor','idioma')):raise ValueError('Preencha título, autor e idioma.')
        if info.get('estado_publicacao') not in {'rascunho','publicado','arquivado'}:raise ValueError('Estado de publicação inválido.')
        if info.get('estado_obra') not in {'planejamento','em_andamento','pausada','concluida'}:raise ValueError('Andamento inválido.')

    def _assinatura_pasta(self,pasta):
        h=hashlib.sha256()
        if not pasta.is_dir():raise ValueError('Pasta da obra não encontrada.')
        for p in sorted(pasta.rglob('*')):
            if p.is_symlink():raise ValueError('A obra contém vínculos simbólicos. Resolva-os antes desta operação.')
            h.update(str(p.relative_to(pasta)).encode());h.update(b'\0')
            if p.is_file():h.update(hashlib.sha256(p.read_bytes()).digest())
        return h.hexdigest()

    def preparar_exclusao_obra(self,slug):
        pasta=self._pasta_obra(slug)
        _,registro_rev=self.ler('obras.json')
        info,_=self.ler(f'{slug}/dados/info-obra.json')
        return {'slug':slug,'titulo':info['titulo'],'id_obra':info['id_obra'],
                'registro_rev':registro_rev,'assinatura':self._assinatura_pasta(pasta)}

    def _lixeira_obras(self):
        pasta=self.caminho('.literature-lixeira')
        if pasta!=self.root/'.literature-lixeira':raise ValueError('Pasta de recuperação inválida.')
        pasta.mkdir(exist_ok=True)
        return pasta

    def excluir_obra(self,proposta):
        slug=proposta['slug'];pasta=self._pasta_obra(slug)
        registro,rev=self.ler('obras.json')
        if rev!=proposta['registro_rev'] or self._assinatura_pasta(pasta)!=proposta['assinatura']:
            raise ValueError('A obra ou o cadastro mudou. Reabra a revisão da exclusão.')
        token=uuid.uuid4().hex;dest=self._lixeira_obras()/token;dest.mkdir()
        manifesto={**proposta,'token':token,'versao':1,'excluida_em':datetime.now(timezone.utc).isoformat()}
        (dest/'manifesto.json').write_text(json.dumps(manifesto,ensure_ascii=False,indent=2),encoding='utf-8')
        try:
            shutil.move(str(pasta),str(dest/'obra'))
            registro['obras'].remove(slug)
            self.salvar('obras.json',registro,rev)
        except Exception:
            if (dest/'obra').exists():shutil.move(str(dest/'obra'),str(pasta))
            shutil.rmtree(dest)
            raise
        return token

    def obras_excluidas(self):
        base=self.root/'.literature-lixeira'
        if not base.exists():return []
        base=self._lixeira_obras();resultado=[]
        for p in sorted(base.iterdir()):
            if p.is_symlink():raise ValueError('Entrada inválida na recuperação de obras.')
            if (p/'manifesto.json').is_symlink():raise ValueError('Manifesto de recuperação inválido.')
            if p.is_dir() and (p/'manifesto.json').is_file():
                d=json.loads((p/'manifesto.json').read_text(encoding='utf-8'))
                if d.get('token')!=p.name:raise ValueError('Manifesto de recuperação inválido.')
                resultado.append(d)
        return sorted(resultado,key=lambda x:x.get('excluida_em',''),reverse=True)

    def restaurar_obra(self,token):
        if not isinstance(token,str) or not re.fullmatch(r'[a-f0-9]{32}',token):raise ValueError('Recuperação inválida.')
        base=self._lixeira_obras()/token
        if base.is_symlink() or (base/'manifesto.json').is_symlink():raise ValueError('Recuperação inválida.')
        manifesto=json.loads((base/'manifesto.json').read_text(encoding='utf-8'));slug=manifesto['slug']
        if manifesto.get('token')!=token:raise ValueError('Manifesto de recuperação inválido.')
        dest=self._pasta_obra(slug,False);registro,rev=self.ler('obras.json')
        if slug in registro['obras'] or dest.exists():raise ValueError('O endereço já está ocupado. A obra excluída continua preservada.')
        origem=base/'obra'
        if origem.is_symlink() or self._assinatura_pasta(origem)!=manifesto['assinatura']:raise ValueError('Os arquivos de recuperação mudaram. Confira-os antes de restaurar.')
        info=json.loads((origem/'dados/info-obra.json').read_text(encoding='utf-8'))
        if info.get('slug')!=slug or info.get('id_obra')!=manifesto['id_obra']:raise ValueError('Identidade de recuperação inconsistente.')
        if any(x['info']['id_obra']==info['id_obra'] for x in self.biblioteca_obras()):raise ValueError('Essa identidade de obra já está cadastrada.')
        # A restauração é editorial: não recoloca uma obra publicada no próximo site sem revisão.
        shutil.move(str(origem),str(dest))
        try:
            path=f'{slug}/dados/info-obra.json';info,info_rev=self.ler(path)
            original=(dest/'dados/info-obra.json').read_bytes()
            info['estado_publicacao']='rascunho';self.salvar(path,info,info_rev)
            registro['obras'].append(slug);self.salvar('obras.json',registro,rev)
        except Exception:
            if 'original' in locals():(dest/'dados/info-obra.json').write_bytes(original)
            shutil.move(str(dest),str(origem));raise
        shutil.rmtree(base)
        return slug

    def exportar_obra(self,slug,destino):
        pasta=self._pasta_obra(slug);self._assinatura_pasta(pasta)
        destino=Path(destino).resolve()
        if destino.suffix.lower()!='.zip' or destino.is_relative_to(self.root):raise ValueError('Salve o pacote .zip fora da pasta do projeto.')
        fd,tmp=tempfile.mkstemp(dir=destino.parent,suffix='.zip');os.close(fd)
        try:
            with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
                for p in sorted(pasta.rglob('*')):
                    if p.is_file():z.write(p,Path(slug)/p.relative_to(pasta))
                z.writestr('LEIA-ME.txt','Pacote de fontes da obra: inclui autoria local, textos e metadados.\nNão é um site independente. Recursos compartilhados em assets/ não estão incluídos.\n')
            os.replace(tmp,destino)
        finally:
            if Path(tmp).exists():Path(tmp).unlink()
        return destino

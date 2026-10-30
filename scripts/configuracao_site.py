"""Configuração pública do site: sem credenciais e independente de backend."""
import json
import re
from urllib.parse import urlsplit

PADRAO={'schema_version':1,'url_publica':'https://literatura.roger.cardoso.nom.br','disqus':{'ativado':False,'shortname':'','obras':True,'capitulos':True}}

def validar(config,cname=None):
    if not isinstance(config,dict) or config.get('schema_version')!=1:raise ValueError('Versão da configuração do site inválida.')
    url=config.get('url_publica','');partes=urlsplit(url)
    if partes.scheme!='https' or not partes.hostname or partes.username or partes.password or partes.port or partes.path not in ('','/') or partes.query or partes.fragment:raise ValueError('Use a origem HTTPS do site, sem caminhos, portas ou parâmetros.')
    if cname and partes.hostname!=cname.strip():raise ValueError('O endereço público precisa corresponder ao domínio do arquivo CNAME.')
    disqus=config.get('disqus')
    if not isinstance(disqus,dict) or any(type(disqus.get(k)) is not bool for k in ('ativado','obras','capitulos')):raise ValueError('Informe as opções de comentários como verdadeiro ou falso.')
    short=disqus.get('shortname')
    if not isinstance(short,str) or (short and not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?',short)):raise ValueError('Informe somente o shortname do Disqus, sem endereço ou espaços.')
    if disqus['ativado'] and not short:raise ValueError('Cadastre o site no Disqus e informe o shortname antes de ativar.')
    return {'schema_version':1,'url_publica':url.rstrip('/'),'disqus':{k:disqus[k] for k in ('ativado','shortname','obras','capitulos')}}

def carregar(root):
    arquivo=root/'configuracao-site.json'
    config=json.loads(arquivo.read_text(encoding='utf-8')) if arquivo.exists() else json.loads(json.dumps(PADRAO))
    return validar(config,(root/'CNAME').read_text(encoding='utf-8').strip())

def validar_opcao(obj,contexto):
    if obj.get('comentarios','herdar') not in {'herdar','ativado','desativado'}:raise ValueError(contexto+': opção de comentários inválida.')

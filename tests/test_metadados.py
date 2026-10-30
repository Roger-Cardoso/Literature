import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gerador',ROOT/'scripts/gerar_site.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
from fixture_projeto import preparar_fixture
class MetadadosTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'projeto'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('node_modules','.wrangler','.literature-lixeira','site','.git','.agents','.codex','.aws','__pycache__','.literature-backups','.unilit-build-*'))
        preparar_fixture(self.root)
        self.path=self.root/'obra-1/dados/editorial.json';self.tree=json.loads(self.path.read_text())
        # Obra fictícia fixa: a suíte não depende dos capítulos reais do autor.
        g.gravar(self.root/'obras.json',{'schema_version':2,'obras':['obra-1']})
        info={'schema_version':2,'id_obra':'fixture-obra','slug':'obra-1','titulo':'Obra de teste','autor':'Autoria fictícia','idioma':'pt-BR','sinopse':'Sinopse de teste.','estado_publicacao':'publicado','estado_obra':'em_andamento','ordem_catalogo':1,'capa':{'src':'/assets/imagens/literature-mark.svg','alt':'Capa de teste'},'personagens':[{'id':'fixture-ana','nome':'Ana'}],'lore':[]}
        g.gravar(self.root/'obra-1/dados/info-obra.json',info)
        caps=[{'id':f'fixture-cap-{i}','titulo':f'Capítulo {i}','ordem':i,'arquivo':f'writed/fixture-{i}.html','estado_publicacao':'publicado','publicado_em':'2020-01-01','cenas':[]} for i in (1,2)]
        self.tree={'schema_version':2,'sagas':[{'id':'fixture-saga','nome':'Saga','ordem':1,'volumes':[{'id':'fixture-volume','nome':'Volume','ordem':1,'arcos':[{'id':'fixture-arco','nome':'Arco','ordem':1,'capitulos':caps}]}]}]}
        self.save()
        for c in caps:(self.root/'obra-1'/c['arquivo']).write_text('<p>Texto fictício de teste.</p>',encoding='utf-8')
    def tearDown(self):self.tmp.cleanup()
    def cap(self):return self.tree['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'][0]
    def save(self):g.gravar(self.path,self.tree)
    def test_fontes_preservadas_e_saida_deterministica(self):
        antes={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*.json')}
        g.gerar(self.root);primeiro={p.relative_to(self.root/'site'):p.read_bytes() for p in (self.root/'site').rglob('*') if p.is_file()}
        g.gerar(self.root);segundo={p.relative_to(self.root/'site'):p.read_bytes() for p in (self.root/'site').rglob('*') if p.is_file()}
        self.assertEqual(primeiro,segundo)
        for p,b in antes.items():self.assertEqual((self.root/p).read_bytes(),b)
        self.assertFalse((self.root/'site/obra-2').exists());self.assertFalse((self.root/'home/dados').exists())
        self.assertFalse(list((self.root/'site').rglob('editorial.json')))
    def test_reordenar_nao_altera_identidade(self):
        lista=self.tree['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'];esperados=[c['id'] for c in sorted(lista,key=lambda x:x['ordem']) if c['estado_publicacao']=='publicado' and c['id']!=self.cap()['id']]+[self.cap()['id']]
        self.cap()['ordem']=max(c['ordem'] for c in lista)+1;self.save();result=g.preparar(self.root)
        caps=[c for s in result[0][2]['sagas'] for v in s['volumes'] for a in v['arcos'] for c in a['capitulos']]
        self.assertEqual([c['id'] for c in caps],esperados)
    def test_falha_preserva_ultima_saida(self):
        g.gerar(self.root);antes=(self.root/'site/catalogo.json').read_bytes()
        self.cap()['arquivo']='../../README.md';self.save()
        with self.assertRaises(g.ErroMetadados):g.gerar(self.root)
        self.assertEqual((self.root/'site/catalogo.json').read_bytes(),antes)
    def test_rejeita_id_duplicado(self):
        self.tree['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'][1]['id']=self.cap()['id'];self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_rejeita_vazio_publicado(self):
        (self.root/'obra-1'/self.cap()['arquivo']).write_text('  ')
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_rejeita_data_e_placeholder(self):
        self.cap()['publicado_em']='13 Jun 2026';self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
        self.cap()['publicado_em']='2026-06-13';self.cap()['sinopse']='Adicione a sinopse';self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_rascunho_nao_copiado_nem_contado(self):
        self.cap()['estado_publicacao']='rascunho';self.save();g.gerar(self.root)
        self.assertFalse((self.root/'site/obra-1'/self.cap()['arquivo']).exists())
        self.assertEqual(json.loads((self.root/'site/catalogo.json').read_text())[0]['total_capitulos'],1)
    def test_obra_simples_sem_agrupamentos_editoriais(self):
        caps=self.tree['sagas'][0]['volumes'][0]['arcos'][0]['capitulos']
        g.gravar(self.path,{'schema_version':2,'capitulos':caps})
        g.gerar(self.root)
        resultado=json.loads((self.root/'site/obra-1/dados/estrutura.json').read_text())
        self.assertEqual(resultado['total_capitulos'],2)
        self.assertEqual(resultado['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'][0]['id'],caps[0]['id'])
    def test_rejeita_verbete_inexistente_no_capitulo(self):
        self.cap()['verbetes_ids']=['nao-existe'];self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_rejeita_nota_sem_texto(self):
        self.cap()['notas']=[{'id':'nota-teste','titulo':'Nota'}];self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_rejeita_personagem_semantico_inexistente(self):
        p=self.root/'obra-1'/self.cap()['arquivo']
        p.write_text('<p data-locutor-id="ausente">Olá.</p>')
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_offline_sem_rascunhos_scripts_ou_imagens_externas(self):
        self.cap()['cenas']=[];self.save()
        p=self.root/'obra-1'/self.cap()['arquivo']
        p.write_text('<p>Texto publicado.</p><script>alert(1)</script><img src="https://example.org/imagem.png" alt="Ilustração">')
        g.gerar(self.root)
        html=(self.root/'site/obra-1/offline.html').read_text()
        self.assertIn('Texto publicado.',html)
        self.assertNotIn('<script',html)
        self.assertNotIn('alert(1)',html)
        self.assertNotIn('https://example.org',html)
        self.assertFalse((self.root/'site/obra-2/offline.html').exists())
    def test_guia_exige_ancora_real(self):
        self.cap()['cenas']=[{'id':'cena-1','visibilidade':'publica','titulo_cena':'Cena 1','relevancia':'essencial','ancora':'inexistente','avisos_conteudo':['Confinamento']}];self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_guia_preserva_avisos_e_resumo_editoriais(self):
        p=self.root/'obra-1'/self.cap()['arquivo'];p.write_text('<section id="chegada"><p>Texto.</p></section>')
        self.cap()['cenas']=[{'id':'cena-1','visibilidade':'publica','titulo_cena':'Cena 1','relevancia':'essencial','ancora':'chegada','avisos_conteudo':['Confinamento'],'resumo_alternativo':'Resumo editorial.'}];self.save();g.gerar(self.root)
        resultado=json.loads((self.root/'site/obra-1/dados/estrutura.json').read_text())
        cena=resultado['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'][0]['cenas'][0]
        self.assertEqual(cena['avisos_conteudo'],['Confinamento']);self.assertEqual(cena['resumo_alternativo'],'Resumo editorial.')
    def test_guia_rejeita_ordem_diferente_do_texto(self):
        p=self.root/'obra-1'/self.cap()['arquivo'];p.write_text('<section id="a">A</section><section id="b">B</section>')
        self.cap()['cenas']=[{'id':'cena-'+x,'visibilidade':'publica','titulo_cena':x,'relevancia':'opcional','ancora':x} for x in ('b','a')];self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_referencias_nativas_multiplas_e_aliases(self):
        p=self.root/'obra-1'/self.cap()['arquivo']
        p.write_text('<p data-speaker="fixture-ana nativo">Olá.</p><section data-pov-id="fixture-ana nativo">Cena.</section><script id="story-entities" type="application/json">[{"id":"nativo","name":"Rui"}]</script>')
        g.preparar(self.root)
        p.write_text('<p data-thinker="inexistente">Olá.</p>')
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_registro_nativo_invalido_nao_e_ignorado(self):
        p=self.root/'obra-1'/self.cap()['arquivo']
        p.write_text('<p>Texto.</p><script id="story-entities" type="application/json">{}</script>')
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_offline_reescreve_destinos_sem_colisao_entre_capitulos(self):
        caps=self.tree['sagas'][0]['volumes'][0]['arcos'][0]['capitulos']
        for c in caps:(self.root/'obra-1'/c['arquivo']).write_text('<p id="cena">Cena.</p><a href="#cena">Voltar</a>')
        g.gerar(self.root);html=(self.root/'site/obra-1/offline.html').read_text()
        for c in caps:
            self.assertIn('id="'+c['id']+'--cena"',html)
            self.assertIn('href="#'+c['id']+'--cena"',html)
        self.assertNotIn('href="#cena"',html)
    def test_assinatura_distingue_fontes_e_autoria(self):
        from estado_publicacao import assinatura_fontes,assinatura_gerada
        g.gerar(self.root);antes=assinatura_fontes(self.root)
        self.assertEqual(antes,assinatura_gerada(self.root))
        pasta=self.root/'obra-1/autoria';pasta.mkdir(exist_ok=True);(pasta/'teste.narrproj').write_text('{}')
        self.assertEqual(antes,assinatura_fontes(self.root))
        (self.root/'obra-1'/self.cap()['arquivo']).write_text('<p>Nova versão.</p>')
        self.assertNotEqual(assinatura_fontes(self.root),assinatura_gerada(self.root))
    def test_participacoes_de_cenas_validas_e_exclusao_de_privadas(self):
        self.cap()['personagens_ids']=['fixture-ana']
        self.cap()['cenas']=[{'id':'pub','visibilidade':'publica','titulo_cena':'Cena pública','relevancia':'opcional','ancora':'pub','personagens_ids':['fixture-ana']},{'id':'privada','visibilidade':'privada','titulo_cena':'Cena reservada','personagens_ids':['fixture-ana']}]
        (self.root/'obra-1'/self.cap()['arquivo']).write_text('<section id="pub"><p>Texto.</p></section>')
        self.save();g.gerar(self.root)
        resultado=json.loads((self.root/'site/obra-1/dados/estrutura.json').read_text());cap=resultado['sagas'][0]['volumes'][0]['arcos'][0]['capitulos'][0]
        self.assertEqual(cap['personagens_ids'],['fixture-ana']);self.assertEqual(cap['cenas'][0]['personagens_ids'],['fixture-ana'])
        self.assertEqual(len(cap['cenas']),1)
        self.cap()['cenas'][0]['personagens_ids']=['ausente'];self.save()
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_referencia_spoiler_invalida(self):
        p=self.root/'obra-1/dados/info-obra.json';i=json.loads(p.read_text());i['personagens'][0]['disponivel_apos_capitulo']='inexistente';g.gravar(p,i)
        with self.assertRaises(g.ErroMetadados):g.preparar(self.root)
    def test_cena_privada_nao_publicada(self):
        self.cap()['cenas']=[{'id':'cena-secreta','visibilidade':'privada','titulo_cena':'Segredo'}];self.save();g.gerar(self.root)
        self.assertNotIn('Segredo',(self.root/'site/obra-1/dados/estrutura.json').read_text())
if __name__=='__main__':unittest.main()

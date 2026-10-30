# Literature

Site estático para https://literatura.roger.cardoso.nom.br/home/.

## Gerar, verificar e visualizar

Requer Python 3.12 ou superior, sem dependências externas:

```sh
python3 scripts/gerar_site.py --validar
python3 -m unittest discover -s tests -v
python3 scripts/gerar_site.py
python3 -m http.server 8000 --directory site
```

Abra http://localhost:8000/home/. A demo é o site real gerado. Se houver uma obra publicada no catálogo, abra-a, leia um capítulo, use **Concluir capítulo** e volte ao índice para conferir o progresso. Também é possível marcar como não lido. Os links antigos `?id=1` e `?id=2` continuam aceitos.

Sirva e publique somente `site/`. A raiz contém fontes editoriais e rascunhos. `site/` é regenerável e não deve ser editada manualmente.

## Fontes e saída

- `obras.json`: lista explícita de pastas de obras; `home/` nunca é descoberta como obra.
- `obra-*/dados/info-obra.json`: apresentação e categorias editoriais.
- `obra-*/dados/editorial.json`: identidades, títulos, sequência e publicação dos capítulos.
- `obra-*/writed/`: textos de origem.
- `home/`, `css-global/`, `js-global/`: interface compartilhada.
- `assets/`: imagens e outros recursos públicos opcionais, copiados para a saída.
- `site/`: catálogo resumido, índice `busca.json`, dados públicos e capítulos publicados.
- `docs/metadados.md`: contrato de edição e exemplos.

Os três comandos geradores antigos encaminham ao mesmo gerador seguro. Os antigos arquivos de catálogo e estrutura da raiz foram substituídos pelas saídas em `site/`.

## GitHub Pages

O fluxo `.github/workflows/pages.yml` valida, testa, gera e publica apenas `site/` quando há envio para `main`, ou por execução manual. Se a branch principal tiver outro nome, ajuste o filtro do fluxo.

1. Envie o projeto ao repositório escolhido.
2. Em Settings → Pages, selecione **GitHub Actions** como fonte.
3. Configure o domínio `literatura.roger.cardoso.nom.br`.
4. No DNS, aponte o CNAME de `literatura` para `<usuario>.github.io`, com o proprietário real do repositório, sem `/home` nem nome do repositório.
5. Após validação do domínio e certificado, ative HTTPS.

O arquivo `CNAME` não configura DNS automaticamente. O repositório e o DNS ainda precisam ser configurados nas contas correspondentes.

Não envie textos confidenciais a um repositório público: excluir rascunhos da saída não os remove do histórico Git.

## Limites

A publicação considera somente as obras cadastradas e marcadas como públicas, com capítulos publicados válidos. Um cadastro vazio é suportado. Não há backend, votação compartilhada ou sincronização entre dispositivos. Progresso fica no navegador. O índice de busca inclui obras e capítulos; a busca da home filtra obras por título, sinopse, temas, gêneros e tags. Marcos de spoiler escondem cartões até a conclusão do capítulo indicado; os dados desses cartões continuam públicos no JSON.

## Identidade visual

Literature mantém a base escura e o acento verde do projeto, com títulos editoriais, componentes compartilhados e um leitor dedicado. Os estilos estão em `css-global/global.css`, `obra.css` e `leitor.css`. Marca, favicon e capa gráfica da primeira obra são SVGs locais em `assets/imagens/`. A capa é uma proposta visual substituível pelo campo `capa.src`, sem alterar o leitor.

Os layouts contemplam telas pequenas, navegação por teclado e preferência por movimento reduzido. As fontes usam alternativas locais do sistema, sem downloads de serviços externos.

## Demo: leitor confortável

Gere o site e abra um capítulo publicado pela página da respectiva obra na prévia local.

1. Abra **Sumário** no cabeçalho e busque um título ou agrupamento. O capítulo atual e os concluídos têm indicações separadas.
2. Abra **Aa**. Experimente sépia, contraste e os ajustes de conforto. A fonte pode chegar a 32 px também no celular. Use **Restaurar preferências** para voltar ao padrão.
3. Role parte do capítulo e recarregue. A retomada tenta reencontrar o parágrafo, com percentual como alternativa. Na página da obra aparece **Continuar leitura**.
4. Ao final do texto, confira os títulos anterior/próximo. A conclusão continua sendo uma escolha explícita.
5. Ative **Modo foco** e use **Sair do foco** para retornar. `Esc` fecha painéis; `Ctrl/Cmd+K` abre a busca do sumário.

A posição e as preferências ficam neste navegador e nesta origem (domínio). Alterações grandes no texto podem tornar a retomada aproximada. Não há sincronização entre dispositivos.

## Demo: leitura contextual

Após gerar, abra `/home/demo-contexto.html`. Consulte “universo”, simule a conclusão para disponibilizar “revelação” e abra as notas. É uma demonstração identificada com conteúdo fictício, sem alterações no manuscrito. O leitor real aceita as mesmas marcações e os campos documentados em `docs/metadados.md`.

## Demo: leitura especializada

Abra `/home/demo-especializada.html` para testar as etiquetas de diálogo/pensamento e a mudança de POV com dados fictícios. Abra os **Auxílios de leitura**, ative as opções e role a área de demonstração.

Na obra publicada, **Baixar leitura offline** entrega `offline.html`, que pode ser aberto diretamente sem servidor. É uma edição de leitura linear; não replica os recursos interativos ou o progresso do site. O leitor também possui estilo de impressão limpo, acessível pelo comando normal do navegador.

## Demo: guia de cenas

Abra `/home/demo-guia-cenas.html`. Expanda o guia, consulte relevância e avisos, abra os detalhes opcionais e use “Pular para a próxima cena”. O texto fictício permite demonstrar o comportamento sem classificar a narrativa existente nem alterar o progresso das obras. Cenas reais devem ser cadastradas editorialmente e ter âncoras no texto, conforme `docs/metadados.md`.

### Conferência do Guia de cenas

A demo foi conferida no navegador em tela ampla e em largura próxima de 390 px. O salto entre cenas transfere o foco ao trecho e preserva o estado não concluído. No leitor, o cabeçalho oferece retorno ao guia quando existem cenas cadastradas. Ao abrir um link para uma cena, o texto aguarda o posicionamento inicial; se a âncora não existir, o leitor abre o guia com um aviso.

## Gerenciamento visual — Literature Studio

Execute `python3 gerenciador.py` na raiz. A janela permite editar metadados, texto HTML, cenas, notas, personagens, verbetes e capas; criar obras/capítulos rascunhos; validar e gerar; abrir prévia local e preparar um ZIP público. Backups e detecção de edição concorrente protegem os arquivos de origem. Não realiza envios ao GitHub.

Roteiro e limites em [docs/gerenciador-visual.md](docs/gerenciador-visual.md).

### Editor semântico e estilo do Studio

O botão **Editor semântico** integra o editor e o schema fornecidos na mesma janela do Studio. Selecione um capítulo para trabalhar com um projeto de autoria vinculado. Importação das estruturas HTML suportadas, salvamento `.narrproj` e aplicação ao HTML são ações distintas; a aplicação exige comparação e preservação das âncoras do guia. O Studio adota o estilo claro/violeta do editor. Fluxo e limites estão em `docs/gerenciador-visual.md`.

### Sessão unificada

Gestão, texto semântico, revisão, recursos compartilhados e prévia textual ficam na mesma janela. Os personagens/verbetes da obra alimentam a autoria; a autoria pode propor recursos e cenas para a gestão mediante revisão. A prévia de CSS e interações do site continua disponível no navegador. Teste gráfico isolado: `python3 tests/verificar_studio_grafico.py`.

### Conciliação e roda do mouse

Capítulos sem autoria salva abrem com seu HTML atual importado, preservando cenas e estruturas suportadas. Abrir autoria externa mantém o capítulo ativo como destino. Revisões antigas não bloqueiam para sempre a aplicação, e mudanças posteriores à comparação continuam protegidas. O Studio roteia a roda entre textos, formulários e painéis; Shift+roda permite deslocamento horizontal. Teste gráfico de rolagem: `python3 tests/verificar_rolagem_grafica.py`.

## Integração e validação — atualização de 30/10/2026

O Studio distingue autoria, aplicação ao capítulo, geração e validação em uma faixa de estado. O editor é um componente `Frame` explícito; as cópias de origem permanecem preservadas. A importação mantém ligações de glossário e estruturas inline suportadas, relata marcações sem reconstrução e usa o mesmo contrato de referências da publicação.

Os testes de metadados usam uma obra fictícia, independente do crescimento da biblioteca real. As verificações adicionais `node tests/test_semantica.cjs` e `node tests/test_obra.cjs` cobrem os auxílios e a apresentação literal dos metadados. A edição offline preserva âncoras com prefixos por capítulo. O site gerado inclui `geracao.json`, usado para reconhecer fontes desatualizadas no Studio.

## Organização dos capítulos

O Studio oferece árvore hierárquica de sagas, volumes, arcos e capítulos, com posições calculadas, busca, filtro de publicação e agrupamentos vazios selecionáveis. **Organizar capítulos** permite inserir e mover itens por destino/posição, criar agrupamentos e converter obras simples sem renomear textos ou identidades. O gerenciador e a publicação compartilham a ordem editorial. Veja [o guia de organização](docs/organizacao-capitulos.md).

## Personagens e participações

A entrada Personagens da árvore abre uma biblioteca pesquisável de CRUD, sem personagens individuais na árvore. Um clique na biblioteca abre a ficha de metadados, com imagem, marco de disponibilidade e consulta de participações. A exclusão revisada cria backup e bloqueia personagens em uso. Capítulos e cenas mantêm seletores de participações por identidade. O editor semântico pode vincular personagens importados aos existentes na obra, preservando texto e histórico, e oferecer participações marcadas para revisão. Veja [o guia de personagens e participações](docs/personagens-participacoes.md).

## Identidades semânticas

Personagens vinculados usam o cadastro da obra e bases persistentes para reconhecer conflitos de nome, tipo e apelidos. Importações sem origem confirmada não são ligadas por coincidência de ID. A gestão integrada oferece entidades locais, propostas individuais, ocorrências por versão e nomes contextuais no leitor. Veja [o guia de identidades](docs/identidades-semanticas.md).

## Gerenciamento de obras

O botão **Obras** do Studio abre uma biblioteca com busca e filtro, metadados, criação, arquivamento, exportação individual de fontes e exclusão com restauração local. Os capítulos, personagens e autorias acompanham a obra. Veja o [guia de gerenciamento de obras](docs/gerenciamento-obras.md).

## Comentários e publicação

O botão **Site e comentários** configura a integração opcional com o Disqus, carregada por clique e vinculada aos IDs permanentes. É necessário cadastrar o fórum e informar seu shortname; a integração começa desativada. Veja [publicação e Disqus](docs/publicacao-disqus.md) para domínio, DNS, GitHub Pages e configuração do serviço.

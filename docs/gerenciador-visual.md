# Literature Studio — gerenciador visual local

## Abrir

```sh
python3 gerenciador.py
```

O comando pode ser chamado de qualquer pasta usando o caminho absoluto do script. Requer Python 3.12 ou superior, Tkinter e sessão gráfica. Não exige bibliotecas Python externas. No Linux, se faltar Tkinter, instale o pacote correspondente de sua distribuição (em sistemas Debian/Ubuntu, normalmente `python3-tk`).

## Primeiro roteiro

1. Selecione a obra na árvore à esquerda. Edite título, sinopse, categorias, estado e periodicidade. Listas são um item por linha.
2. Selecione **Capa**, importe uma imagem local e salve. A imagem é copiada para `assets/imagens/`; o original não é modificado.
3. Expanda **Capítulos**. Edite título, ordem, publicação e data. Selecione **Texto HTML** para editar o manuscrito. O editor é de código HTML, não um editor de texto formatado.
4. Selecione uma cena para revisar relevância, avisos, tratamento, consequência de pular e resumo. A relevância e a avaliação de sensibilidade permanecem decisões suas.
5. Clique **Salvar** ou use Ctrl+S, depois **Validar**. Os problemas aparecem na janela; salvar não equivale a aprovar a publicação.
6. Clique **Gerar site** e depois **Prévia**. A prévia abre a área de leitura interna; o botão de navegador inicia uma porta local livre e serve somente `site/`. Ela apresenta a última geração, não alterações ainda não geradas.
7. Use **Pacote de publicação** para gerar novamente e salvar um ZIP somente dos arquivos públicos. Para enviar a versão pública, use **Publicar no GitHub**. A configuração de DNS é feita no provedor do domínio.

## Obras, capítulos e recursos

**Nova obra** cria uma obra rascunho com estrutura simples e páginas baseadas no modelo atual da primeira obra. **Novo capítulo** cria um rascunho com identidade permanente e arquivo HTML vazio. Em obras hierárquicas, usa o mesmo arco do capítulo selecionado ou o primeiro arco disponível. Preencha o texto antes de publicar.

**Novo recurso** aceita personagem, verbete, cena ou nota. Para criar cena/nota, selecione primeiro o capítulo. Cenas exigem uma âncora no HTML. A validação verifica se ela existe, é única e segue a ordem do texto. Recursos incompletos podem ser salvos para edição, mas a geração rejeita inconsistências.

**Estrutura avançada** edita o JSON completo dos agrupamentos, permitindo nomes e reorganização entre saga, volume e arco. Preserve IDs e referências. Esta área exige conhecimento da estrutura e cria backup ao salvar.

Publicar um capítulo exige texto não vazio, data válida não futura e estado `publicado`. A obra também precisa estar publicada para aparecer. Não há agendamento automático ou envio remoto. A validação pode apontar outros campos inválidos em todo o projeto.

## Preservação

As gravações usam substituição de arquivo e preservam uma cópia anterior em `.literature-backups/`. O botão **Backups** permite visualizar e restaurar uma cópia. Restaurar também cria backup do arquivo substituído. Backups são locais, excluídos do pacote e ignorados pelo Git; mantenha uma cópia externa para proteção contra perda do computador.

Se um arquivo mudar fora da ferramenta depois de ser aberto, salvar é bloqueado. Recarregue e reconcilie suas mudanças. A ferramenta pergunta sobre alterações pendentes ao mudar de item ou sair. Operações de validação/geração rodam sem bloquear a janela e impedem novas gravações pela interface durante sua execução.

Não há exclusão definitiva de obras ou capítulos pela interface. Use estado rascunho ou arquivado para retirá-los da publicação. O arquivo público anterior permanece até uma geração bem-sucedida.

## Arquivos da ferramenta

- `gerenciador.py`: entrada principal.
- `scripts/gerenciador_visual.py`: janela e formulários.
- `scripts/gestao_projeto.py`: criação, gravação, backups e pacote público.
- `scripts/gerar_site.py`: processo de validação e geração já utilizado no projeto.

## Limites

A gestão é local e de um projeto. A prévia no navegador, quando usada, precisa ficar com o gerenciador aberto; ao fechar, o servidor é encerrado. O editor HTML não oferece edição visual do manuscrito, e o editor avançado de estrutura é JSON. A ferramenta não revisa conteúdo sensível, inventa sinopses, detecta automaticamente cenas ou infere locutores. Marcadores de spoiler, IDs de personagens e verbetes devem respeitar o contrato em `docs/metadados.md`.

## Aplicação unificada: gestão e autoria na mesma janela

O Studio contém uma única janela principal, com a árvore do projeto à esquerda e áreas de trabalho à direita:

- **Gestão e metadados:** obra, capítulo, capa, cenas, avisos, notas e recursos.
- **Texto e semântica:** o editor fornecido incorporado como componente, com seus menus, ferramentas e painéis internos.
- **Prévia da publicação:** leitura textual da última geração dentro do Studio.

Selecionar um capítulo e abrir **Editor semântico** usa a área interna, sem iniciar outro processo ou outra aplicação. A troca de capítulos protege a autoria não salva. O botão Salvar e Ctrl+S atendem à área ativa. Backups, estrutura avançada, revisão do HTML e comparação de recursos usam painéis internos. Seletores de arquivos e confirmações do sistema continuam sendo diálogos normais do aplicativo.

### Como as capacidades se alimentam

Os personagens e verbetes cadastrados na obra ficam disponíveis na autoria semântica. Identidades existentes no editor não são sobrescritas silenciosamente. **Compartilhar recursos com a obra** apresenta uma comparação para adicionar personagens, atualizar nomes por identidade e compartilhar termos/definições do glossário. A aplicação é explícita e mantém campos editoriais existentes. Entidades de outros tipos permanecem na autoria, sem serem transformadas automaticamente em personagens.

As seções explicitamente marcadas como cena no editor entram na proposta de atualização do Guia de cenas ao aplicar o capítulo. As entradas existentes preservam seus avisos, relevância e resumos. Novas entradas começam com relevância e conteúdo ainda não avaliados. A revisão apresenta HTML e alterações do guia. Âncoras de cenas existentes não podem desaparecer silenciosamente.

Após aplicar o capítulo ou os recursos, a árvore e os formulários são atualizados na mesma sessão. Não é necessário reabrir o gerenciador. A publicação continua exigindo validação e geração. Se houver autoria ativa diferente do HTML, Gerar abre a revisão e aguarda sua aplicação antes de prosseguir.

### Fluxo de autoria

1. Selecione o capítulo ou seu Texto HTML e abra **Editor semântico**.
2. Se existir, o `.narrproj` vinculado é carregado. Caso contrário, o HTML atual é convertido para autoria, mantendo as cenas e marcações suportadas, sem gravar no manuscrito.
3. **Reabrir HTML do capítulo** recarrega o texto atual mediante confirmação. O importador preserva cenas/âncoras, seções principais, títulos, negrito/itálico/sublinhado, listas, separadores, funções semânticas suportadas, recapitulação, prévia e registros nativos de entidades/glossário. Elementos não reconstruídos são listados na revisão. Não é um importador universal de HTML; compare o resultado antes de aplicar.
4. Edite texto, formatação, entidades, seções/POV, listas, elementos inline, recapitulação, prévia e glossário.
5. **Salvar** preserva a autoria `.narrproj` com backup. **Revisar e aplicar** atualiza o HTML e a proposta de cenas depois da sua revisão. Autorias antigas recuperam automaticamente as cenas cujo texto corresponde de forma exata e única ao HTML. Se isso não for possível, um painel permite associar a seleção de texto à cena existente, sem digitar seus IDs nem descartar seus avisos.
6. Revise campos editoriais na área de gestão e gere o site. A prévia interna apresenta o texto publicado na última geração; **Conferir site no navegador** permanece disponível para CSS, responsividade e interações reais.

### Fronteiras que continuam explícitas

A importação preserva o conjunto de estruturas suportadas, sem prometer fidelidade universal a HTML externo. O `.narrproj` conserva a autoria semântica; o HTML é o conteúdo aplicado à publicação. Alterações anteriores do HTML aparecem na comparação com a versão atual; alterações feitas depois de abrir a comparação bloqueiam a gravação. Cenas sem correspondência precisam ser conciliadas pelo painel de seleção.

A prévia interna é uma visualização de leitura em Tkinter, não um navegador HTML/CSS completo. Nenhuma dependência externa foi adicionada para simular um motor de navegador. O site real pode ser conferido no navegador pelo botão correspondente.

O leitor reconhece os registros JSON nativos de entidades/glossário e marcações de locutor, pensamento e POV. Scripts executáveis são removidos da aplicação. As definições e entidades nativas não recebem marcos de spoiler inferidos: a publicação deve ser revisada editorialmente.

### Origem e manutenção

Os arquivos originais fornecidos fora do Literature não foram modificados. As cópias preservadas ficam em `scripts/editor_semantico/`, com hashes em `proveniencia.json`. `scripts/editor_componente.py` adapta o editor para componente Tk sem alterar essas cópias. `scripts/integracao_semantica.py` concentra autoria, revisão e compartilhamento; `scripts/gerenciador_visual.py` coordena a sessão única.

### Verificação gráfica isolada

Em uma sessão de desktop, execute `python3 tests/verificar_studio_grafico.py`. O teste cria uma cópia temporária e verifica autoria incorporada, revisão/aplicação com backup, preservação do guia e prévia interna. Não salva nos manuscritos reais.

## Correções de conciliação e rolagem

Abrir um `.narrproj` externo enquanto um capítulo está ativo mantém esse capítulo como destino. O arquivo externo permanece intacto; o salvamento é uma cópia de autoria vinculada dentro do Literature. O vínculo não fica permanentemente bloqueado por um hash antigo: a revisão compara o HTML atual e captura a versão que poderá ser aplicada.

A barra de ações se reorganiza em linhas, e Revisar e aplicar permanece visível no editor estreito. A roda do mouse é gerida uma única vez por sessão: primeiro rola o texto/lista sob o mouse; no limite, pode alcançar o contêiner ancestral. Inclui formulários, painéis internos, árvore, editor, barra lateral, comparações somente leitura e prévia. Shift+roda move horizontalmente onde há conteúdo largo. Campos de seleção não trocam de valor ao tentar rolar o formulário. Os editores de texto e comparações contam com barras de rolagem explícitas.

Teste de rolagem em sessão gráfica: `python3 tests/verificar_rolagem_grafica.py`. O teste gera eventos de roda sobre os widgets e verifica deslocamentos reais, incluindo propagação entre áreas aninhadas e comparação horizontal. Não grava conteúdo das obras.

## Estados de autoria, capítulo e publicação

A faixa de estado mostra quatro etapas separadas: autoria salva ou com alterações pendentes, capítulo atualizado ou aguardando aplicação, site atualizado ou desatualizado e validação das fontes atuais. As informações se atualizam periodicamente na mesma janela. Salvar um `.narrproj` não significa aplicar seu conteúdo ao capítulo; aplicar ao capítulo não significa gerar a publicação.

A geração registra uma assinatura das fontes em `site/geracao.json`. Uma mudança nas fontes editoriais, páginas, recursos ou regras de geração torna a publicação local desatualizada. Alterações somente nos arquivos de autoria não alteram essa assinatura, mas continuam aparecendo como aplicação pendente quando o HTML exportado difere do capítulo. Fontes alteradas durante uma geração interrompem a substituição da saída anterior.

O componente do editor agora tem inicialização explícita como `Frame`, reutilizando métodos do editor original, sem executar uma versão do código criada por substituições de texto. `abrir_autoria` e `exportar_capitulo` são os pontos de entrada usados pela integração. As cópias de origem continuam preservadas.

O importador mantém estruturas inline suportadas e ligações explícitas de glossário, além das estruturas narrativas. A revisão apresenta contagens e avisos de marcações sem reconstrução. A validação de referências é compartilhada entre a aplicação ao capítulo e a geração pública. Se os recursos da obra mudarem durante a comparação, é necessário abrir uma nova revisão antes de aplicar.

## Organização hierárquica

O botão **Organizar capítulos** oferece movimentação por destino e posição, criação de agrupamentos e inserção antes/depois. A árvore mostra sagas, volumes e arcos, incluindo os vazios, em ordem editorial. A seleção é mantida por ID durante reorganizações. Busca, filtros, expansão do caminho atual e carregamento dos filhos do capítulo sob demanda auxiliam obras maiores. Consulte [Organização dos capítulos](organizacao-capitulos.md) para o fluxo completo e as regras de preservação.

## Personagens e participações

**Personagens** na árvore abre a biblioteca de CRUD em uma página própria da mesma janela. Os personagens individuais não aparecem na árvore principal. Um clique na biblioteca abre a ficha de metadados, que mantém o acesso às participações. A exclusão tem revisão, backup e proteção de referências. Capítulos e cenas têm seletores de personagens por nome/apelido, gravando IDs permanentes. O editor semântico oferece vínculo de entidades importadas ao cadastro existente e revisão das participações a partir de marcações explícitas. Consulte [Personagens e participações](personagens-participacoes.md).

## Identidade compartilhada

O cadastro da obra é a autoridade para personagens usados nas marcações. **Entidades e identidades** reúne entidades vinculadas, locais, conflitos e propostas individuais. Bases e origens são persistidas na autoria. A ficha permite consultar ocorrências por versão e o leitor admite nomes contextuais para preservar revelações. Veja [Identidades semânticas](identidades-semanticas.md).

## Biblioteca de obras

Use **Obras** para gerenciar a coleção na mesma janela: criar, abrir a ficha, buscar, filtrar, arquivar, exportar fontes e excluir com recuperação. A restauração conserva as identidades e retorna a obra a rascunho. Leia o [guia completo](gerenciamento-obras.md), incluindo a diferença entre fontes privadas e pacote público.

## Atualização do repositório

A aba **Publicar no GitHub** prepara e revisa os arquivos públicos antes do envio, acompanha o Pages e pode sincronizar os comentários. A publicação utiliza a pasta gerenciada `publicado/`; fontes privadas e credenciais ficam locais. Consulte [o fluxo completo](publicar-pelo-studio.md).

### Reações dos leitores

Em **Site e comentários → Gerenciar reações**, consulte Gostei, Não gostei e o total de votos de cada obra/capítulo, busque títulos, pause ou retome as reações e exporte os totais. Use a mesma credencial privada da moderação. A ativação global e os padrões ficam em Site e comentários; a ficha de cada obra e capítulo oferece o campo Reações. Veja [o guia de reações](reacoes.md).

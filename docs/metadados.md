# Contrato de metadados — versão 2

O validador executável é `scripts/gerar_site.py`. Ele valida todas as obras cadastradas antes de substituir a saída, preserva a saída anterior em caso de erro de validação e nunca grava nas fontes editoriais.

## Regras de autoria

`schema_version` deve ser 2. Identidades são textos únicos em todo o cadastro e não devem mudar ao renomear/reordenar itens. `slug` corresponde à pasta da obra nesta versão. Alterar endereço exige planejar redirecionamentos; não há renomeação automática.

Edite títulos, sinopses, categorias, ordem e datas nas fontes. Palavras, totais, catálogo e índice de busca são derivados, não campos editáveis. A contagem inclui todo texto visível do HTML (inclusive títulos, notas e recapitulação), excluindo tags, scripts e estilos.

A ordem é um inteiro único entre irmãos. Obras usam `ordem_catalogo`, com identidade como desempate. Números de capítulos são rótulos opcionais e não determinam identidade.

## Obra

Campos essenciais: `id_obra`, `slug`, `titulo`, `autor`, `idioma`, `schema_version`, `estado_obra`, `estado_publicacao`, `capa` e `sinopse`.

- `estado_obra`: `planejamento`, `em_andamento`, `pausada`, `concluida`.
- `estado_publicacao`: `rascunho`, `publicado`, `arquivado`.
- `capa`: objeto com `src` e `alt`. Use `/assets/imagens/...` para recursos locais compartilhados; arquivos dessa pasta são públicos.
- `formato`: texto editorial; `generos`, `temas`, `tags`, `avisos_conteudo`: listas de textos.
- `publico_alvo`: opcional. `classificacao_indicativa`: indicação editorial opcional, não certificação oficial.
- `periodicidade_texto`: opcional, mensagem para leitores, sem agendamento automático.

Uma obra pública precisa de pelo menos um capítulo publicado. Arquivado não é incluído no site nesta versão. Textos de preenchimento conhecidos são rejeitados em metadados públicos.

## Capítulos e agrupamentos

`editorial.json` aceita a árvore `sagas → volumes → arcos → capitulos`. Agrupamentos têm `id`, `nome`, `ordem`; `slug` e sinopse são opcionais. Agrupamentos vazios são omitidos da saída.

Para obras simples, use uma lista `capitulos` na raiz em vez de `sagas`. O gerador adapta a lista ao leitor com agrupamentos internos; não é necessário criar níveis editoriais artificiais.

Exemplo de capítulo (adapte ID e arquivo ao cadastrar):

```json
{
  "id": "minha-obra-cap-003",
  "titulo": "Uma nova chegada",
  "numero": "3",
  "ordem": 3,
  "arquivo": "writed/capitulo-03.html",
  "estado_publicacao": "rascunho",
  "publicado_em": null,
  "sinopse": "",
  "avisos_conteudo": [],
  "personagens_ids": []
}
```

O arquivo deve existir dentro da obra, inclusive para rascunhos. Para publicar, preencha `publicado_em` em `YYYY-MM-DD`, mude o estado e gere novamente. Capítulos públicos vazios ou com data futura são rejeitados. Não há publicação automática por data. `atualizado_em` é opcional e não pode preceder a publicação. A primeira data permanece sob controle editorial.

`id_legado` é reservado aos números dos links/progresso anteriores. Não reutilize nem regenere esses números. Capítulos novos não precisam dele. O leitor converte o histórico antigo para IDs estáveis, sem apagar a chave legada na migração. Ao desmarcar uma conclusão, o histórico legado já convertido é limpo para que não reative o capítulo.

## Personagens, universo e spoilers

Personagens: `id`, `nome`, `descricao_curta`, `imagem`, `imagem_alt`, `aliases` (lista opcional).

Verbetes em `lore`: `id`, `titulo`, `descricao`, `categoria`.

`disponivel_apos_capitulo` pode referenciar o ID de um capítulo publicado. A interface só apresenta o cartão após a conclusão desse capítulo. Isso evita spoilers casuais; não oferece confidencialidade, pois o JSON é público.

`personagens_ids` nos capítulos só aceita identidades cadastradas na obra.

## Cenas

`cenas` é opcional. Cada cena tem `id` e `visibilidade` explícita (`publica` ou `privada`). Cenas privadas são excluídas dos dados gerados. Cenas públicas precisam de `titulo_cena`, `descricao` e `relevancia` (`alta`, `media`, `baixa`). Aqui relevância significa importância editorial da cena para o desenvolvimento do capítulo, atribuída pelo autor; o gerador não a infere.

As cenas públicas ficam numa seção de bastidores que a pessoa abre voluntariamente. Não inclua planejamento confidencial em repositório público.

## Publicação segura

Somente obras e capítulos `publicado` entram em `site/`; rascunhos não entram no catálogo, na navegação, no índice de busca nem na cópia de textos. Não coloque rascunhos em `assets/`, `home/`, `css-global/` ou `js-global/`, pois essas pastas são públicas.

Não edite as saídas para ajustar dados: serão substituídas na próxima geração. Erros devem ser corrigidos na fonte indicada. Não há likes/dislikes no contrato; progresso pertence ao navegador de cada leitor.

## Leitura contextual

Um capítulo pode indicar `verbetes_ids` (lista de IDs de `lore`) para apresentar referências numa seção recolhível. Para um termo diretamente no HTML, use `<span data-verbete-id="ID-DO-VERBETE">termo</span>`. A marcação só vira botão se o verbete estiver disponível; definições são textos editoriais, sem interpretação automática.

Notas opcionais usam `notas: [{"id":"nota-permanente","titulo":"Nota do autor","texto":"Conteúdo da nota"}]`. Cada nota pode ter `disponivel_apos_capitulo`, com a mesma regra de conclusão explícita dos verbetes. Notas vazias e referências inválidas são rejeitadas. `avisos_conteudo` aparece no mesmo painel.

A apresentação respeita marcos no navegador, mas os metadados públicos continuam acessíveis no JSON. Esta função evita spoilers casuais, não oferece confidencialidade. Recapitulações e prévias existentes em HTML continuam recolhíveis; seu texto não é gerado automaticamente.

A demo funcional fica em `/home/demo-contexto.html`, usa dados fictícios e armazenamento com identidade própria, separado das obras. O link “Ver no universo” do componente real abre o verbete na página da obra; na demo, essa ação é ocultada porque não há obra publicada correspondente.

## Leitura especializada

No HTML autoral, use `data-locutor-id="ID-PERSONAGEM"` em um diálogo, `data-pensador-id="ID-PERSONAGEM"` em um pensamento e `data-pov-id="ID-PERSONAGEM"` em uma seção. As identidades precisam existir em `personagens`. A geração rejeita referências inexistentes. Não há detecção automática de locutor ou POV.

Os auxílios ficam desativados por padrão. No leitor, o botão fixo “Auxílios” abre suas opções no início do painel de leitura, inclusive no modo foco. Quando não há marcações disponíveis, os controles correspondentes ficam desabilitados com uma explicação. Personagens ainda bloqueados pelo marco de spoiler não recebem etiquetas. O indicador de POV acompanha a última seção marcada que passou pelo início da área de leitura. As configurações ficam no navegador.

Cada obra publicada recebe `offline.html`, uma edição linear autocontida com sumário e somente capítulos publicados. Imagens locais dentro do projeto são incorporadas; imagens externas são omitidas. Scripts e elementos de incorporação são removidos. Não acompanha notas editoriais, glossário interativo, progresso ou preferências do leitor. Os blocos recolhíveis existentes no texto continuam manuais. A exportação não é EPUB nem um backup editorial.

O CSS de impressão do leitor remove controles e evita o recorte causado pela área de rolagem. Use a impressão do navegador para escolher impressora ou salvar em PDF. Não há bloqueio de impressão.

## Guia de cenas: orientação de leitura e conteúdo sensível

Substitui a apresentação de “Estrutura”. Sua finalidade é permitir decidir entre ler, pular uma cena ou pular o capítulo. Relevância e sensibilidade são independentes e atribuídas pelo autor. Avisos ficam disponíveis antes da leitura, sem exigir conclusão. Descrições, consequências e resumos ficam em detalhes opcionais sinalizados com spoilers.

Uma cena pública deve ter `id` permanente, `titulo_cena` neutro, `visibilidade: "publica"`, `ancora` e `relevancia`. A âncora corresponde a um `id` único no HTML do capítulo, como `<section id="cena-chegada">`. As cenas seguem a ordem do texto e não podem compartilhar âncoras. `fim-do-capitulo` é reservado ao leitor.

Valores de relevância: `essencial` (para acompanhar a trama), `complementar` e `opcional` (para a continuidade). Os antigos valores `alta`, `media` e `baixa` continuam aceitos como equivalentes. Isso não determina valor artístico.

Campos opcionais: `avisos_conteudo` (lista específica, por exemplo “Presença de aranhas”), `tratamento` (texto sobre como o conteúdo aparece), `consequencia_pular`, `resumo_alternativo` e `descricao`. Nenhum deles é inferido. Uma lista vazia aparece como “Sem avisos cadastrados”, sem prometer ausência de conteúdo sensível.

O guia na página da obra abre o leitor na cena escolhida; no leitor, salta para a cena seguinte ou fim do capítulo. Há acesso ao capítulo seguinte quando publicado. A navegação não marca conclusão, e é possível voltar pelo guia. O leitor não impede a pessoa de concluir manualmente depois de pular. A edição offline linear ainda não inclui este guia interativo.

### Cadastro inicial das obras existentes

O primeiro capítulo da Obra 1 tem três divisões `.scene` no HTML: elas receberam âncoras permanentes e entradas correspondentes no guia. O segundo capítulo não possui divisões de cena e recebe apenas um trecho integral de navegação, identificado explicitamente como capítulo completo, sem inferir cortes narrativos.

`relevancia: "nao_avaliada"` comunica uma avaliação pendente. `avaliacao_conteudo` aceita `pendente` (padrão) ou `revisada`. Campos vazios com estado pendente não representam ausência de conteúdo sensível. Para concluir a curadoria, revise cada trecho, preencha seus avisos e relevância e altere o estado de avaliação. Os resumos e consequências continuam opcionais e não são criados automaticamente.

## Contrato semântico entre autoria e publicação

A autoria normaliza `data-locutor-id`, `data-pensador-id` e `data-pov-id` para `data-speaker`, `data-thinker` e `data-pov-character`. O leitor e a validação continuam aceitando as formas antigas. Referências múltiplas são separadas por espaços; cada identidade deve existir nos personagens da obra ou no registro nativo `story-entities`. Destinatários e alvos nativos também são verificados. Registros inválidos não são ignorados silenciosamente pela geração.

Ligações `data-verbete-id` são verificadas contra os verbetes da obra. Ligações `data-glossary-term` precisam de uma definição no registro nativo `story-glossary`. A importação preserva essas ligações em elementos inline compatíveis. Quando há ligações explícitas de glossário na autoria, elas prevalecem sobre a marcação automática de ocorrências por palavra.

No leitor, cada auxílio é habilitado apenas quando há marcações correspondentes disponíveis. O indicador de POV acompanha a rolagem e é recalculado em mudanças de aparência e tamanho da janela. A ativação das etiquetas preserva a posição do parágrafo visível. Na edição offline, os destinos internos recebem um prefixo por capítulo e seus links são reescritos em conjunto para evitar colisões.

## Participações editoriais

`personagens_ids` é uma lista opcional de IDs do cadastro da própria obra, aceita em capítulos e cenas. A lista deve conter referências existentes, sem repetições. Não usa nomes como chaves e não é preenchida por busca textual. A consulta inversa do personagem é derivada dessas associações. Capítulo e cena mantêm listas independentes, e cenas privadas continuam excluídas da saída pública. Os seletores do Studio preservam esses campos e permitem escolher os personagens por nome/apelido.

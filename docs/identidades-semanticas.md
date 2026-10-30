# Personagens e identidades semânticas

A biblioteca da obra administra a identidade, o nome, os apelidos e o tipo semântico do personagem. O editor usa essa identidade nas marcações. Personagens vinculados não têm um segundo cadastro independente no editor.

## Acessos

**Entidades e identidades** no editor — ou a ferramenta **Entidades** da barra lateral — abre a gestão integrada. Ela distingue:

- **Cadastro da obra:** personagem vinculado, cuja ficha é aberta na biblioteca.
- **Local à autoria:** entidade provisória ou outro elemento narrativo ainda não cadastrado como personagem.
- **Conflito:** nome, tipo ou apelidos precisam de conciliação.

É possível criar um personagem diretamente no cadastro, criar/editar/remover entidades locais, vincular uma importada, revisar uma proposta individual para o cadastro e consultar as ocorrências da autoria. A exclusão de personagens vinculados permanece na biblioteca, com proteção de referências; remover uma entidade local não exclui um personagem da obra.

Os campos de falante, pensador, destinatário, alvo e POV oferecem busca por nome, apelido ou ID e gravam referências permanentes. O tipo semântico do personagem pode ser `character` ou `creature`; uma criatura pode ser personagem e POV. A alteração de tipo não renomeia o ID e pode exigir revisão das marcações e reexportação dos capítulos afetados.

## Comparação entre cadastro e autoria

O campo adicional `integracao_entidades` do `.narrproj` guarda versão da integração, identidade da obra, bases dos personagens utilizados, conflitos e procedência de importações/vínculos. O formato principal da autoria continua na versão 5.

Ao sincronizar, o Studio compara o cadastro atual, a base salva e a representação local:

- Se somente o cadastro mudou, a representação é atualizada e a autoria fica pendente de salvamento.
- Se a autoria mudou o nome, o tipo ou os apelidos de um personagem vinculado, a diferença exige revisão.
- Se os dois lados mudaram, os valores locais são preservados e o conflito é apresentado.
- Autorias antigas sem base salva não têm nomes ou tipos divergentes sobrescritos: diferenças relevantes viram conflitos.

Em **Conciliar conflitos**, escolha **Usar dados do cadastro** ou **Revisar proposta para o cadastro**. A proposta mostra uma comparação e usa backup/revisão antes de gravar. Enquanto houver conflitos, a aplicação e a exportação são bloqueadas. Salvar o rascunho continua permitido para conservar o trabalho pendente.

O comando genérico **Recursos da obra** continua voltado às definições do glossário. Personagens são cadastrados e alterados pela ficha ou por propostas individuais, evitando copiar indiscriminadamente todas as entidades locais para a biblioteca.

## Importações

Um arquivo importado que não declare a mesma identidade de obra não recebe vínculos só porque seus IDs coincidem com os do cadastro. IDs coincidentes recebem identidades locais provisórias, e as referências nas marcações/seções são ajustadas sem mudar o texto. O tipo original é preservado.

A procedência inclui o resumo criptográfico do arquivo, a obra declarada de origem, o destino e os IDs remapeados. Vínculos anteriores continuam como histórico. Use **Vincular importada** para confirmar a identidade, ou uma proposta individual para cadastrar um novo personagem. Nomes e apelidos auxiliam a seleção, mas não fazem fusões automáticas.

Uma autoria aberta sem capítulo ativo continua sem vínculo de capítulo: metadados do arquivo não autorizam alterar outro capítulo automaticamente. O vínculo é estabelecido pelo contexto selecionado no Studio.

## Cópias para portabilidade

O `.narrproj` conserva entidades locais e cópias dos personagens usados ou em conflito. Na abertura de uma autoria vinculada, o catálogo atual fornece as demais opções dos seletores. O HTML exportado inclui somente entidades referenciadas nas marcações, reduzindo a repetição de elencos completos.

As cópias servem para portabilidade e comparação; o cadastro da obra permanece a autoridade. Um editor externo que ignore e descarte o campo de integração pode perder a base de comparação. Nesse caso, a reabertura é conservadora, como uma autoria antiga sem base.

## Nome contextual e revelações

Nas marcações de fala, pensamento e citação, **Nome apresentado neste trecho** (`data-display-name`) pode conter `???` ou um pseudônimo. Na seção/POV, **Nome apresentado no indicador de POV** (`data-pov-display-name`) faz o mesmo para o indicador.

A identidade verdadeira permanece na referência. O leitor usa a apresentação explícita daquele contexto; quando ela está vazia, usa o nome disponível pelas regras existentes de revelação. O nome contextual é texto editorial público: confira a prévia antes de publicar. Vincular uma voz conhecida pelo autor não obriga a revelar o nome real ao leitor.

## Ocorrências e participações

A ficha do personagem oferece **Ocorrências semânticas deste personagem**. Ela distingue as marcações no **capítulo aplicado**, na **autoria salva** e na **sessão aberta**. A mesma marcação pode aparecer em versões diferentes. A consulta permite abrir o capítulo correspondente.

No editor, **Ocorrências na autoria** permite selecionar uma marcação e ir ao trecho atual. Funções como falante, pensador, destinatário, alvo e POV são mostradas separadamente. Não há inferência por busca de nomes no texto.

As participações declaradas em capítulos e cenas continuam independentes das ocorrências semânticas. O painel **Participações do capítulo** oferece as referências existentes como proposta para o autor conferir; não afirma presença física nem sobrescreve automaticamente a lista editorial.

## Verificações

- `python3 -m unittest discover -s tests -q`: sincronização, conflitos, importações, origens, tipos, ocorrências e demais contratos.
- `node tests/test_semantica.cjs`: nomes contextuais e comportamento dos auxílios.
- `python3 tests/verificar_identidades_grafico.py`: em cópia temporária, verifica base salva, atualização do cadastro, conflito preservado e conciliado, seleção por apelido, ocorrências, apresentação contextual, exportação enxuta e isolamento de colisões de importação.

As alterações de arquivos de autoria existentes acontecem ao salvar/aplicar, com as proteções locais habituais. Os testes gráficos não alteram a obra real.

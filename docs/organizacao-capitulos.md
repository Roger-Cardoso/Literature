# Organização hierárquica dos capítulos

O Literature Studio apresenta a estrutura editorial como **Obra → Saga → Volume → Arco → Capítulo**. Obras com capítulos simples continuam funcionando. Agrupamentos vazios aparecem na árvore e podem ser selecionados para criação de conteúdo.

## Posição e identidade

- **ID:** identidade permanente. Mover um capítulo ou agrupamento não muda os IDs.
- **Pertencimento:** determinado pelo agrupamento que contém o item no JSON editorial.
- **Ordem:** inteiro positivo, único entre irmãos. As operações de organização ajustam a sequência dos grupos afetados.
- **Posição exibida:** endereço calculado, como `1.2.3.4` para saga, volume, arco e capítulo. Não é gravado como outra fonte de verdade.
- **Número editorial:** rótulo do capítulo para o leitor, como `12`, `Prólogo` ou `Extra 2`. Não é renumerado automaticamente.
- **Arquivo:** o texto permanece no mesmo caminho ao mover. A hierarquia editorial não obriga a reorganizar pastas do computador.

A árvore e a geração pública compartilham a ordenação pelo campo `ordem`, independentemente da disposição física dos itens nas listas do JSON. Identidades repetidas, ordens repetidas/não positivas, nomes vazios e estruturas misturadas são recusados pela validação estrutural.

## Navegar

A coluna **Posição** mostra o endereço editorial; **Publicação** distingue publicado, rascunho e arquivado. Os agrupamentos mostram o total de capítulos descendentes. O caminho do item selecionado aparece sobre os metadados, incluindo a posição para distinguir agrupamentos com nomes iguais.

Use a busca para localizar título, número, ID ou agrupamento. A busca ignora acentos e diferenças entre maiúsculas e minúsculas. O filtro de publicação pode ser combinado com a busca. Os ancestrais dos capítulos encontrados continuam visíveis.

**Expandir caminho atual** abre os ancestrais e revela a seleção; quando necessário, limpa os filtros que a escondem. **Recolher** fecha os ramos. Atualizações preservam a seleção por identidade e o estado de expansão. Texto HTML, cenas e notas são materializados na árvore quando o capítulo é expandido, reduzindo a quantidade de widgets em obras extensas. Barras de rolagem vertical e horizontal permanecem disponíveis.

## Inserir capítulos

1. Selecione um arco, capítulo ou agrupamento da obra.
2. Clique em **Novo capítulo**.
3. Informe o título, confira o arco de destino e escolha a posição final.
4. Clique em **Criar capítulo nesta posição**.

O capítulo é criado como rascunho, com ID novo e número editorial vazio. No painel **Organizar capítulos**, um capítulo selecionado também oferece **Inserir novo capítulo antes** e **depois**. O destino é sempre mostrado antes de gravar.

## Criar agrupamentos

Abra **Organizar capítulos → Novo agrupamento**. Escolha saga, volume ou arco, informe nome, destino e posição. A seleção atual ajuda a preencher o agrupamento pai. Um volume precisa de uma saga; um arco precisa de um volume. É possível criar agrupamentos sem capítulos e preenchê-los depois.

Obras simples oferecem uma ação explícita para organizar os capítulos existentes em **Saga 1 → Volume 1 → Arco 1**. A conversão mantém os dados dos capítulos e permite criar os demais agrupamentos em seguida.

## Reordenar e mover

- **Subir/Descer:** desloca o item selecionado uma posição entre irmãos.
- **Organizar capítulos:** permite escolher outro destino compatível e uma posição final, tanto para capítulos quanto para agrupamentos.
- **Conferir movimentação:** apresenta o caminho atual e o proposto.
- **Aplicar movimentação com backup:** grava a proposta conferida. Se destino ou posição forem alterados, é necessário conferir novamente.

Mover um agrupamento leva seus descendentes. A estrutura fixa impede destinos de nível incorreto. IDs, arquivos, cenas, notas, números editoriais, autoria semântica e referências de progresso são preservados. A publicação passa a seguir a nova ordem quando o site for validado e gerado novamente.

O campo `ordem` é somente leitura no formulário comum: use as ações de organização. A estrutura avançada em JSON continua disponível e passa pela validação estrutural antes de salvar.

## Proteção de alterações

As operações usam backup e revisão do arquivo editorial. Se ele mudar enquanto um painel estiver aberto, a proposta antiga não sobrescreve a versão nova. Se a criação de capítulo falhar ao gravar os metadados, seu arquivo provisório é removido e a estrutura fornecida à operação permanece intacta.

Ao recarregar uma estrutura reorganizada externamente, a seleção é localizada pelo ID, não pelo índice antigo da lista. A faixa de estado indica quando o site gerado ficou desatualizado.

Em janelas estreitas, os painéis do editor incorporado podem ser alternados pelos botões **Ferramentas** e **Propriedades semânticas**, mantendo a coluna de texto utilizável ao lado da árvore.

## Verificação

- `python3 -m unittest discover -s tests -q`: regras de identidade, posições, movimentações, conversão e conflitos de gravação.
- `python3 tests/verificar_hierarquia_grafica.py`: em sessão gráfica, usa uma cópia temporária com 1.000 capítulos fictícios. Verifica árvore, ordem, agrupamentos vazios, expansão sob demanda, movimentação visual, inserção, criação de agrupamento, filtros, recarregamento por ID, vínculo semântico, janela menor e correspondência com a ordem pública.
- `python3 tests/verificar_studio_grafico.py`: fluxo de autoria, revisão e aplicação.
- `python3 tests/verificar_rolagem_grafica.py`: deslocamento real das áreas roláveis.

Esses testes não gravam nos manuscritos reais. O cenário com mil capítulos verifica comportamento; não representa uma medição de desempenho em sessão prolongada.

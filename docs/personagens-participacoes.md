# Personagens e participações

O cadastro da obra é a referência para as participações editoriais. Os seletores mostram nomes e apelidos, mas salvam identidades permanentes em `personagens_ids`. Renomear um personagem não exige reescrever os capítulos e cenas que o referenciam.

## Biblioteca e ficha na mesma janela

Clique em **Personagens** na árvore da obra para abrir a **Biblioteca de personagens**, uma página persistente do gerenciador. A árvore principal não lista personagens individuais; eles aparecem somente na biblioteca. O botão **Personagens** da barra superior abre a mesma página.

A biblioteca reúne busca por nome, apelido ou ID, apresentação curta, contagem de capítulos associados e ações de CRUD:

- **Novo personagem:** cria o registro e abre sua ficha.
- **Clique simples em um personagem:** abre sua página de gestão de metadados. Pelo teclado, selecione a linha e pressione Enter.
- **Abrir ficha:** oferece a mesma navegação pelo botão.
- **Excluir personagem:** apresenta uma revisão antes de remover o cadastro com backup.
- **Atualizar:** relê o cadastro e as contagens.

A ficha permite editar nome, apelidos, descrição, imagem, descrição alternativa e marco de disponibilidade por um seletor de capítulos. Use **Salvar** para gravar. A identidade permanece somente leitura. **Voltar à biblioteca de personagens** ou clicar novamente na entrada da árvore retorna à biblioteca. Alterações pendentes continuam protegidas pela escolha de salvar, descartar ou cancelar a navegação.

Homônimos são permitidos e distinguidos pelo ID; nomes iguais não provocam fusão automática. **Consultar participações deste personagem** abre somente as participações da ficha atual, com acesso direto ao capítulo ou cena. O índice inclui rascunhos e cenas privadas, pois é uma ferramenta local. Os dados privados continuam sujeitos aos filtros da geração pública.

## Exclusão com preservação de vínculos

A exclusão é bloqueada enquanto existirem participações editoriais ou marcações semânticas que referenciem o personagem nos textos, nos arquivos de autoria da obra ou na autoria atualmente aberta. O painel informa onde ele está em uso. Remova ou substitua os vínculos antes de repetir a exclusão.

Personagens sem uso podem ser excluídos pelo botão **Excluir personagem com backup**. A operação confere novamente os vínculos e a revisão do cadastro antes de gravar. Textos, arquivos de imagem e autorias históricas não são apagados; registros de entidades sem marcações não contam como participação. Uma referência em uma autoria histórica ainda marcada precisa ser revista antes da exclusão.

## Associar participações a capítulos e cenas

Selecione um capítulo ou uma cena. O campo **Participações** oferece os personagens existentes na obra, com busca por nome e apelido. A seleção é múltipla e permanece preservada ao filtrar a lista. Clique nos nomes desejados e salve os metadados. **Limpar seleção** remove as associações daquele campo.

As participações de capítulo e cena são independentes: uma associação de cena aparece no índice do personagem, mas não duplica automaticamente a lista do capítulo. Uma associação editorial não afirma presença física; pode representar uma participação que o autor deseja registrar. O programa não procura nomes no texto para decidir participações.

Vínculos inexistentes ou repetidos são rejeitados na gravação e na publicação. Referências antigas ausentes permanecem visíveis no seletor para correção, em vez de serem descartadas silenciosamente. Uma alteração do cadastro que removeria um personagem ainda associado é bloqueada, inclusive ao restaurar metadados de uma cópia anterior.

## Vincular personagens importados pelo editor semântico

No editor de um capítulo, abra **Entidades e identidades → Vincular importada**:

1. Escolha uma entidade importada ainda sem vínculo com o cadastro.
2. Selecione o personagem existente na obra que ela representa.
3. Clique em **Conferir vínculo** e confira o destino e a quantidade de marcações afetadas.
4. Clique em **Aplicar vínculo à autoria**.

O editor substitui a identidade importada nas referências de fala, pensamento, destinatário, alvo e POV, usando o ID do cadastro. Texto, formatação, intervalos e histórico de escrita são preservados. A operação não funde dois personagens já cadastrados. Metadados adicionais compatíveis são preservados; conflitos de metadados adicionais são bloqueados para revisão.

O vínculo altera a autoria em memória. Use **Salvar** para conservá-la no `.narrproj` e **Revisar e aplicar ao capítulo** para atualizar o texto editorial. O arquivo externo original não é sobrescrito por essa operação.

## Participações a partir de marcações explícitas

O botão **Participações do capítulo** no editor oferece uma seleção inicial com as associações já cadastradas e os personagens do cadastro referenciados nas marcações da autoria atual. É uma proposta para conferência: o autor pode marcar ou desmarcar personagens antes de aplicar.

Entidades ainda não vinculadas ao cadastro não entram nessa proposta. Use primeiro o vínculo de personagens quando necessário. **Aplicar participações ao capítulo com backup** grava somente as associações editoriais; não aplica implicitamente o texto em edição.

Nomes, tipos e apelidos são comparados com uma base salva na autoria. Divergências ficam preservadas para **Conciliar conflitos** ou para uma proposta individual ao cadastro. Consulte [Identidades semânticas](identidades-semanticas.md). A autoria e o cadastro continuam tendo salvamentos explícitos.

## Validação

`python3 -m unittest discover -s tests -q` cobre referências, homônimos, renomeações, preservação de metadados e bloqueio de referências inválidas. Em uma sessão gráfica, `python3 tests/verificar_biblioteca_personagens_grafica.py` verifica navegação por clique, árvore sem personagens filhos, CRUD e exclusão protegida em cópia temporária. `python3 tests/verificar_personagens_grafico.py` verifica o fluxo completo em cópia temporária, incluindo busca, capítulos e cenas, consulta inversa, vínculo semântico e preservação do desfazer. Os manuscritos reais não são modificados pelos testes.

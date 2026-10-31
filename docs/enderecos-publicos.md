# Endereços públicos do Literature

As obras usam `/nome-da-obra/`, e os capítulos usam `/nome-da-obra/capitulo-1/`, `/nome-da-obra/capitulo-2/` etc. O título do capítulo não entra no endereço.

A ficha da obra no Studio separa a pasta interna (`slug`) do **Endereço público**. O endereço inicial é sugerido a partir do título, com letras minúsculas sem acentos, números e hífens. Alterar apenas o título não muda o endereço já atribuído. A ficha mostra uma prévia do link. Endereços reservados, repetidos ou em conflito com outra pasta são recusados.

Cada capítulo recebe um `numero_url` inteiro e exclusivo em toda a obra, percorrendo inicialmente a ordem de sagas, volumes, arcos e capítulos. A numeração também reserva os rascunhos. Depois de atribuída, ela é permanente: mover o capítulo, alterar seu título ou sua numeração de apresentação não transfere o link para outro texto. Novos capítulos recebem o próximo número disponível, mesmo se inseridos antes de outros. Excluir um capítulo não libera seu número para reutilização. Portanto, podem existir lacunas na sequência pública. O Studio mostra esse número como somente leitura.

O campo editorial `numero` continua sendo a numeração de apresentação; `ordem` continua determinando a organização da árvore e a sequência de leitura. O endereço, o ID e a posição têm funções distintas.

Ao mudar o endereço público da obra, o Studio guarda o anterior em `enderecos_anteriores`. A geração mantém páginas de encaminhamento para a obra e seus capítulos nos endereços anteriores. Os acessos antigos `pasta/index-obra.html`, `pasta/` e `pasta/leitor.html?id=ID` continuam funcionando. O leitor resolve o ID original e encaminha ao capítulo correto, conservando o parâmetro de cena e o fragmento. Um ID inexistente mostra erro de leitura; não é encaminhado a um capítulo aleatório.

Comentários, reações e progresso continuam associados aos mesmos IDs. O manifesto de interações atualiza os links administrativos após a publicação, mantendo a identidade das discussões e dos votos.

A geração cria pastas com `index.html`, metadados canônicos e o ID do capítulo incorporado à página. Recursos e dados da obra continuam em sua pasta interna. Não é necessário um servidor de aplicação ou uma regra de reescrita do GitHub Pages. Os encaminhamentos de compatibilidade usam JavaScript; o endereço antigo da obra também oferece um link de continuação.

**Gere e publique pelo Studio após alterar metadados.** A prévia precisa ser servida com `site/` como raiz, como já ocorre no Studio. As rotas começam na raiz do domínio personalizado. Não edite a saída `site/` manualmente. As fontes antigas sem campos de endereço recebem valores sugeridos na geração sem alteração dos arquivos; salvá-las pelo Studio fixa esses valores para as próximas edições.

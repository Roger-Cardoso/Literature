# Reações de leitores

Obras e capítulos oferecem **Gostei** e **Não gostei**, com totais separados, sem cadastro. O site continua no GitHub Pages e usa o mesmo Worker e banco D1 dos comentários.

## Uso no site

Uma reação por identificador de navegador em cada obra/capítulo. Escolher a outra opção troca o voto; clicar na opção já selecionada retira o voto. O estado e os totais só mudam na tela depois da confirmação do serviço. Uma repetição do mesmo pedido não soma outro voto.

Os totais são consultados ao abrir a página. A identificação aleatória é criada no armazenamento local apenas ao escolher uma reação. Se ela já existir, o site consulta a reação correspondente para marcar o botão selecionado. Sem armazenamento local, os totais continuam visíveis e o formulário explica por que não é possível votar.

O Turnstile é carregado quando necessário após a escolha de uma reação, com ação `reaction`. A verificação vale por dez minutos para o identificador e a conexão. O serviço também limita a conexão a 60 tentativas de alteração por janela de dez minutos. Não há verificação externa para apenas visualizar os totais. Prévia local e leitura offline não registram votos.

Limpar os dados do navegador ou usar outro navegador/dispositivo permite outra identificação. Não são pessoas únicas nem uma pesquisa representativa. Os limites reduzem abuso, mas não impedem manipulação por múltiplas conexões ou identidades.

## Gerenciamento

Em **Site e comentários**, configure a ativação global e os padrões de obras e capítulos. Nas fichas, o campo **Reações** permite herdar, ativar ou desativar; desativar na obra também desativa seus capítulos. Reações e comentários são independentes.

Gere e publique o site pelo Studio para sincronizar as permissões da versão publicada. A mesma lista de IDs estáveis agora informa separadamente quais itens recebem comentários e quais recebem reações. Alterar títulos não perde votos. Arquivar ou desativar remove o acesso público, conservando os registros no banco; eles voltam a ser considerados quando o mesmo ID é habilitado novamente.

Em **Gerenciar reações**, carregue a mesma credencial da moderação e conecte. A tela oferece busca de títulos, paginação, totais separados, quantidade de votos e proporção de Gostei acompanhada da amostra. A exportação JSON inclui os totais de todo o catálogo sincronizado, independentemente da busca atual, sem identificadores dos visitantes. Itens retirados do catálogo permanecem no banco, mas não entram nessa exportação.

**Pausar / retomar selecionado** age diretamente no serviço, sem precisar publicar novamente. A pausa bloqueia temporariamente registro, troca e retirada de votos e preserva os totais. A pausa é independente da ativação editorial: retomar não reativa um item desativado nas fichas.

## Atualização do serviço

Na pasta `backend/comentarios`, aplique `npx wrangler d1 migrations apply literature-comments --remote` e depois `npx wrangler deploy`. Faça isso antes de publicar a interface nova. A migração `0003_reactions.sql` acrescenta as permissões às discussões e cria tabelas e gatilhos de reações; não altera nem apaga comentários.

O banco impõe unicidade por item e resumo do identificador. Gatilhos atualizam contadores na mesma transação de inserir, trocar ou remover, evitando contar todos os votos a cada visita. O identificador original e o IP não são guardados nas reações. A identidade é transformada por HMAC com o segredo existente; trocar esse segredo invalida o vínculo com votos anteriores. Resumos de conexão e autorizações temporárias expiram e são removidos pela rotina diária.

A credencial administrativa continua privada, fora do projeto. Nenhum token é incluído no site ou na exportação dos totais. O gerenciador usa a sessão em memória e não publica credenciais.

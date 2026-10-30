# Biblioteca e gerenciamento de obras

Abra o Literature Studio e clique em **Obras** na barra principal. A biblioteca é uma aba da mesma janela; reabrir o comando reutiliza essa aba.

## Biblioteca

Busque por título, autor, endereço ou identidade permanente. O filtro de publicação oferece rascunhos, publicadas e arquivadas. A lista mostra andamento, total de capítulos, quantidade de capítulos marcados como publicados e número de personagens. Essa contagem de capítulos não significa que eles já estejam disponíveis no site: a obra também precisa estar publicada e passar pela validação.

Selecione uma linha e use **Abrir metadados**, duplo clique ou Enter. A ficha existente permite editar título, autor, sinopse, idioma, andamento, publicação, ordem do catálogo, gêneros, temas e demais metadados. A capa e os recursos associados continuam disponíveis na árvore. O título pode mudar sem alterar a identidade ou o endereço da obra. Salve pelo botão **Salvar** ou Ctrl+S.

## Criar

**Nova obra** abre um formulário integrado com título, autor e endereço. O endereço aceita letras minúsculas, números e hífens. Endereços existentes são recusados.

A obra recebe identidade própria, metadados iniciais, páginas de obra/leitor e estrutura de capítulos vazia, sempre como rascunho. Depois, use **Novo capítulo**, **Organizar capítulos**, **Personagens** e o editor semântico. Os modelos ficam em `scripts/modelos/obra/`, permitindo criar obras mesmo com o cadastro vazio; não é necessário manter `obra-1` como modelo vivo.

## Arquivar

**Arquivar / voltar a rascunho** mostra a mudança antes de gravá-la e faz backup dos metadados. Arquivar conserva capítulos, personagens e autorias. Uma obra arquivada pode retornar a rascunho; não é publicada automaticamente.

As mudanças na publicação só entram na saída local depois de **Gerar site**. O gerenciamento não envia alterações ao GitHub.

## Exportar fontes

**Exportar fontes** cria um ZIP individual, fora da pasta do projeto. Ele inclui os arquivos da pasta da obra, inclusive autorias privadas `.narrproj`, textos HTML e metadados. Se houver autoria aberta com alterações, o Studio oferece salvá-la antes.

Esse é um pacote de fontes para guarda e transporte manual. Ele não é um site independente, não contém as imagens e outros recursos compartilhados de `assets/`, e não possui importação automática nesta versão. Para distribuição aos leitores, use o comando separado **Pacote de publicação**, que trabalha com a saída pública gerada.

## Excluir e restaurar

**Excluir com recuperação** exige digitar o endereço exato da obra. A operação retira o endereço de `obras.json` e move a pasta inteira para `.literature-lixeira/`, acompanhada de um manifesto. Recursos compartilhados ficam no projeto.

O Studio oferece resolver alterações pendentes antes da revisão. A autoria da obra excluída é fechada depois da confirmação. Se arquivos ou o cadastro mudarem durante a revisão, a exclusão é recusada para que você abra uma revisão atualizada. Falhas ao atualizar o cadastro tentam reverter a movimentação da pasta.

Em **Restaurar obra**, escolha a obra guardada. IDs, textos, participações e autorias são preservados. A obra volta como **rascunho**, para revisão antes de publicar. Um endereço ocupado, uma identidade já cadastrada ou arquivos de recuperação modificados impedem a restauração; os dados continuam guardados.

A recuperação é local e não substitui uma cópia de segurança em outro dispositivo. Sua pasta está ignorada pelo Git. Não há exclusão permanente pela interface. Um site gerado antes da exclusão continua com o conteúdo anterior até a próxima geração; uma publicação remota exige também atualizar os arquivos hospedados.

## Verificações

- `python3 -m unittest discover -s tests -q`: inclui CRUD, concorrência, preservação de autoria, falhas de cadastro e recuperação, colisões de endereço, pacote de fontes e criação após excluir todas as obras.
- `python3 tests/verificar_obras_grafico.py`: percorre a biblioteca, criação, edição, filtros, arquivamento, exportação, exclusão com editor aberto, restauração e cancelamento de edição, usando uma cópia temporária.

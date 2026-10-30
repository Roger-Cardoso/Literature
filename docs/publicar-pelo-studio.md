# Atualizar o site pelo Literature Studio

O botão **Publicar no GitHub** abre uma aba persistente na mesma janela. Ela permite conectar a conta, preparar a publicação, revisar arquivos, enviar e acompanhar o GitHub Pages. Não é necessário inicializar Git na pasta do projeto.

## Primeiro acesso

O destino inicial é `Roger-Cardoso/Literature`, branch `main`. É possível alterar e salvar outro destino ao preparar uma revisão. O repositório precisa ter o fluxo integrado do Studio em `.github/workflows/pages.yml`, identificado por `literature-studio-snapshot-v1`. A integração não cria repositórios, branches ou troca o domínio automaticamente.

O envio usa o **GitHub CLI (`gh`)** instalado na máquina. Em computadores novos, instale-o pelo site https://cli.github.com e use **Conectar GitHub**. Se for necessária autenticação, o Studio mostra o endereço oficial e o código temporário na área de detalhes. **Autorizar no navegador** abre https://github.com/login/device. Autorize sua conta; não cole tokens no gerenciador. As credenciais são administradas pelo GitHub CLI, fora do projeto. O botão **Cancelar autenticação** interrompe o processo de conexão iniciado pelo Studio.

A conta precisa de permissão para atualizar o conteúdo da branch de destino e consultar suas execuções. Restrições de branch e recusas de permissão são respeitadas; não existe envio forçado. A atualização inicial do fluxo de publicação exige permissão para modificar workflows.

## Publicar

1. Salve seus metadados. Salve a autoria semântica e revise/aplique ao capítulo quando houver diferenças.
2. Abra **Publicar no GitHub** e confira repositório e branch.
3. Use **Preparar e revisar**. O Studio valida, gera uma saída nova e compara com o repositório.
4. Confira a lista de arquivos a criar, alterar ou remover. Selecionar uma linha mostra o conteúdo público preparado, ou identifica o recurso binário. A prévia textual é limitada a 50 KB por arquivo.
5. Ajuste a descrição da atualização e clique em **Enviar versão revisada**.
6. Acompanhe o resultado na aba. **Abrir execução no GitHub** mostra os detalhes dos testes e da implantação. **Abrir site** abre o endereço configurado.

O envio é uma decisão explícita. Preparar não envia. Se os arquivos coincidirem com a versão remota, o Studio informa que não há mudanças. Se o destino, as fontes locais ou a branch remota mudarem depois da revisão, é necessário preparar novamente.

## Conteúdo enviado

O Studio envia **somente a saída pública gerada**, para a pasta gerenciada `publicado/` do repositório. Inclui páginas, capítulos publicados, dados públicos, imagens, estilos e scripts usados pelo site. Arquivos de autoria `.narrproj`, metadados editoriais de origem, rascunhos, lixeira, backups, credenciais e ferramentas locais não entram no pacote.

O código do Studio e do serviço de comentários permanece no repositório. Sua atualização é uma operação de desenvolvimento separada; o botão atualiza a publicação do site.

O manifesto `.literature-publicacao.json` identifica a publicação e confere seus arquivos por hash. O fluxo do GitHub valida esse pacote e o entrega ao Pages. Se ainda não houver `publicado/`, o fluxo conserva a geração a partir das fontes do repositório. Uma pasta `publicado/` já existente sem identificação do Studio não é assumida nem apagada automaticamente.

As remoções se limitam aos arquivos antigos dentro de `publicado/`. Os demais arquivos do repositório são preservados. Excluir uma obra do projeto local só retira suas páginas hospedadas depois de gerar, revisar e enviar a atualização, com implantação aprovada. Conteúdo removido de um repositório público pode continuar no histórico Git.

O envio suporta arquivos de até 50 MB e até 150 MB de dados alterados por publicação. Arquivos grandes usam envio binário; textos menores são agrupados para reduzir o número de solicitações. Não há sincronização automática dos manuscritos nem restauração das fontes locais a partir da saída pública.

## Comentários

A opção **Sincronizar comentários após implantação aprovada** usa a credencial privada já preparada em `~/.config/literature/comments-admin.json`. Ela não é enviada ao GitHub.

A sincronização utiliza o manifesto exato da versão enviada, depois de os testes e a implantação serem aprovados. Se a branch já tiver outra atualização, a sincronização antiga é recusada. Uma falha na sincronização não desfaz o site implantado; o resultado aparece na aba e pode ser retomado por **Sincronizar comentários agora** ou pela moderação.

Se não houver credencial local correspondente ao serviço, use a moderação para carregá-la. Um manifesto vazio fecha as discussões antigas sem apagar seus comentários. Desativar comentários com o endereço do serviço ainda configurado também permite sincronizar o manifesto vazio.

## Retomar e conferir

O destino fica em `.literature-studio.json`, e o último envio em `.literature-publicacoes/ultimo.json`. Esses arquivos locais são ignorados pelo Git e não contêm tokens. O recibo conserva commit, resultado, manifesto público e configuração pública necessários para retomar a consulta após reiniciar o Studio.

**Consultar publicação** acompanha a execução correspondente ao commit enviado. O acompanhamento ocorre a cada 15 segundos enquanto está pendente, sem confundir envio com implantação aprovada. Fechar o programa não cancela uma execução já iniciada no GitHub.

Se houver perda de conexão durante o envio, consulte o recibo e o histórico remoto antes de repetir. A integração confere se a branch recebeu o commit mesmo quando a resposta final se perde. Uma falha antes de atualizar a branch pode deixar objetos sem referência no GitHub, sem alterar o site.

## Verificações

- `python3 -m unittest discover -s tests -q`
- `python3 tests/verificar_publicacao_grafico.py`
- `python3 scripts/verificar_publicacao.py publicado` — usado no GitHub Actions.

Os testes gráficos usam uma cópia temporária e um GitHub fictício. O ensaio real de envio deve usar o pacote público revisado e a conta autorizada.

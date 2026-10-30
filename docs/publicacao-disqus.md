# Histórico: integração Disqus substituída

A integração ativa foi substituída por comentários próprios com Cloudflare Workers e D1. Não é necessário criar fórum no Disqus ou contratar esse serviço. Consulte [o guia atual](comentarios-proprios.md). As instruções de domínio/GitHub Pages abaixo continuam úteis; a configuração de comentários Disqus é apenas histórica.

# Publicação do Literature e comentários

Destino: `Roger-Cardoso/Literature`. Endereço: `https://literatura.roger.cardoso.nom.br/home/`.

## Comentários

No Studio, use **Site e comentários**. Cadastre o site em https://disqus.com/admin/create/ e informe o **shortname** fornecido, sem `.disqus.com`. O identificador é público, não é uma senha. Ative a integração, escolha os padrões de obras/capítulos, salve e gere o site.

No painel do Disqus, configure:

- URL do site: `https://literatura.roger.cardoso.nom.br`.
- Idioma: português.
- Trusted Domains: `literatura.roger.cardoso.nom.br`, sem protocolo nem caminho.
- Moderação e anúncios conforme sua preferência e plano.

O projeto não cria a conta Disqus. Enquanto o shortname estiver vazio, a integração permanece desativada. Não há credenciais ou chaves secretas no navegador.

A ficha de cada obra e capítulo oferece **Comentários**, com `herdar`, `ativado` e `desativado`. Desativar uma obra também bloqueia os comentários de seus capítulos. Essas opções não ativam um serviço globalmente desativado.

As discussões usam a identidade permanente da obra e do capítulo; títulos e posições não determinam o vínculo. Cada página possui URL HTTPS canônica, e os parâmetros de rastreamento e âncoras do navegador não criam outras discussões.

O leitor encontra a discussão depois do texto e da navegação final. A discussão geral da obra avisa sobre spoilers de toda a obra; capítulos avisam sobre spoilers daquele capítulo. A moderação dos comentários é feita no Disqus, não pelo guia de cenas.

O script externo só é solicitado ao clicar em **Abrir comentários**. Antes disso, a área explica o serviço e oferece o link da política de privacidade. Prévia local, outros domínios e edição offline não carregam discussões reais. Uma falha de rede permite tentar novamente e não interrompe a leitura. O plano gratuito pode exibir anúncios, e o serviço possui suas próprias práticas de coleta de dados; o carregamento por clique não substitui avaliar as configurações e os requisitos de privacidade aplicáveis ao site.

A incorporação usa https://help.disqus.com/en/articles/1717112-universal-embed-code e a atualização dinâmica usa https://help.disqus.com/en/articles/1717163-using-disqus-on-ajax-sites.

## GitHub Pages

O fluxo `.github/workflows/pages.yml` executa os testes, gera a saída e publica **somente `site/`**. Em **Settings → Pages**, a fonte deve ser **GitHub Actions**.

Configure o domínio personalizado em **Settings → Pages → Custom domain** como `literatura.roger.cardoso.nom.br`. O arquivo CNAME do projeto registra o endereço pretendido, mas não substitui a configuração do Pages nem altera DNS. Em publicações por Actions, a configuração do domínio no GitHub é necessária.

No provedor que administra o DNS de `roger.cardoso.nom.br`, configure o registro do subdomínio:

| Campo | Valor |
|---|---|
| Tipo | CNAME |
| Nome relativo à zona `roger.cardoso.nom.br` | `literatura` |
| Destino | `Roger-Cardoso.github.io` |

Se o provedor administra uma zona superior, use o nome correspondente ao subdomínio completo. Não inclua protocolo, `/home`, nome de repositório ou caminho no destino. Após a verificação do domínio e emissão do certificado, ative **Enforce HTTPS** no GitHub Pages. A orientação oficial está em https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site.

## Conteúdo e próximas atualizações

Um cadastro vazio produz uma página inicial sem obras, o que é suportado. Não restaure obras excluídas apenas para conseguir publicar: cadastre ou restaure deliberadamente o conteúdo desejado, revise os metadados e marque as obras e capítulos prontos como publicados. Depois, valide, gere e atualize o repositório.

O gerenciador é local. Salvar nele não envia alterações ao GitHub automaticamente. O processo de publicação deve enviar somente os arquivos escolhidos; backups, lixeira, arquivos pessoais e exportações ficam fora. Rascunhos presentes em um repositório público continuam acessíveis no código/histórico mesmo quando o gerador não os inclui no site.

Os testes usam obras sintéticas em diretórios temporários, independentes do catálogo do autor. Por isso a publicação continua verificável depois de excluir todas as obras reais.

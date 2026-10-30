# Serviço de comentários do Literature

Worker + D1, separado do site estático. Texto simples, aprovação obrigatória, uma camada de respostas, exportação e moderação no Studio. Não usa Disqus nem contas de leitores. Os testes do serviço usam SQLite real e a interface D1 adaptada, sem criar dados na Cloudflare.

## Pré-requisitos e implantação

Use uma conta Cloudflare com Workers no plano gratuito e Node 22.13 ou superior. Não é necessário transferir o DNS do Registro.br: o serviço pode usar seu endereço `workers.dev`, enquanto as páginas continuam no GitHub Pages.

Na pasta `backend/comentarios`:

1. `npm ci`
2. `npx wrangler login` — ou `npx wrangler login --device` em sessão remota.
3. `npx wrangler d1 create literature-comments`
4. Coloque o ID retornado em `d1_databases[0].database_id` do `wrangler.jsonc`. Não use o identificador de exemplo em produção.
5. Confira `SITE_ORIGIN`, que deve ser a origem HTTPS exata do site, sem barra final.
6. `npm run migrate:remote`
7. `npm run deploy`

Não execute a migração remota em um banco diferente sem conferir nome e ID. As migrações são versionadas pelo Wrangler.

## Implantação assistida

Depois de autenticar o Wrangler, também é possível executar, na raiz, `python3 scripts/implantar_comentarios.py`. O utilitário cria os recursos específicos do projeto, evita sobrescrever recursos de mesmo nome sem credencial local de origem, aplica a migração, implanta, registra segredos por entrada privada, verifica a saúde, atualiza a configuração pública, gera o site e sincroniza suas discussões.

Se houver mais de uma conta autorizada, ele pede a escolha por `--account-id`. Não assina planos pagos. A conta precisa permitir Workers, D1 e Turnstile; um subdomínio `workers.dev` precisa estar disponível para a implantação pelo Wrangler. Se o painel exigir configurar esse subdomínio, conclua essa etapa antes de repetir.

As credenciais ficam em `~/.config/literature/comments-admin.json`, com permissão apenas para o proprietário, fora do projeto. O Studio pode carregá-las por **Carregar credencial** na moderação. O utilitário conserva o progresso para retomada, sem imprimir segredos. Não copie esse arquivo para o repositório. A publicação no GitHub continua sendo uma etapa separada.

## Segredos e verificação

No painel Cloudflare Turnstile, crie um widget do tipo **Managed**, com hostname permitido `literatura.roger.cardoso.nom.br`. Não use chaves de teste na publicação. O widget não exige que o domínio use o DNS da Cloudflare.

O navegador recebe somente a **site key pública**. Configure a secret key e dois segredos aleatórios no Worker:

- `npx wrangler secret put TURNSTILE_SECRET_KEY`
- `npx wrangler secret put ADMIN_TOKEN`
- `npx wrangler secret put IP_HASH_SECRET`

Para `ADMIN_TOKEN` e `IP_HASH_SECRET`, use valores diferentes, gerados criptograficamente, com pelo menos 32 caracteres; prefira 64 caracteres hexadecimais. Guarde a credencial de moderação em seu gerenciador de senhas. Não a coloque no JSON do site, repositório, arquivo exportado ou chat. O Wrangler solicita o valor pela entrada privada do terminal.

A rota `/v1/health` confirma serviço e banco e informa `ready: true` quando os segredos necessários estão configurados. Não revela os valores. Ela não substitui testar a chave real do Turnstile no domínio publicado.

## Conectar ao site

No Studio, abra **Site e comentários**. Informe a URL HTTPS do Worker e a site key pública. Ative comentários, salve, gere e publique o site. A geração produz `site/comentarios-manifesto.json` com as discussões habilitadas de obras e capítulos públicos.

Abra **Site e comentários → Abrir moderação**, informe `ADMIN_TOKEN` e conecte. Use **Sincronizar discussões** para habilitar exatamente as discussões da versão gerada. Depois de publicar, arquivar, remover ou alterar as permissões de uma obra/capítulo, repita geração, publicação e sincronização. A sincronização não é automática no GitHub Actions e não coloca segredos no site.

A sincronização envia lotes de até 20 discussões para uma geração nova e só a efetiva quando todos os lotes chegaram. Uma falha antes da confirmação conserva a geração ativa. Um manifesto vazio fecha todas as discussões públicas sem apagar os comentários. Arquivar conteúdo no site, isoladamente, não fecha seu serviço: faça também a sincronização.

## Moderação

A interface oferece pendentes, aprovados, ocultos e todos, com paginação. O nome informado pelo visitante não autentica identidade. As mensagens não são publicadas automaticamente.

Aprovar uma resposta só a torna pública se a mensagem original estiver aprovada e a discussão continuar ativa. Ocultar o comentário principal também esconde suas respostas. Excluir remove definitivamente a mensagem e suas respostas, mediante confirmação no Studio.

A exportação salva todas as mensagens, inclusive pendentes e ocultas. O Studio exige um destino fora do projeto. Guarde-a em local privado. A cópia não contém a credencial administrativa; não existe importação automática de cópias nesta versão. Para uma cópia integral do banco, use também a exportação D1 pelo painel ou Wrangler e teste sua recuperação.

## Proteções e limites

- Somente discussões do manifesto ativo recebem/leem comentários públicos.
- Autorização de moderação por segredo, somente em cabeçalho HTTPS; o cliente recusa redirecionamentos.
- Origem web permitida exata, sem CORS aberto, e verificação server-side do Turnstile, hostname e ação `comment`.
- Campos com limites, tamanho máximo do corpo, armadilha antispam e 5 envios por conexão por janela de 10 minutos.
- Limite atômico no banco; endereço IP não gravado no comentário. Resumo HMAC com janela temporal para controle de frequência.
- Chave de envio estável evita duplicação em novas tentativas; texto continua no formulário quando o envio falha.
- Consultas parametrizadas; texto exibido como texto, sem HTML de visitantes.
- Mensagens de erro não expõem detalhes internos. Logs de observabilidade não são habilitados pelo projeto.
- Limpeza diária dos contadores expirados e gerações antigas; comentários não são removidos por inatividade.
- Sem anexos, e-mail, login, notificações, edição pelo visitante ou verificação de identidade nesta versão.

Não é uma promessa de armazenamento ilimitado ou bloqueio absoluto de spam. Acompanhe as cotas do plano e a fila. Configure contato e procedimentos de moderação adequados ao público. A página `privacidade.html` descreve o funcionamento e oferece o canal público do projeto para solicitações; revise esse contato antes de abrir a comunidade.

## Verificações locais

- `npm test` — contratos do serviço, com SQLite real.
- `npx wrangler deploy --dry-run --outdir /tmp/literature-worker-build` — compilação e bindings.
- `npm run migrate:local` — esquema somente na instância local.
- `npm run dev` — runtime local. A interface pública bloqueia envio em prévias locais; o teste ponta a ponta público exige o serviço configurado e o domínio HTTPS.
- Na raiz: `python3 -m unittest discover -s tests -q`, `node tests/test_comentarios.cjs`, `python3 tests/verificar_comentarios_grafico.py` e `python3 tests/verificar_moderacao_grafico.py`.

O arquivo `.dev.vars` e a pasta `.wrangler` são locais e ignorados pelo Git. Não exponha o endpoint administrativo no frontend; ele é usado pelo Studio com credencial de sessão.

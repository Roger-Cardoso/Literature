# Comentários próprios do Literature

O site continua no GitHub Pages. Um serviço separado Cloudflare Worker, com banco D1, guarda as conversas. O visitante não precisa de conta GitHub, Disqus ou cadastro de leitor.

## Para o leitor

No fim do capítulo ou na página da obra, **Abrir comentários** consulta somente mensagens aprovadas. A conversa do capítulo pode conter spoilers daquele capítulo; a conversa geral pode conter spoilers de toda a obra.

O formulário solicita nome e texto. Os nomes são informados pelo visitante, não verificados. A verificação antispam só é carregada quando a pessoa solicita **Verificar para enviar**. Ao enviar, a mensagem recebe a indicação de que aguarda aprovação: ela não é inserida imediatamente na conversa pública. Uma falha conserva o texto para nova tentativa.

É possível responder a um comentário principal aprovado. Há uma camada de respostas. Não há anexos, notificações, login ou edição pelo visitante nesta versão. A prévia local e o arquivo offline não enviam comentários reais.

## Configuração e moderação

1. Implante o serviço seguindo [as instruções do backend](../backend/comentarios/README.md).
2. No Studio, abra **Site e comentários**.
3. Informe a URL HTTPS do Worker e a chave pública do Turnstile, ative e salve.
4. Gere e publique o site. Ajuste a opção **Comentários** nas fichas de obra/capítulo quando necessário.
5. Abra **Abrir moderação**, informe a credencial administrativa e conecte. Ela fica apenas na sessão; não vai para o site.
6. Use **Sincronizar discussões** para autorizar exatamente as discussões da versão gerada.
7. Consulte pendentes, leia o texto e aprove, oculte ou exclua. Use **Mais resultados** para percorrer consultas maiores.

A sincronização deve ser repetida após publicar, arquivar, remover ou desativar comentários em obras/capítulos. Ela usa IDs permanentes e não muda a identidade da discussão quando o título muda. Somente discussões do catálogo sincronizado recebem novos envios. Uma sincronização vazia fecha as discussões e conserva os comentários para moderação.

Ocultar uma mensagem esconde suas respostas. Excluir apaga definitivamente a mensagem e as respostas, com confirmação. O botão de exportação gera uma cópia JSON privada, inclusive pendentes e ocultos, e exige destino fora do projeto. Não existe restauração automática desse JSON nesta versão; mantenha também cópias do D1 quando necessário.

A publicação do site e a sincronização do serviço são operações separadas. O GitHub Actions não recebe credenciais de moderação nem sincroniza sozinho. Gerar o site não implanta ou contrata o backend.

## Custo e estado de ativação

O projeto está preparado para usar as cotas gratuitas de Workers e D1. Não habilita plano pago nem garante capacidade ilimitada. A criação da conta, autenticação, configuração de Turnstile e implantação são necessárias para operar o serviço. Enquanto a URL e a chave pública não estiverem configuradas, a integração fica desativada.

Configurações antigas de Disqus são migradas para o provedor próprio desativado. Não há importação automática de comentários Disqus.

## Dados

O texto e o nome ficam no banco para moderação. O IP é processado durante a verificação e o limite de envio, mas não é salvo junto à mensagem. O contador temporário usa resumo com chave secreta e janela de tempo. Há uma página pública `privacidade.html` explicando o funcionamento e o canal do projeto; revise o contato e a operação de moderação antes de abrir a comunidade.

/* Disqus é opcional e só recebe conexão após uma ação explícita. */
(function(global){
    'use strict';
    let carregamento=null, sequencia=0;
    const criar=(tag,texto,classe)=>{const e=document.createElement(tag);if(texto)e.textContent=texto;if(classe)e.className=classe;return e;};
    function permitido(config,obra,capitulo){
        const d=config?.disqus;
        if(!d?.ativado||!/^[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?$/.test(d.shortname)||obra.comentarios==='desativado'||capitulo?.comentarios==='desativado')return false;
        const opcao=(capitulo||obra).comentarios;
        return opcao==='ativado'||d[capitulo?'capitulos':'obras']===true;
    }
    function identidade(config,obra,capitulo){
        const url=new URL(config.url_publica);
        if(url.protocol!=='https:'||url.username||url.password||url.port||!['','/'].includes(url.pathname)||url.search||url.hash)throw Error('Endereço público inválido.');
        if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(obra.slug)||!obra.id_obra||(capitulo&&!capitulo.id))throw Error('Identidade de comentários incompleta.');
        const pagina=new URL(`${obra.slug}/${capitulo?'leitor.html':'index-obra.html'}`,url.origin+'/');
        if(capitulo)pagina.searchParams.set('id',capitulo.id);
        return {identifier:JSON.stringify(['literature',String(obra.id_obra),capitulo?String(capitulo.id):null]),url:pagina.href,title:capitulo?`${capitulo.titulo} — ${obra.titulo}`:obra.titulo};
    }
    function carregar(shortname){
        if(global.DISQUS)return Promise.resolve();
        if(carregamento)return carregamento;
        carregamento=new Promise((resolve,reject)=>{
            const s=document.createElement('script');s.src=`https://${shortname}.disqus.com/embed.js`;s.async=true;
            const timeout=setTimeout(falhar,15000);
            function falhar(){clearTimeout(timeout);s.remove();carregamento=null;reject(Error('Não foi possível carregar o Disqus. A leitura continua disponível. Verifique a conexão ou os bloqueios do navegador.'));}
            s.onload=()=>{clearTimeout(timeout);resolve();};s.onerror=falhar;document.head.appendChild(s);
        });return carregamento;
    }
    async function montar({obra,capitulo=null,destino}){
        if(!destino)return;
        const vez=++sequencia;destino.replaceChildren();destino.hidden=true;
        try{
            const resposta=await fetch('../configuracao-site.json');if(!resposta.ok)return;
            const config=await resposta.json();if(vez!==sequencia||!permitido(config,obra,capitulo))return;
            const pagina=identidade(config,obra,capitulo);destino.hidden=false;destino.classList.add('comentarios-literature');
            destino.append(criar('h2',capitulo?'Comentários do capítulo':'Conversa sobre a obra'));
            destino.append(criar('p',capitulo?'Esta discussão pode conter spoilers deste capítulo. Evite revelar acontecimentos posteriores.':'Esta discussão geral pode conter spoilers de toda a obra.'));
            const aviso=criar('p','Comentários fornecidos pelo Disqus. Ao abrir, seu navegador se conecta ao serviço externo, que pode usar cookies e exibir anúncios.');destino.append(aviso);
            const privacidade=criar('a','Privacidade do Disqus');privacidade.href='https://help.disqus.com/en/articles/1717103-disqus-privacy-policy';privacidade.target='_blank';privacidade.rel='noopener noreferrer';destino.append(privacidade);
            if(location.origin!==new URL(config.url_publica).origin||location.protocol!=='https:'){
                destino.append(criar('p','Os comentários ficam disponíveis no endereço publicado. A prévia local não carrega discussões reais.'));return;
            }
            const botao=criar('button','Abrir comentários','btn-config');botao.type='button';destino.append(botao);
            const status=criar('p');status.setAttribute('role','status');destino.append(status);
            botao.onclick=async()=>{
                botao.disabled=true;status.textContent='Carregando comentários…';
                let thread=destino.querySelector('#disqus_thread');if(!thread){thread=criar('div');thread.id='disqus_thread';destino.append(thread);}
                const configurar=function(){this.page.identifier=pagina.identifier;this.page.url=pagina.url;this.page.title=pagina.title;this.language='pt_BR';};
                try{
                    if(global.DISQUS)global.DISQUS.reset({reload:true,config:configurar});
                    else{global.disqus_config=configurar;await carregar(config.disqus.shortname);}
                    if(vez!==sequencia)return;
                    botao.hidden=true;status.textContent='Se os comentários não aparecerem, confira a conexão e os bloqueios do navegador.';
                }catch(e){if(vez===sequencia){status.textContent=e.message;botao.disabled=false;botao.textContent='Tentar carregar comentários novamente';}}
            };
        }catch(e){destino.hidden=true;/* Falha do serviço opcional não interrompe a leitura. */}
    }
    global.ComentariosLiterature={montar,permitido,identidade};
})(window);

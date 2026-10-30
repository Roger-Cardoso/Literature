/* Interface própria. API e verificação só são carregadas por ação do leitor. */
(function(global){
 'use strict';
 let sequencia=0,turnstilePromise=null,widgetAtual=null;
 const criar=(tag,texto,classe)=>{const e=document.createElement(tag);if(texto)e.textContent=texto;if(classe)e.className=classe;return e;};
 function permitido(config,obra,capitulo){
  const c=config?.comentarios;
  if(!c?.ativado||!c.api_url||!c.turnstile_site_key||obra.comentarios==='desativado'||capitulo?.comentarios==='desativado')return false;
  return (capitulo||obra).comentarios==='ativado'||c[capitulo?'capitulos':'obras']===true;
 }
 function identidade(config,obra,capitulo){
  const url=new URL(config.url_publica);
  if(url.protocol!=='https:'||url.username||url.password||url.port||!['','/'].includes(url.pathname)||url.search||url.hash)throw Error('Endereço público inválido.');
  if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(obra.slug)||!obra.id_obra||(capitulo&&!capitulo.id))throw Error('Identidade incompleta.');
  const pagina=new URL(`${obra.slug}/${capitulo?'leitor.html':'index-obra.html'}`,url.origin+'/');if(capitulo)pagina.searchParams.set('id',capitulo.id);
  return {identifier:JSON.stringify(['literature',String(obra.id_obra),capitulo?String(capitulo.id):null]),url:pagina.href,title:capitulo?`${capitulo.titulo} — ${obra.titulo}`:obra.titulo};
 }
 function apiUrl(config){
  const url=new URL(config.comentarios.api_url);
  if(url.protocol!=='https:'||url.username||url.password||url.port||!['','/'].includes(url.pathname)||url.search||url.hash)throw Error('Serviço não configurado.');return url.origin;
 }
 function carregarTurnstile(){
  if(global.turnstile)return Promise.resolve();if(turnstilePromise)return turnstilePromise;
  turnstilePromise=new Promise((resolve,reject)=>{
   const s=criar('script');s.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';s.async=true;
   const falhar=()=>{clearTimeout(timer);s.remove();turnstilePromise=null;reject(Error('A verificação não carregou. Confira a conexão e tente novamente.'));};
   const timer=setTimeout(falhar,15000);s.onerror=falhar;s.onload=()=>{if(!global.turnstile){falhar();return;}clearTimeout(timer);resolve();};document.head.appendChild(s);
  });return turnstilePromise;
 }
 async function montar({obra,capitulo=null,destino}){
  if(!destino)return;
  const vez=++sequencia;
  if(widgetAtual!==null&&global.turnstile){try{global.turnstile.remove(widgetAtual);}catch{}widgetAtual=null;}
  destino.replaceChildren();destino.hidden=true;
  try{
   const resposta=await fetch('../configuracao-site.json');if(!resposta.ok)return;
   const config=await resposta.json();if(vez!==sequencia||!permitido(config,obra,capitulo))return;
   const pagina=identidade(config,obra,capitulo),base=apiUrl(config);destino.hidden=false;destino.classList.add('comentarios-literature');
   destino.append(criar('h2',capitulo?'Comentários do capítulo':'Conversa sobre a obra'));
   destino.append(criar('p',capitulo?'Pode haver spoilers deste capítulo. Evite revelar acontecimentos posteriores.':'Esta conversa geral pode conter spoilers de toda a obra.'));
   destino.append(criar('p','Os comentários são públicos após aprovação. O nome é informado pelo visitante, sem identidade verificada. Não publique dados pessoais.', 'comentarios-nota'));
   if(location.origin!==new URL(config.url_publica).origin||location.protocol!=='https:'){
    destino.append(criar('p','Comentários disponíveis no site publicado. A prévia local não envia mensagens reais.'));return;
   }
   const abrir=criar('button','Abrir comentários','btn-config');abrir.type='button';destino.append(abrir);
   const status=criar('p');status.setAttribute('role','status');destino.append(status);
   const area=criar('div');area.hidden=true;destino.append(area);
   async function request(path,options={}){
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
    try{const r=await fetch(base+path,{...options,signal:controller.signal,credentials:'omit'});const data=await r.json();if(!r.ok)throw Error(data.error||'Serviço temporariamente indisponível.');return data;}catch(e){if(e.name==='AbortError')throw Error('O serviço demorou a responder. Tente novamente.');throw e;}finally{clearTimeout(timer);}
   }
   let initialized=false,after=null,list,mais,form,author,message,parentId=null,reply,token='',widget=null,requestId=null,website;
   function limparResposta(){parentId=null;reply.textContent='';reply.hidden=true;requestId=null;}
   function renderComment(item){
    const card=criar('article',null,'comentario'+(item.parent_id?' comentario-resposta':''));
    const header=criar('div',null,'comentario-cabecalho');header.append(criar('strong',item.author));
    const time=criar('time',new Date(item.created_at).toLocaleString('pt-BR'));time.dateTime=new Date(item.created_at).toISOString();header.append(time);card.append(header);
    if(item.parent_id)card.append(criar('p',`Em resposta a ${item.reply_to||'um comentário anterior'}.`,'comentarios-nota'));
    card.append(criar('p',item.body,'comentario-texto'));
    if(!item.parent_id){const responder=criar('button','Responder','comentario-acao');responder.type='button';responder.onclick=()=>{parentId=item.id;requestId=null;reply.hidden=false;reply.textContent=`Respondendo a ${item.author}`;message.focus();};card.append(responder);}
    list.append(card);
   }
   async function carregar(reset=false){
    mais.disabled=true;status.textContent='Buscando comentários…';
    try{
     const query=new URLSearchParams({thread:pagina.identifier,after:String(reset?0:after||0),limit:'30'});const data=await request('/v1/comments?'+query);
     if(vez!==sequencia)return;
     if(reset)list.replaceChildren();for(const item of data.items)renderComment(item);after=data.next;mais.hidden=after===null;
     status.textContent=list.children.length?'Somente comentários aprovados são exibidos.':'Ainda não há comentários aprovados. Você pode iniciar a conversa.';
    }catch(e){if(vez===sequencia)status.textContent=e.message;}finally{mais.disabled=false;}
   }
   function formulario(){
    form=criar('form',null,'comentarios-form');form.append(criar('h3','Participar da conversa'));
    form.append(criar('p','Seu nome e texto ficam guardados para moderação. Para combater spam, o envio usa a verificação Cloudflare Turnstile e limites temporários por conexão. O endereço IP não é salvo junto ao comentário.','comentarios-nota'));
    const privacy=criar('a','Como tratamos os dados dos comentários');privacy.href='../privacidade.html';form.append(privacy);
    const field=(titulo,tag,max)=>{const label=criar('label',titulo),input=criar(tag);input.required=true;input.maxLength=max;label.append(input);form.append(label);return input;};
    author=field('Como você quer aparecer','input',60);author.minLength=2;author.autocomplete='nickname';
    reply=criar('p');reply.hidden=true;form.append(reply);const cancelar=criar('button','Cancelar resposta');cancelar.type='button';cancelar.onclick=limparResposta;form.append(cancelar);
    message=field('Seu comentário','textarea',2000);message.minLength=3;message.rows=5;
    const hp=criar('label','Deixe este campo vazio','comentarios-armadilha');hp.setAttribute('aria-hidden','true');website=criar('input');website.tabIndex=-1;website.autocomplete='off';hp.append(website);form.append(hp);
    const verifica=criar('div');form.append(verifica);const verificar=criar('button','Verificar para enviar');verificar.type='button';form.append(verificar);
    const enviar=criar('button','Enviar para aprovação','btn-config');enviar.type='submit';enviar.disabled=true;form.append(enviar);
    verificar.onclick=async()=>{
     verificar.disabled=true;status.textContent='Preparando verificação…';
     try{
      await carregarTurnstile();if(vez!==sequencia)return;
      if(widget!==null){global.turnstile.remove(widget);widget=null;}
      widget=global.turnstile.render(verifica,{sitekey:config.comentarios.turnstile_site_key,action:'comment',theme:'auto',callback:value=>{token=value;enviar.disabled=false;status.textContent='Verificação concluída. Seu comentário pode ser enviado.';},'expired-callback':()=>{token='';enviar.disabled=true;status.textContent='Refaça a verificação para enviar.';},'error-callback':()=>{token='';enviar.disabled=true;verificar.disabled=false;status.textContent='Não foi possível verificar. Tente novamente.';}});widgetAtual=widget;
     }catch(e){status.textContent=e.message;verificar.disabled=false;}
    };
    message.oninput=author.oninput=()=>{requestId=null;};
    form.onsubmit=async event=>{
     event.preventDefault();if(!token||!form.reportValidity())return;
     enviar.disabled=true;status.textContent='Enviando para moderação…';requestId=requestId||crypto.randomUUID();
     try{
      await request('/v1/comments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({thread:pagina.identifier,author:author.value.trim(),body:message.value.trim(),parent_id:parentId,request_id:requestId,website:website.value,turnstile_token:token})});
      if(vez!==sequencia)return;
      message.value='';limparResposta();status.textContent='Comentário recebido! Ele ficará visível depois da aprovação.';
     }catch(e){if(vez===sequencia)status.textContent=e.message;}finally{token='';if(vez===sequencia&&widget!==null)global.turnstile.reset(widget);verificar.disabled=false;}
    };
    area.append(form);
   }
   abrir.onclick=async()=>{
    abrir.disabled=true;
    try{
     if(!initialized){initialized=true;area.hidden=false;list=criar('div',null,'comentarios-lista');area.append(list);mais=criar('button','Carregar mais');mais.type='button';mais.hidden=true;mais.onclick=()=>carregar(false);area.append(mais);formulario();abrir.textContent='Atualizar comentários';}
     await carregar(true);
    }finally{abrir.disabled=false;}
   };
  }catch{destino.hidden=true;}
 }
 global.ComentariosLiterature={montar,permitido,identidade};
})(window);

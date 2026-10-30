const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
class Elemento{
 constructor(tag){this.tag=tag;this.children=[];this.hidden=false;this.value='';this.classList={add(){}};this.attrs={};}
 append(...e){this.children.push(...e);} appendChild(e){this.append(e);return e;} replaceChildren(...e){this.children=e;} setAttribute(k,v){this.attrs[k]=v;} remove(){} focus(){this.focused=true;} reportValidity(){return true;}
 set innerHTML(_){throw Error('Não renderize conteúdo de visitantes como HTML');}
}
const all=w=>[w,...w.children.flatMap(all)];
(async()=>{
 let config={schema_version:2,url_publica:'https://literatura.roger.cardoso.nom.br',comentarios:{ativado:true,api_url:'https://comments.example',turnstile_site_key:'public-site-key',obras:true,capitulos:true}};
 let posts=[],reads=0,fail=false,challenge=null,resets=0;
 const head=new Elemento('head'),ctx={window:{},document:{createElement:t=>new Elemento(t),head},location:{origin:config.url_publica,protocol:'https:'},URL,URLSearchParams,AbortController,setTimeout,clearTimeout,crypto,fetch:async(url,opts={})=>{
  if(url==='../configuracao-site.json')return {ok:true,json:async()=>config};
  if(opts.method==='POST'){posts.push(JSON.parse(opts.body));return {ok:!fail,json:async()=>fail?{error:'Falha simulada'}:{status:'pending'}};}
  reads++;return {ok:true,json:async()=>({items:[{id:'root-comment',author:'Leitor',body:'<script>não executar</script>',created_at:1700000000000,parent_id:null}],next:null})};
 }};vm.createContext(ctx);vm.runInContext(fs.readFileSync('js-global/comentarios.js','utf8'),ctx);
 const api=ctx.window.ComentariosLiterature,obra={id_obra:'obra-uuid',slug:'minha-obra',titulo:'Título'},cap={id:'cap-uuid',titulo:'Capítulo'},destino=new Elemento('section');
 const a=api.identidade(config,obra,cap),b=api.identidade(config,{...obra,titulo:'Outro título',slug:'outro-endereco'},cap);assert.equal(a.identifier,b.identifier);assert.equal(a.url,config.url_publica+'/minha-obra/leitor.html?id=cap-uuid');
 assert.equal(api.permitido(config,{...obra,comentarios:'desativado'},{...cap,comentarios:'ativado'}),false);config.comentarios.capitulos=false;assert.equal(api.permitido(config,obra,cap),false);assert.equal(api.permitido(config,obra,{...cap,comentarios:'ativado'}),true);config.comentarios.capitulos=true;
 await api.montar({obra,capitulo:cap,destino});assert.equal(destino.hidden,false);assert.equal(reads,0);assert.equal(head.children.length,0,'Nenhuma conexão externa antes do clique');
 await all(destino).find(e=>e.tag==='button'&&e.textContent==='Abrir comentários').onclick();assert.equal(reads,1);assert.equal(head.children.length,0,'Abrir conversa não carrega Turnstile');
 assert.ok(all(destino).some(e=>e.textContent==='<script>não executar</script>'));
 ctx.window.turnstile={render(_e,options){challenge=options;options.callback('verified');return 'widget-id';},reset(){resets++;},remove(){}};
 await all(destino).find(e=>e.textContent==='Verificar para enviar').onclick();assert.equal(challenge.action,'comment');assert.equal(challenge.sitekey,'public-site-key');
 const form=all(destino).find(e=>e.tag==='form'),inputs=all(form).filter(e=>e.tag==='input'),message=all(form).find(e=>e.tag==='textarea');inputs[0].value='Ana';message.value='Meu comentário';
 all(destino).find(e=>e.textContent==='Responder').onclick();fail=true;await form.onsubmit({preventDefault(){}});assert.equal(message.value,'Meu comentário','Falha não apaga texto');
 const first=posts[0].request_id;challenge.callback('another-token');fail=false;await form.onsubmit({preventDefault(){}});assert.equal(posts[1].request_id,first,'Nova tentativa usa a mesma identidade');assert.equal(posts[1].thread,a.identifier);assert.equal(posts[1].parent_id,'root-comment');assert.equal(message.value,'');assert.equal(resets,2);
 assert.ok(all(destino).some(e=>e.textContent?.includes('depois da aprovação')));assert.equal(reads,1,'Envio não finge aprovação nem injeta comentário público');
 ctx.location.origin='http://localhost:8765';ctx.location.protocol='http:';await api.montar({obra,capitulo:cap,destino});assert.equal(all(destino).some(e=>e.tag==='button'),false);assert.equal(reads,1);
 config.comentarios.ativado=false;await api.montar({obra,destino});assert.equal(destino.hidden,true);
 console.log('Comentários próprios: IDs e herança; carregamento por clique; texto literal seguro; resposta; verificação; envio pendente; falha preserva rascunho; idempotência; prévia isolada: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});

const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
class Elemento{
 constructor(tag){this.tag=tag;this.children=[];this.hidden=false;this.value='';this.attrs={};this.classList={add(){}};}
 append(...es){this.children.push(...es);}replaceChildren(...es){this.children=es;}setAttribute(k,v){this.attrs[k]=v;}
 set innerHTML(_){throw Error('Conteúdo deve ser texto literal.');}
}
const all=e=>[e,...e.children.flatMap(all)];
(async()=>{
 const storage=new Map(),config={url_publica:'https://literatura.roger.cardoso.nom.br',comentarios:{ativado:false,api_url:'https://comments.example',turnstile_site_key:'public-key'},reacoes:{ativado:true,obras:true,capitulos:true}};
 let mine=0,verified=false,challengeCalls=0,writes=[],gate=null,blocked=false,paused=false,fail=false;
 const ctx={window:{localStorage:{getItem:k=>{if(blocked)throw Error();return storage.get(k)||null;},setItem:(k,v)=>{if(blocked)throw Error();storage.set(k,v);}},turnstile:{render(el,options){assert.equal(options.action,'reaction');challengeCalls++;options.callback('valid-token');return 'reaction-widget';},remove(){}},ComentariosLiterature:{identidade:(c,o,cap)=>({identifier:JSON.stringify(['literature',o.id_obra,cap?.id||null])}),carregarVerificacao:async()=>{}}},document:{createElement:t=>new Elemento(t)},location:{origin:config.url_publica,protocol:'https:'},URL,URLSearchParams,AbortController,setTimeout,clearTimeout,crypto,fetch:async(url,options={})=>{
  if(url==='../configuracao-site.json'){assert.equal(options.cache,'no-store','Configuração atual é consultada sem usar cópia antiga');return {ok:true,json:async()=>config};}
  const body=options.body?JSON.parse(options.body):null;
  if(url.endsWith('/state'))return {ok:true,json:async()=>({likes:mine===1?1:0,dislikes:mine===-1?1:0,mine,can_vote:verified,paused})};
  if(options.method==='POST'){
   writes.push(body);if(gate)await gate;
   if(fail)return {ok:false,json:async()=>({error:'Falha simulada'})};
   if(!verified&&body.turnstile_token!=='valid-token')return {ok:false,json:async()=>({error:'Verifique',code:'verification_required'})};verified=true;mine=body.value;
  }
  return {ok:true,json:async()=>({likes:mine===1?1:0,dislikes:mine===-1?1:0,...(body?{mine,can_vote:verified}:{}),paused})};
 }};vm.createContext(ctx);vm.runInContext(fs.readFileSync('js-global/reacoes.js','utf8'),ctx);
 const api=ctx.window.ReacoesLiterature,obra={id_obra:'obra',reacoes:'herdar'},cap={id:'cap'},root=new Elemento('section');
 assert.equal(api.permitido(config,obra,cap),true,'Independente dos comentários');assert.equal(api.permitido(config,{...obra,reacoes:'desativado'},{...cap,reacoes:'ativado'}),false);
 await api.montar({obra,capitulo:cap,destino:root});assert.equal(root.hidden,false);assert.equal(writes.length,0);assert.equal(storage.size,0,'Não cria identificação antes da interação');assert.equal(challengeCalls,0);
 let likes=all(root).find(e=>e.tag==='button'&&e.textContent.startsWith('Gostei')),dislikes=all(root).find(e=>e.tag==='button'&&e.textContent.startsWith('Não gostei'));
 await likes.onclick();assert.equal(writes.at(-1).value,1);assert.equal(likes.attrs['aria-pressed'],'true');assert.equal(likes.textContent,'Gostei · 1');assert.equal(challengeCalls,1);const visitor=writes[0].visitor;
 await dislikes.onclick();assert.equal(mine,-1);assert.equal(challengeCalls,1,'Reutiliza a verificação válida');assert.equal(writes.at(-1).visitor,visitor);assert.equal(dislikes.attrs['aria-pressed'],'true');
 await dislikes.onclick();assert.equal(mine,0);assert.equal(writes.at(-1).value,0);
 let release;gate=new Promise(r=>release=r);const primeiro=likes.onclick();await Promise.resolve();await dislikes.onclick();release();await primeiro;gate=null;assert.equal(mine,1,'Bloqueia cliques concorrentes');
 await api.montar({obra,capitulo:cap,destino:root});likes=all(root).find(e=>e.tag==='button'&&e.textContent.startsWith('Gostei'));assert.equal(likes.attrs['aria-pressed'],'true','Recupera estado do serviço');
 fail=true;await likes.onclick();assert.equal(likes.attrs['aria-pressed'],'true','Falha não finge alterar o voto');assert.ok(all(root).some(e=>e.textContent==='Falha simulada'));fail=false;
 blocked=true;await likes.onclick();assert.ok(all(root).some(e=>e.textContent?.includes('permita o armazenamento local')));blocked=false;
 paused=true;await api.montar({obra,capitulo:cap,destino:root});assert.equal(all(root).find(e=>e.textContent?.startsWith('Gostei')).disabled,true);
 ctx.location.origin='http://localhost:8765';ctx.location.protocol='http:';const count=writes.length;await api.montar({obra,destino:root});assert.equal(all(root).filter(e=>e.tag==='button').length,0);assert.equal(writes.length,count);
 config.reacoes.ativado=false;await api.montar({obra,destino:root});assert.equal(root.hidden,true);
 console.log('Reações: independência, identidade local, verificação, voto/troca/remoção, consulta autoritativa, cliques concorrentes, falhas, pausa e prévia isolada: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});

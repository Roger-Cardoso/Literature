const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Elemento{
 constructor(tag){this.tag=tag;this.children=[];this.hidden=false;this.classList={add(){}};this.attrs={};}
 append(...e){this.children.push(...e);} appendChild(e){this.append(e);return e;} replaceChildren(...e){this.children=e;} setAttribute(k,v){this.attrs[k]=v;}
 querySelector(s){return this.children.find(e=>s==='#disqus_thread'&&e.id==='disqus_thread')||null;} remove(){}
}
(async()=>{
 let config={url_publica:'https://literatura.roger.cardoso.nom.br',disqus:{ativado:true,shortname:'literature-teste',obras:true,capitulos:true}};
 const head=new Elemento('head'),ctx={window:{},document:{createElement:t=>new Elemento(t),head},location:{origin:'https://literatura.roger.cardoso.nom.br',protocol:'https:'},URL,setTimeout,clearTimeout,fetch:async()=>({ok:true,json:async()=>config})};vm.createContext(ctx);vm.runInContext(fs.readFileSync('js-global/comentarios.js','utf8'),ctx);
 const api=ctx.window.ComentariosLiterature,obra={id_obra:'obra-uuid',slug:'minha-obra',titulo:'Título'},cap={id:'cap-uuid',titulo:'Capítulo'},destino=new Elemento('section');
 const a=api.identidade(config,obra,cap),b=api.identidade(config,{...obra,titulo:'Título novo',slug:'outro-endereco'},{...cap,titulo:'Outro título'});
 assert.equal(a.identifier,b.identifier);assert.equal(a.url,'https://literatura.roger.cardoso.nom.br/minha-obra/leitor.html?id=cap-uuid');assert.notEqual(a.identifier,api.identidade(config,obra).identifier);
 assert.equal(api.permitido(config,{...obra,comentarios:'desativado'}, {...cap,comentarios:'ativado'}),false);
 assert.equal(api.permitido(config,obra,{...cap,comentarios:'desativado'}),false);
 config.disqus.capitulos=false;assert.equal(api.permitido(config,obra,cap),false);assert.equal(api.permitido(config,obra,{...cap,comentarios:'ativado'}),true);config.disqus.capitulos=true;
 await api.montar({obra,capitulo:cap,destino});assert.equal(destino.hidden,false);assert.equal(head.children.length,0,'Nenhum embed antes do clique');
 const botao=destino.children.find(e=>e.tag==='button');const carregando=botao.onclick();assert.equal(head.children.length,1);assert.equal(head.children[0].src,'https://literature-teste.disqus.com/embed.js');
 const contexto={page:{}};ctx.window.disqus_config.call(contexto);assert.equal(contexto.page.identifier,a.identifier);assert.equal(contexto.page.url,a.url);assert.equal(contexto.language,'pt_BR');
 head.children[0].onerror();await carregando;assert.equal(botao.disabled,false);assert.match(botao.textContent,/novamente/);
 const repetir=botao.onclick();head.children[1].onload();await repetir;assert.equal(botao.hidden,true);
 let reset;ctx.window.DISQUS={reset:v=>{reset=v;}};await api.montar({obra,capitulo:{...cap,id:'outro-capitulo'},destino});await destino.children.find(e=>e.tag==='button').onclick();const segunda={page:{}};reset.config.call(segunda);assert.notEqual(segunda.page.identifier,a.identifier);assert.match(segunda.page.url,/id=outro-capitulo/);assert.equal(reset.reload,true);
 ctx.location.origin='http://localhost:8765';ctx.location.protocol='http:';await api.montar({obra,capitulo:cap,destino});assert.equal(destino.children.some(e=>e.tag==='button'),false,'Prévia não conecta ao Disqus');
 config.disqus.ativado=false;await api.montar({obra,destino});assert.equal(destino.hidden,true);config.disqus.ativado=true;config.disqus.shortname='x.example/ataque';await api.montar({obra,destino});assert.equal(destino.hidden,true);
 console.log('Comentários: IDs estáveis; URL canônica por capítulo; herança e bloqueios; carregamento por clique; falha e nova tentativa; troca de discussão; prévia isolada; shortname inválido recusado: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});

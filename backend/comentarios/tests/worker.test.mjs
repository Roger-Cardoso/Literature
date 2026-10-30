import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {createWorker} from '../src/worker.mjs';
class D1 {
 constructor(){this.sql=new DatabaseSync(':memory:');for(const file of readdirSync(new URL('../migrations/',import.meta.url)).filter(f=>f.endsWith('.sql')).sort())this.sql.exec(readFileSync(new URL('../migrations/'+file,import.meta.url),'utf8'));}
 prepare(sql){const db=this;return {values:[],bind(...values){this.values=values;return this;},async first(){return db.sql.prepare(sql).get(...this.values)||null;},async all(){return {results:db.sql.prepare(sql).all(...this.values)};},async run(){const r=db.sql.prepare(sql).run(...this.values);return {meta:{changes:r.changes}};}};}
 async batch(statements){this.sql.exec('BEGIN');try{const r=[];for(const s of statements)r.push(await s.run());this.sql.exec('COMMIT');return r;}catch(e){this.sql.exec('ROLLBACK');throw e;}}
}
const ORIGIN='https://literatura.roger.cardoso.nom.br',thread=JSON.stringify(['literature','obra-1','cap-1']);
async function fixture(){
 let time=1700000000000;
 const env={DB:new D1(),SITE_ORIGIN:ORIGIN,ADMIN_TOKEN:'a'.repeat(40),IP_HASH_SECRET:'b'.repeat(40),TURNSTILE_SECRET_KEY:'private-secret'};
 const worker=createWorker({verify:async token=>token==='valid-token',now:()=>time});
 async function call(path,method='GET',data=null,admin=false,extra={}){
  const headers={Origin:ORIGIN,...(data?{'Content-Type':'application/json'}:{}),...(admin?{Authorization:'Bearer '+env.ADMIN_TOKEN}:{}),'CF-Connecting-IP':'203.0.113.10',...extra};
  return worker.fetch(new Request('https://comments.example'+path,{method,headers,body:data?JSON.stringify(data):undefined}),env);
 }
 const generation=crypto.randomUUID();await call('/v1/admin/threads','POST',{generation,threads:[{id:thread,title:'Capítulo',url:ORIGIN+'/obra-1/leitor.html?id=cap-1'}]},true);assert.equal((await call('/v1/admin/threads/commit','POST',{generation,total:1},true)).status,200);
 const submit=(changes={})=>call('/v1/comments','POST',{thread,author:'Leitor',body:'Comentário de teste.',request_id:crypto.randomUUID(),turnstile_token:'valid-token',...changes});
 const all=()=>call('/v1/admin/comments?status=all','GET',null,true).then(r=>r.json());
 const publicComments=()=>call('/v1/comments?thread='+encodeURIComponent(thread)).then(r=>r.json());
 return {worker,env,call,submit,all,publicComments,advance:ms=>{time+=ms;}};
}
test('envios pendentes são privados; aprovação, ocultação e exclusão autenticadas',async()=>{
 const f=await fixture();assert.equal((await f.submit()).status,202);assert.equal((await f.publicComments()).items.length,0);
 const item=(await f.all()).items[0];assert.equal(item.status,'pending');assert.ok(!('ip' in item));
 assert.equal((await f.call('/v1/admin/comments/'+item.id,'PATCH',{status:'approved'})).status,401);
 assert.equal((await f.call('/v1/admin/comments/'+item.id,'PATCH',{status:'approved'},true)).status,200);assert.equal((await f.publicComments()).items[0].body,item.body);
 await f.call('/v1/admin/comments/'+item.id,'PATCH',{status:'hidden'},true);assert.equal((await f.publicComments()).items.length,0);
 await f.call('/v1/admin/comments/'+item.id,'DELETE',null,true);assert.equal((await f.all()).items.length,0);
});
test('respostas só ao mesmo tópico e a comentários raiz aprovados; ocultação e cascata',async()=>{
 const f=await fixture();await f.submit();const root=(await f.all()).items[0];
 assert.equal((await f.submit({parent_id:root.id})).status,400);await f.call('/v1/admin/comments/'+root.id,'PATCH',{status:'approved'},true);
 assert.equal((await f.submit({parent_id:root.id})).status,202);const reply=(await f.all()).items[1];await f.call('/v1/admin/comments/'+reply.id,'PATCH',{status:'approved'},true);
 assert.equal((await f.publicComments()).items.length,2);assert.equal((await f.submit({parent_id:reply.id})).status,400);
 await f.call('/v1/admin/comments/'+root.id,'PATCH',{status:'hidden'},true);assert.equal((await f.publicComments()).items.length,0);
 await f.call('/v1/admin/comments/'+root.id,'DELETE',null,true);assert.equal((await f.all()).items.length,0);
});
test('origens, verificação, armadilha e tópicos não publicados são recusados',async()=>{
 const f=await fixture();assert.equal((await f.call('/v1/comments','POST',{},false,{Origin:'https://outro.example'})).status,403);
 assert.equal((await f.submit({turnstile_token:'invalid'})).status,403);assert.equal((await f.submit({website:'spam'})).status,400);
 assert.equal((await f.submit({thread:JSON.stringify(['literature','rascunho',null])})).status,404);assert.equal((await f.submit({author:'a'})).status,400);
 const pre=await f.call('/v1/comments','OPTIONS');assert.equal(pre.status,204);assert.equal(pre.headers.get('Access-Control-Allow-Origin'),ORIGIN);
 const blocked=await f.call('/v1/comments','OPTIONS',null,false,{Origin:'https://outro.example'});assert.equal(blocked.headers.has('Access-Control-Allow-Origin'),false);
});
test('idempotência evita duplicação e não permite reutilizar UUID com outro texto',async()=>{
 const f=await fixture(),id=crypto.randomUUID();assert.equal((await f.submit({request_id:id})).status,202);assert.equal((await f.submit({request_id:id})).status,202);
 assert.equal((await f.submit({request_id:id,body:'Outro texto'})).status,409);assert.equal((await f.all()).items.length,1);
});
test('limite por conexão é atômico e expira por janela; IP não fica em claro',async()=>{
 const f=await fixture();const responses=await Promise.all(Array.from({length:6},()=>f.submit()));assert.equal(responses.filter(r=>r.status===202).length,5);assert.equal(responses.filter(r=>r.status===429).length,1);
 const rate=await f.env.DB.prepare('SELECT * FROM rate_limits').first();assert.match(rate.key,/^[a-f0-9]{64}$/);assert.ok(!JSON.stringify(rate).includes('203.0.113'));
 f.advance(600001);assert.equal((await f.submit()).status,202);
});
test('sincronização incompleta não substitui geração ativa; commit fecha tópicos antigos',async()=>{
 const f=await fixture(),generation=crypto.randomUUID();assert.equal((await f.call('/v1/admin/threads','POST',{generation,threads:[]},true)).status,200);
 assert.equal((await f.call('/v1/admin/threads/commit','POST',{generation,total:1},true)).status,409);assert.equal((await f.call('/v1/comments?thread='+encodeURIComponent(thread))).status,200);
 await f.call('/v1/admin/threads/commit','POST',{generation,total:0},true);assert.equal((await f.call('/v1/comments?thread='+encodeURIComponent(thread))).status,404);
});
test('paginação, exportação privada e SQL parametrizado preservam texto literal',async()=>{
 const f=await fixture();await f.submit({body:"<script>alert('x')</script> -- DROP TABLE comments;"});await f.submit();
 const page1=await f.call('/v1/admin/comments?status=all&limit=1','GET',null,true).then(r=>r.json());assert.equal(page1.items.length,1);assert.ok(page1.next);
 const page2=await f.call('/v1/admin/comments?status=all&limit=1&after='+page1.next,'GET',null,true).then(r=>r.json());assert.equal(page2.items.length,1);assert.notEqual(page1.items[0].id,page2.items[0].id);
 assert.equal((await f.call('/v1/admin/comments?status=all')).status,401);assert.equal((await f.call('/v1/comments?thread='+encodeURIComponent(thread)+'&after=-1')).status,400);
});
test('corpos grandes, JSON inválido e erro interno não expõem detalhes',async()=>{
 const f=await fixture();assert.equal((await f.submit({body:'x'.repeat(20000)})).status,413);
 const bad=new Request('https://comments.example/v1/comments',{method:'POST',headers:{Origin:ORIGIN,'Content-Type':'application/json'},body:'{'});assert.equal((await createWorker().fetch(bad,f.env)).status,400);
 f.env.DB.prepare=()=>{throw Error('private connection details');};const r=await f.call('/v1/admin/comments','GET',null,true);assert.equal(r.status,503);assert.ok(!(await r.text()).includes('private connection'));
});

test('validação real de Turnstile exige hostname e ação corretos',async()=>{
 const f=await fixture(),original=globalThis.fetch;let resultado={success:true,hostname:'outro.example',action:'comment'};
 globalThis.fetch=async(url,options)=>{assert.equal(url,'https://challenges.cloudflare.com/turnstile/v0/siteverify');assert.equal(options.body.get('secret'),f.env.TURNSTILE_SECRET_KEY);return {ok:true,json:async()=>resultado};};
 const req=()=>new Request('https://comments.example/v1/comments',{method:'POST',headers:{Origin:ORIGIN,'Content-Type':'application/json','CF-Connecting-IP':'203.0.113.10'},body:JSON.stringify({thread,author:'Leitor',body:'Texto verificado',request_id:crypto.randomUUID(),turnstile_token:'valid-token'})});
 try{
  assert.equal((await createWorker().fetch(req(),f.env)).status,403);
  resultado={success:true,hostname:new URL(ORIGIN).hostname,action:'outra'};assert.equal((await createWorker().fetch(req(),f.env)).status,403);
  resultado.action='comment';assert.equal((await createWorker().fetch(req(),f.env)).status,202);
 }finally{globalThis.fetch=original;}
});
test('limpeza remove limites expirados e preserva geração ativa e comentários',async()=>{
 const f=await fixture();await f.submit();f.advance(2*86400000);let limpeza;await f.worker.scheduled({},f.env,{waitUntil(p){limpeza=p;}});await limpeza;
 assert.equal((await f.env.DB.prepare('SELECT COUNT(*) AS n FROM rate_limits').first()).n,0);assert.equal((await f.all()).items.length,1);assert.equal((await f.publicComments()).items.length,0);
});

test('serviço público recusa HTTP sem TLS',async()=>{
 const f=await fixture();const r=await f.worker.fetch(new Request('http://comments.example/v1/health'),f.env);assert.equal(r.status,400);
});

test('spoilers, herança de respostas e classificação sem alterar estado',async()=>{
 const f=await fixture();const requestId=crypto.randomUUID();await f.submit({spoiler:true,request_id:requestId});const root=(await f.all()).items[0];
 await f.call('/v1/admin/comments/'+root.id,'PATCH',{status:'approved'},true);await f.submit({parent_id:root.id});const reply=(await f.all()).items[1];await f.call('/v1/admin/comments/'+reply.id,'PATCH',{status:'approved'},true);
 assert.ok((await f.publicComments()).items.every(i=>i.spoiler===1));assert.equal((await f.publicComments()).total,2);
 await f.call('/v1/admin/comments/'+root.id,'PATCH',{spoiler:false},true);assert.equal((await f.all()).items[0].status,'approved');assert.equal((await f.submit({spoiler:true,request_id:requestId})).status,202,'Revisão do moderador não muda a identidade do envio');
 assert.equal((await f.submit({spoiler:false,request_id:requestId})).status,409);assert.equal((await f.submit({spoiler:'false'})).status,400);
});
test('busca e discussão filtradas no servidor; busca trata texto literalmente',async()=>{
 const f=await fixture();await f.submit({author:'Ana',body:'A passagem de 100% foi ótima.'});await f.submit({author:'Bia'});
 const query='/v1/admin/comments?status=all&q='+encodeURIComponent('100%');assert.equal((await f.call(query,'GET',null,true).then(r=>r.json())).items.length,1);
 const outro=JSON.stringify(['literature','outra',null]);assert.equal((await f.call('/v1/admin/comments?status=all&thread='+encodeURIComponent(outro),'GET',null,true).then(r=>r.json())).items.length,0);
});
test('migração preserva mensagens anteriores com proteção inicialmente desmarcada',()=>{
 const sql=new DatabaseSync(':memory:');sql.exec(readFileSync(new URL('../migrations/0001_comments.sql',import.meta.url),'utf8'));
 sql.prepare("INSERT INTO comments(id,request_id,thread_id,author,body,status,created_at,updated_at) VALUES (?,?,?,?,?,'approved',?,?)").run(crypto.randomUUID(),crypto.randomUUID(),thread,'Ana','Mensagem anterior à atualização',1700000000000,1700000000000);
 const antes=sql.prepare('SELECT * FROM comments').get();sql.exec(readFileSync(new URL('../migrations/0002_spoilers.sql',import.meta.url),'utf8'));const depois=sql.prepare('SELECT * FROM comments').get();
 for(const key of Object.keys(antes))assert.equal(depois[key],antes[key]);assert.equal(depois.spoiler,0);assert.equal(depois.submitted_spoiler,0);sql.close();
});
async function reactionsFixture(){
 const f=await fixture(),generation=crypto.randomUUID();
 await f.call('/v1/admin/threads','POST',{generation,threads:[{id:thread,title:'Capítulo com reações',url:ORIGIN+'/obra-1/leitor.html?id=cap-1',comments_enabled:false,reactions_enabled:true}]},true);
 await f.call('/v1/admin/threads/commit','POST',{generation,total:1},true);
 const visitor=crypto.randomUUID();const vote=(value,extra={})=>f.call('/v1/reactions','POST',{thread,visitor,value,turnstile_token:'valid-token',...extra});
 const totals=()=>f.call('/v1/reactions?thread='+encodeURIComponent(thread)).then(r=>r.json());
 return {...f,visitor,vote,totals};
}
test('reações: um voto, repetição idempotente, troca, remoção e contadores transacionais',async()=>{
 const f=await reactionsFixture();assert.equal((await f.publicComments()).error,'Discussão indisponível.');assert.equal((await f.submit()).status,404,'Reações não habilitam comentários');
 assert.equal((await f.vote(1)).status,200);assert.equal((await f.vote(1)).status,200);assert.deepEqual(await f.totals(),{likes:1,dislikes:0,paused:false});
 const id=crypto.randomUUID();await f.vote(-1,{visitor:id});assert.deepEqual(await f.totals(),{likes:1,dislikes:1,paused:false});
 await f.vote(-1);assert.deepEqual(await f.totals(),{likes:0,dislikes:2,paused:false});await f.vote(0);await f.vote(0);assert.deepEqual(await f.totals(),{likes:0,dislikes:1,paused:false});
 const state=await f.call('/v1/reactions/state','POST',{thread,visitor:id}).then(r=>r.json());assert.equal(state.mine,-1);assert.equal(state.can_vote,true);
 const rows=f.env.DB.sql.prepare('SELECT * FROM reactions').all();assert.equal(rows.length,1);assert.ok(!JSON.stringify(rows).includes(id));assert.ok(!JSON.stringify(rows).includes('203.0.113.10'));
});
test('reações: verificação por conexão expira e não vale para outro visitante',async()=>{
 const f=await reactionsFixture();assert.equal((await f.vote(1,{turnstile_token:null})).status,403);assert.equal((await f.vote(1,{turnstile_token:'invalid'})).status,403);assert.equal((await f.vote(1)).status,200);
 assert.equal((await f.vote(-1,{turnstile_token:null})).status,200);assert.equal((await f.vote(1,{visitor:crypto.randomUUID(),turnstile_token:null})).status,403);
 const otherIP=await f.call('/v1/reactions','POST',{thread,visitor:f.visitor,value:1},false,{'CF-Connecting-IP':'203.0.113.11'});assert.equal(otherIP.status,403);
 f.advance(600001);assert.equal((await f.vote(1,{turnstile_token:null})).status,403);
});
test('reações: pausa, autenticação, catálogo independente e retenção após desativação',async()=>{
 const f=await reactionsFixture();await f.vote(1);assert.equal((await f.call('/v1/admin/reactions','PATCH',{thread,paused:true})).status,401);
 await f.call('/v1/admin/reactions','PATCH',{thread,paused:true},true);assert.equal((await f.vote(-1)).status,409);assert.equal((await f.totals()).likes,1);assert.equal((await f.totals()).paused,true);
 await f.call('/v1/admin/reactions','PATCH',{thread,paused:false},true);assert.equal((await f.vote(-1)).status,200);
 const generation=crypto.randomUUID();await f.call('/v1/admin/threads','POST',{generation,threads:[{id:thread,title:'Renomeado',url:ORIGIN+'/obra-1/index-obra.html',reactions_enabled:false}]},true);await f.call('/v1/admin/threads/commit','POST',{generation,total:1},true);
 assert.equal((await f.call('/v1/reactions?thread='+encodeURIComponent(thread))).status,404);assert.equal((await f.vote(1)).status,404);
 const admin=await f.call('/v1/admin/reactions?q=renomeado','GET',null,true).then(r=>r.json());assert.equal(admin.items[0].dislikes,1);assert.equal(admin.items[0].reactions_enabled,0);assert.ok(!JSON.stringify(admin).includes(f.visitor));
});
test('reações: valores e origem inválidos, limite por conexão e ação específica Turnstile',async()=>{
 const f=await reactionsFixture();for(const value of [2,'1',null,true])assert.equal((await f.vote(value)).status,400);
 assert.equal((await f.call('/v1/reactions','POST',{thread,visitor:f.visitor,value:1},false,{Origin:'https://outro.example'})).status,403);
 for(let i=0;i<60;i++)assert.equal((await f.vote(i%2?1:-1)).status,200);assert.equal((await f.vote(1)).status,429);
 const other=await reactionsFixture();let action;const worker=createWorker({verify:async(_t,_ip,_env,a)=>{action=a;return true;}});
 await worker.fetch(new Request('https://comments.example/v1/reactions',{method:'POST',headers:{Origin:ORIGIN,'Content-Type':'application/json','CF-Connecting-IP':'203.0.113.10'},body:JSON.stringify({thread,visitor:other.visitor,value:1,turnstile_token:'token'})}),other.env);assert.equal(action,'reaction');
});
test('migração de reações não altera os comentários e conserva compatibilidade das discussões',()=>{
 const db=new DatabaseSync(':memory:');for(const name of ['0001_comments.sql','0002_spoilers.sql'])db.exec(readFileSync(new URL('../migrations/'+name,import.meta.url),'utf8'));
 const generation=crypto.randomUUID();db.prepare('INSERT INTO generations VALUES (?,?)').run(generation,1);db.prepare('INSERT INTO threads VALUES (?,?,?,?)').run(generation,thread,'Capítulo',ORIGIN+'/obra');
 db.exec(readFileSync(new URL('../migrations/0003_reactions.sql',import.meta.url),'utf8'));const row=db.prepare('SELECT * FROM threads').get();assert.equal(row.comments_enabled,1);assert.equal(row.reactions_enabled,0);db.close();
});

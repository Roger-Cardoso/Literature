import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createWorker} from '../src/worker.mjs';
class D1 {
 constructor(){this.sql=new DatabaseSync(':memory:');this.sql.exec(readFileSync(new URL('../migrations/0001_comments.sql',import.meta.url),'utf8'));}
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

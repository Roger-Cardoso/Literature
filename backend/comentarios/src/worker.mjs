/* Comments are plain text; all submissions require approval. Secrets never leave the Worker. */
const MAX_BODY = 16384;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const ACTIVE = "(SELECT value FROM site_state WHERE key='active_generation')";
class ApiError extends Error { constructor(status,message){super(message);this.status=status;} }
const reject=(status,message)=>{throw new ApiError(status,message);};
const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const text=(v,min,max,label)=>{if(typeof v!=='string')reject(400,`${label} inválido.`);v=v.trim();if(v.length<min||v.length>max||/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(v))reject(400,`${label} deve ter entre ${min} e ${max} caracteres.`);return v;};
const uuid=(v)=>{if(typeof v!=='string'||!UUID.test(v))reject(400,'Identificador inválido.');return v;};
function threadId(value){
    const id=text(value,1,512,'Discussão');
    let parts;try{parts=JSON.parse(id);}catch{reject(400,'Discussão inválida.');}
    if(!Array.isArray(parts)||parts.length!==3||parts[0]!=='literature'||typeof parts[1]!=='string'||!parts[1]||parts[1].length>180||(parts[2]!==null&&(typeof parts[2]!=='string'||!parts[2]||parts[2].length>180)))reject(400,'Discussão inválida.');
    return JSON.stringify(parts);
}
async function body(request){
    if(!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json'))reject(415,'Envie JSON.');
    if(Number(request.headers.get('Content-Length'))>MAX_BODY)reject(413,'Mensagem muito grande.');
    const reader=request.body?.getReader();if(!reader)reject(400,'Corpo vazio.');let size=0;const chunks=[];
    while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>MAX_BODY){await reader.cancel();reject(413,'Mensagem muito grande.');}chunks.push(value);}
    const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
    let result;try{result=JSON.parse(new TextDecoder().decode(bytes));}catch{reject(400,'JSON inválido.');}
    if(!result||typeof result!=='object'||Array.isArray(result))reject(400,'Objeto JSON esperado.');return result;
}
function page(url){
    const raw=url.searchParams.get('after')||'0',limit=url.searchParams.get('limit')||'30';
    if(!/^\d{1,15}$/.test(raw)||!/^\d{1,3}$/.test(limit)||Number(limit)<1||Number(limit)>100)reject(400,'Paginação inválida.');
    return {after:Number(raw),limit:Number(limit)};
}
async function equalSecret(input,secret){
    if(!input||!secret||secret.length<32)return false;
    const hash=async s=>new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)));
    const [a,b]=await Promise.all([hash(input),hash(secret)]);let diff=0;for(let i=0;i<a.length;i++)diff|=a[i]^b[i];return diff===0;
}
async function ipKey(ip,window,secret){
    const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);
    return [...new Uint8Array(await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(`${window}:${ip}`)))].map(x=>x.toString(16).padStart(2,'0')).join('');
}
async function verifyTurnstile(token,ip,env){
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
    try{
        const response=await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify',{method:'POST',body:new URLSearchParams({secret:env.TURNSTILE_SECRET_KEY,response:token,remoteip:ip}),signal:controller.signal});
        if(!response.ok)reject(503,'A verificação está indisponível. Tente novamente.');
        const result=await response.json();return result.success===true&&result.hostname===new URL(env.SITE_ORIGIN).hostname&&result.action==='comment';
    }finally{clearTimeout(timer);}
}
const known=async(db,id)=>db.prepare(`SELECT id FROM threads WHERE generation=${ACTIVE} AND id=?`).bind(id).first();
export function createWorker({verify=verifyTurnstile,now=()=>Date.now()}={}){
 return {
  async fetch(request,env){
    const origin=request.headers.get('Origin');let site;
    try{site=new URL(env.SITE_ORIGIN);if(site.origin!==env.SITE_ORIGIN||site.protocol!=='https:')throw Error();}catch{return json({error:'Serviço ainda não configurado.'},503);}
    function finish(response){if(origin===site.origin){response.headers.set('Access-Control-Allow-Origin',origin);response.headers.set('Vary','Origin');}return response;}
    try{
      if(origin&&origin!==site.origin)reject(403,'Origem não autorizada.');
      if(request.method==='OPTIONS')return finish(new Response(null,{status:204,headers:{'Access-Control-Allow-Methods':'GET, POST, PATCH, DELETE, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization','Access-Control-Max-Age':'600'}}));
      if(!env.DB)reject(503,'Banco de comentários ainda não configurado.');
      const url=new URL(request.url),db=env.DB,time=now(),path=url.pathname;
      if(url.protocol!=='https:'&&!['localhost','127.0.0.1'].includes(url.hostname))reject(400,'Use HTTPS para acessar o serviço.');
      if(path==='/v1/health'&&request.method==='GET'){await db.prepare('SELECT key FROM site_state LIMIT 1').first();return finish(json({service:'literature-comments',version:1,ready:Boolean(env.ADMIN_TOKEN?.length>=32&&env.IP_HASH_SECRET?.length>=32&&env.TURNSTILE_SECRET_KEY)}));}
      const admin=path.startsWith('/v1/admin/');
      if(admin&&!await equalSecret(request.headers.get('Authorization')?.replace(/^Bearer /,''),env.ADMIN_TOKEN))reject(401,'Credencial de moderação inválida.');
      if(path==='/v1/comments'&&request.method==='GET'){
        const thread=threadId(url.searchParams.get('thread'));if(!await known(db,thread))reject(404,'Discussão indisponível.');
        const {after,limit}=page(url);
        const {results}=await db.prepare(`SELECT c.seq,c.id,c.parent_id,c.author,c.body,c.created_at,p.author AS reply_to FROM comments c LEFT JOIN comments p ON p.id=c.parent_id WHERE c.thread_id=? AND c.status='approved' AND c.seq>? AND (c.parent_id IS NULL OR p.status='approved') ORDER BY c.seq LIMIT ?`).bind(thread,after,limit+1).all();
        const items=results.slice(0,limit);return finish(json({items,next:results.length>limit?items.at(-1).seq:null}));
      }
      if(path==='/v1/comments'&&request.method==='POST'){
        if(origin!==site.origin)reject(403,'Envie o comentário pela página do Literature.');
        if(!env.ADMIN_TOKEN||env.ADMIN_TOKEN.length<32||!env.IP_HASH_SECRET||env.IP_HASH_SECRET.length<32||!env.TURNSTILE_SECRET_KEY)reject(503,'O envio ainda não está configurado.');
        const data=await body(request),thread=threadId(data.thread),author=text(data.author,2,60,'Nome'),message=text(data.body,3,2000,'Comentário'),requestId=uuid(data.request_id),parent=data.parent_id==null?null:uuid(data.parent_id);
        if(data.website)reject(400,'Envio recusado.'); // Campo que permanece vazio para visitantes.
        if(!await known(db,thread))reject(404,'Discussão indisponível.');
        const token=text(data.turnstile_token,1,2048,'Verificação'),ip=request.headers.get('CF-Connecting-IP');
        if(!ip)reject(503,'Não foi possível verificar o envio.');
        if(!await verify(token,ip,env))reject(403,'Refaça a verificação antes de enviar.');
        const existing=await db.prepare('SELECT thread_id,author,body,parent_id FROM comments WHERE request_id=?').bind(requestId).first();
        if(existing){if(existing.thread_id!==thread||existing.author!==author||existing.body!==message||existing.parent_id!==parent)reject(409,'Esse envio já foi usado. Atualize o formulário.');return finish(json({status:'pending'},202));}
        const bucket=Math.floor(time/600000),key=await ipKey(ip,bucket,env.IP_HASH_SECRET);
        const count=await db.prepare('INSERT INTO rate_limits(key,hits,expires_at) VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET hits=hits+1 RETURNING hits').bind(key,(bucket+2)*600000).first();
        if(count.hits>5)reject(429,'Muitos envios. Aguarde alguns minutos antes de tentar novamente.');
        if(parent&&!await db.prepare("SELECT id FROM comments WHERE id=? AND thread_id=? AND status='approved' AND parent_id IS NULL").bind(parent,thread).first())reject(400,'O comentário original não está disponível para resposta.');
        const id=crypto.randomUUID();
        const result=await db.prepare(`INSERT OR IGNORE INTO comments(id,request_id,thread_id,parent_id,author,body,status,created_at,updated_at) SELECT ?,?,?,?,?,?,'pending',?,? WHERE EXISTS(SELECT 1 FROM threads WHERE generation=${ACTIVE} AND id=?) AND (? IS NULL OR EXISTS(SELECT 1 FROM comments WHERE id=? AND status='approved' AND thread_id=? AND parent_id IS NULL))`).bind(id,requestId,thread,parent,author,message,time,time,thread,parent,parent,thread).run();
        if(!result.meta.changes){const retry=await db.prepare('SELECT thread_id,author,body,parent_id FROM comments WHERE request_id=?').bind(requestId).first();if(!retry||retry.thread_id!==thread||retry.author!==author||retry.body!==message||retry.parent_id!==parent)reject(409,'A discussão mudou. Atualize antes de enviar.');}
        return finish(json({status:'pending'},202));
      }
      if(path==='/v1/admin/threads'&&request.method==='POST'){
        const data=await body(request),generation=uuid(data.generation);
        if(!Array.isArray(data.threads)||data.threads.length>20)reject(400,'Envie até 20 discussões por lote.');
        const current=await db.prepare("SELECT value FROM site_state WHERE key='active_generation'").first();if(current?.value===generation)reject(409,'Não altere uma geração ativa.');
        const rows=data.threads.map(t=>{const id=threadId(t.id),title=text(t.title,1,400,'Título');let pageUrl;try{pageUrl=new URL(t.url);}catch{reject(400,'URL inválida.');}if(pageUrl.origin!==site.origin||pageUrl.hash)reject(400,'URL fora do site.');return {id,title,url:pageUrl.href};});
        await db.batch([db.prepare('INSERT OR IGNORE INTO generations(id,created_at) VALUES (?,?)').bind(generation,time),...rows.map(t=>db.prepare('INSERT INTO threads(generation,id,title,url) VALUES (?,?,?,?) ON CONFLICT(generation,id) DO UPDATE SET title=excluded.title,url=excluded.url').bind(generation,t.id,t.title,t.url))]);
        return finish(json({ok:true}));
      }
      if(path==='/v1/admin/threads/commit'&&request.method==='POST'){
        const data=await body(request),generation=uuid(data.generation);
        if(!Number.isSafeInteger(data.total)||data.total<0)reject(400,'Total inválido.');
        if(!await db.prepare('SELECT id FROM generations WHERE id=?').bind(generation).first())reject(400,'Geração não encontrada.');
        const count=await db.prepare('SELECT COUNT(*) AS total FROM threads WHERE generation=?').bind(generation).first();if(count.total!==data.total)reject(409,'A sincronização está incompleta.');
        await db.prepare("INSERT INTO site_state(key,value) VALUES ('active_generation',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(generation).run();
        return finish(json({ok:true,total:data.total}));
      }
      if(path==='/v1/admin/comments'&&request.method==='GET'){
        const {after,limit}=page(url),status=url.searchParams.get('status')||'pending';if(!['pending','approved','hidden','all'].includes(status))reject(400,'Filtro inválido.');
        const {results}=await db.prepare(`SELECT c.*,t.title,t.url FROM comments c LEFT JOIN threads t ON t.generation=${ACTIVE} AND t.id=c.thread_id WHERE c.seq>? AND (?='all' OR c.status=?) ORDER BY c.seq LIMIT ?`).bind(after,status,status,limit+1).all();
        const items=results.slice(0,limit);return finish(json({items,next:results.length>limit?items.at(-1).seq:null}));
      }
      const match=path.match(/^\/v1\/admin\/comments\/([0-9a-f-]+)$/);
      if(match&&request.method==='PATCH'){
        const id=uuid(match[1]),data=await body(request);if(!['approved','hidden','pending'].includes(data.status))reject(400,'Estado inválido.');
        const result=await db.prepare('UPDATE comments SET status=?,updated_at=? WHERE id=?').bind(data.status,time,id).run();if(!result.meta.changes)reject(404,'Comentário não encontrado.');return finish(json({ok:true}));
      }
      if(match&&request.method==='DELETE'){
        const result=await db.prepare('DELETE FROM comments WHERE id=?').bind(uuid(match[1])).run();if(!result.meta.changes)reject(404,'Comentário não encontrado.');return finish(json({ok:true}));
      }
      reject(404,'Recurso não encontrado.');
    }catch(error){return finish(json({error:error instanceof ApiError?error.message:'Serviço temporariamente indisponível.'},error instanceof ApiError?error.status:503));}
  },
  async scheduled(_event,env,ctx){
    ctx.waitUntil(env.DB.batch([
      env.DB.prepare('DELETE FROM rate_limits WHERE expires_at<?').bind(now()),
      env.DB.prepare(`DELETE FROM generations WHERE id!=COALESCE(${ACTIVE},'') AND created_at<?`).bind(now()-86400000)
    ]));
  }
 };
}
export default createWorker();

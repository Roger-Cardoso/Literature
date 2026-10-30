const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const store = new Map([['progresso_obra-1', '[1,2]']]);
const ctx = {window: {},localStorage:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v)}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('js-global/metadados.js','utf8'),ctx);
const api=ctx.window.Unilit;
const estrutura={sagas:[{volumes:[{arcos:[{capitulos:[{id:'estavel-b',id_legado:2},{id:'estavel-a',id_legado:1}]}]}]}]};
assert.equal(JSON.stringify(api.lidos('obra-1',estrutura)), '["estavel-a","estavel-b"]');
assert.equal(store.get('progresso_obra-1'),'[1,2]');
assert.equal(api.revelar({disponivel_apos_capitulo:'estavel-a'},'obra-1',estrutura),true);
assert.equal(api.revelar({disponivel_apos_capitulo:'ausente'},'obra-1',estrutura),false);
store.set('progresso_obra-1','inválido');store.set('unilit:v2:progresso:obra-1','{}');
assert.equal(JSON.stringify(api.lidos('obra-1',estrutura)),'[]');
ctx.localStorage.getItem=()=>{throw Error('bloqueado')};ctx.localStorage.setItem=()=>{throw Error('bloqueado')};
assert.equal(JSON.stringify(api.lidos('obra-1',estrutura)),'[]');
// Verifica a sintaxe de todos os scripts embutidos nas páginas públicas.
for(const path of ['home/index.html','scripts/modelos/obra/index-obra.html','scripts/modelos/obra/leitor.html']) {
 for(const match of fs.readFileSync(path,'utf8').matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) new vm.Script(match[1],{filename:path});
}
console.log('Migração legada, marcos de spoiler, armazenamento indisponível e sintaxe das páginas: OK');

new vm.Script(fs.readFileSync('js-global/leitor.js', 'utf8'), {filename:'leitor.js'});

new vm.Script(fs.readFileSync('js-global/contexto.js','utf8'),{filename:'contexto.js'});

new vm.Script(fs.readFileSync('js-global/semantica.js','utf8'),{filename:'semantica.js'});

new vm.Script(fs.readFileSync('js-global/guia-cenas.js','utf8'),{filename:'guia-cenas.js'});

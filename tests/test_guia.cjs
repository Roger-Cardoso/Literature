const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(tag){this.tag=tag;this.children=[];this.attrs={};}append(...x){this.children.push(...x)}setAttribute(k,v){this.attrs[k]=v}}
const ctx={window:{},document:{createElement:t=>new El(t),createTextNode:t=>({textContent:t})}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('js-global/guia-cenas.js','utf8'),ctx);
const cenas=[{titulo_cena:'Cena 1',ancora:'a',relevancia:'essencial',avisos_conteudo:['Aranhas'],resumo_alternativo:'Resumo com spoilers.'},{titulo_cena:'Cena 2',ancora:'b',relevancia:'opcional',avisos_conteudo:[]}];
const destino=new El('div');let alvo;
const painel=ctx.window.GuiaCenas.montar({capitulo:{id:'cap',cenas},destino,raiz:{},ir:x=>alvo=x,proximo:{id:'outro',titulo:'Próximo'}});
const primeira=painel.children.find(x=>x.tag==='section');
assert(primeira.children.some(x=>x.textContent==='Conteúdo: Aranhas'));
const spoiler=primeira.children.find(x=>x.tag==='details');assert(spoiler);assert.equal(spoiler.attrs.open,undefined);
const nav=primeira.children.find(x=>x.tag==='nav');let prevenido=false;nav.children[1].onclick({preventDefault:()=>prevenido=true});assert(prevenido);assert.equal(alvo,'b');
const segunda=painel.children.filter(x=>x.tag==='section')[1];segunda.children.find(x=>x.tag==='nav').children[1].onclick({preventDefault(){}});assert.equal(alvo,'fim-do-capitulo');
assert.equal(painel.children.at(-1).href,'leitor.html?id=outro');
const preview=ctx.window.GuiaCenas.montar({capitulo:{id:'cap',cenas},destino:new El('div')});
assert.equal(preview.children.find(x=>x.tag==='section').children.find(x=>x.tag==='nav').children[0].href,'leitor.html?id=cap&cena=a');
console.log('Guia: avisos antecipados, spoilers fechados, saltos de cena/fim/capítulo e links da página da obra: OK');

const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{
 constructor(tag='div'){this.tag=tag;this.children=[];this.style={};this.dataset={};this.textContent='';}
 append(...xs){this.children.push(...xs)}replaceChildren(...xs){this.children=xs}addEventListener(){}
 get childElementCount(){return this.children.length}
 set innerHTML(_){throw Error('Metadados precisam ser inseridos como texto, sem interpretação de HTML');}
}
const ids=new Map(),obter=id=>{if(!ids.has(id))ids.set(id,new El());return ids.get(id)};
const literal='<img src=x onerror="efeito()"> & "citação"';
const ctx={document:{getElementById:obter,createElement:t=>new El(t),querySelector:obter},Unilit:{revelar:()=>true,capitulos:()=>[{id:'cap'}]},infoGlobal:{titulo:literal,capa_url:'/capa.svg',capa:{alt:literal},status:'Em andamento',autor:literal,sinopse:literal,formato:'publicacao_seriada',tags:[literal],lore:[{id:'verbete',titulo:literal,descricao:literal}],personagens:[{id:'ana',nome:literal,descricao_curta:literal}]},estruturaGlobal:{total_capitulos:1,total_palavras:100},calcularTempoFormatado:()=> '1 min'};
const fonte=fs.readFileSync('scripts/modelos/obra/index-obra.html','utf8');const inicio=fonte.indexOf('        function elemento('),fim=fonte.indexOf('        // --- SISTEMA DE SELETORES',inicio);
vm.createContext(ctx);vm.runInContext(fonte.slice(inicio,fim),ctx);vm.runInContext('renderizarHero();renderizarAbas()',ctx);
assert.equal(obter('ui-titulo').innerText,literal);assert.equal(obter('ui-tags').children[1].textContent,literal);
assert.equal(obter('container-lore').children[0].children[0].textContent,literal);
const personagem=obter('container-personagens').children[0];assert.equal(personagem.children[0].src,'../assets/imagens/personagem.svg');assert.equal(personagem.children[1].children[0].textContent,literal);
console.log('Obra: metadados literais, atributos separados e imagem substituta local: OK');

const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
class Elemento {
 constructor(){this.children=[];this.attrs={};this.listeners={};this.textContent='';}
 append(...itens){this.children.push(...itens)}
 get childElementCount(){return this.children.length}
 setAttribute(k,v){this.attrs[k]=v}
 addEventListener(k,v){this.listeners[k]=v}
 showModal(){this.open=true}close(){this.open=false}
 replaceWith(el){this.substituto=el}
}
const ctx={window:{},document:{createElement:()=>new Elemento()},Unilit:{revelar:x=>!x.disponivel_apos_capitulo}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('js-global/contexto.js','utf8'),ctx);
const publico=new Elemento();publico.dataset={verbeteId:'aberto'};publico.textContent='Termo';
const bloqueado=new Elemento();bloqueado.dataset={verbeteId:'fechado'};bloqueado.textContent='Segredo';
const destino=new Elemento();
const resultado=ctx.window.ContextoLiterature.montar({obra:{id_obra:'obra',slug:'obra',lore:[{id:'aberto',titulo:'Definição',descricao:'Texto editorial'},{id:'fechado',titulo:'Segredo',descricao:'Não revelar',disponivel_apos_capitulo:'futuro'}]},estrutura:{},capitulo:{verbetes_ids:['aberto','fechado'],notas:[{titulo:'Nota',texto:'Nota pública'},{titulo:'Oculta',texto:'Segredo',disponivel_apos_capitulo:'futuro'}]},raiz:{querySelector:()=>null,querySelectorAll:selector=>selector==='[data-glossary-term]'?[]:[publico,bloqueado]},destino});
assert(publico.substituto);assert.equal(bloqueado.substituto,undefined);
assert.equal(publico.substituto.attrs['aria-haspopup'],'dialog');
publico.substituto.listeners.click();assert.equal(resultado.dialogo.open,true);
assert.equal(resultado.dialogo.children[0].textContent,'Definição');
assert.equal(resultado.dialogo.children[1].textContent,'Texto editorial');
assert.equal(resultado.painel.children.filter(e=>e.textContent==='Segredo').length,0);
assert.equal(resultado.painel.children.length,4); // resumo, nota pública, título e verbete disponível
console.log('Glossário por referência, ativação acessível, diálogo e exclusão de spoilers: OK');

const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
class El{
 constructor(){this.children=[];this.listeners={};this.dataset={};this.hidden=false;this.textContent='';}
 append(...xs){this.children.push(...xs)} setAttribute(k,v){this[k]=v} remove(){this.removed=true}
 before(el){this.etiqueta=el} addEventListener(k,fn){this.listeners[k]=fn}
}
function montar({locutor=true,pov=false,bloqueado=false,exibicao=null}={}){
 const area=new El();area.scrollTop=0;area.clientHeight=500;area.getBoundingClientRect=()=>({top:0});area.dispatchEvent=e=>area.listeners[e.type]?.();
 const p=new El();p.dataset.locutorId='ana';if(exibicao)p.dataset.displayName=exibicao;p.getBoundingClientRect=()=>({top:100+(p.etiqueta&&!p.etiqueta.hidden?40:0)-area.scrollTop,bottom:150});
 const sec=new El();sec.dataset.povCharacter='ana';if(exibicao)sec.dataset.povDisplayName=exibicao;let topoSec=0;sec.getBoundingClientRect=()=>({top:topoSec});
 const raiz=new El();raiz.querySelector=()=>null;raiz.querySelectorAll=q=>q==='p'?[p]:q.includes('data-locutor-id')?(locutor?[p]:[]):pov?[sec]:[];
 const destino=new El();const salvo={};const ctx={window:{},document:{createElement:()=>new El(),createTextNode:text=>({textContent:text})},Event:class{constructor(type){this.type=type}},Unilit:{revelar:()=>!bloqueado,ler:()=>({}),salvar:(k,v)=>salvo[k]=v}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync('js-global/semantica.js','utf8'),ctx);
 const resultado=ctx.window.SemanticaLiterature.montar({obra:{id_obra:'obra',personagens:[{id:'ana',nome:'Ana'}]},estrutura:{},raiz,area,destino});
 const inputs=resultado.painel.children.filter(x=>x.className==='opcao').map(x=>x.children[0]);
 return {area,p,raiz,inputs,resultado,salvo,mover:top=>topoSec=top};
}
let x=montar();assert.equal(x.inputs[0].disabled,false);assert.equal(x.inputs[1].disabled,true);
const antes=x.p.getBoundingClientRect().top;x.inputs[0].checked=true;x.inputs[0].onchange();
assert.equal(x.p.getBoundingClientRect().top,antes,'Ativar etiquetas mantém o parágrafo na mesma altura');assert.equal(x.area.scrollTop,40);
x=montar({locutor:false,pov:true});assert.equal(x.inputs[0].disabled,true);assert.equal(x.inputs[1].disabled,false);
x.inputs[1].checked=true;x.inputs[1].onchange();assert.equal(x.raiz.etiqueta.hidden,false);assert.equal(x.raiz.etiqueta.textContent,'Ponto de vista · Ana');
x.mover(300);x.area.dispatchEvent({type:'literature:layout'});assert.equal(x.raiz.etiqueta.hidden,true,'Mudança de layout recalcula o POV');
x=montar({bloqueado:true});assert(x.inputs.every(i=>i.disabled),'Identidades bloqueadas não são oferecidas como auxílio');
console.log('Auxílios: disponibilidade individual, posição estável, atualização de POV e bloqueio de spoilers: OK');

x=montar({pov:true,bloqueado:true,exibicao:'???'});assert.equal(x.p.etiqueta.textContent,'???');x.inputs[1].checked=true;x.inputs[1].onchange();assert.equal(x.raiz.etiqueta.textContent,'Ponto de vista · ???');assert(!x.raiz.etiqueta.textContent.includes('Ana'));
console.log('Nome contextual preserva identidade oculta nas etiquetas e no POV: OK');

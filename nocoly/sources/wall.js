(function(){
  const $=id=>document.getElementById(id);
  const wall=$('wall'), chips=$('chips'), detail=$('detail'), stats=$('stats'), ph=$('ph'), phl=$('phl');
  if(!wall) return;
  const PHNAME={1:'Core Foundation'}; PHASES.forEach(p=>PHNAME[p[0]]=p[1]);
  const on=new Set(['bcat','bcoa','bterm','bgeo','btax']);
  const META={}; // id -> {name, sub, deps, kind, count, course}
  CORE.forEach(w=>META[w[0]]={name:w[1],sub:w[2],deps:w[3],kind:'core',count:1,course:1});
  BUNDLES.forEach(b=>b[4].forEach(w=>META[w[0]]={name:w[1],sub:w[2],deps:w[3],kind:'bundle',count:1,course:1,bundle:b[0]}));
  PHASES.forEach(p=>p[2].forEach(w=>META[w[0]]={name:w[1],sub:w[2],deps:w[3],kind:'phase',count:w[4]||1,course:p[0]}));
  // '!' prefix = hard dependency even when the target lives in an optional bundle
  Object.values(META).forEach(m=>{
    m.hard=new Set(m.deps.filter(d=>d[0]==='!').map(d=>d.slice(1)));
    m.deps=m.deps.map(d=>d[0]==='!'?d.slice(1):d);
  });
  const RDEP={}; Object.entries(META).forEach(([id,m])=>m.deps.forEach(d=>(RDEP[d]=RDEP[d]||[]).push(id)));

  function act0(){return BUNDLES.filter(b=>on.has(b[0])).map(b=>b[0]);}
  function present(){
    const p=+ph.value, s=new Set();
    CORE.forEach(w=>s.add(w[0]));
    BUNDLES.forEach(b=>{ if(on.has(b[0])) b[4].forEach(w=>s.add(w[0])); });
    PHASES.forEach(x=>{ if(x[0]<=p) x[2].forEach(w=>s.add(w[0])); });
    return s;
  }
  function status(id,S){
    const m=META[id]; if(!m) return {};
    const miss=m.deps.filter(d=>!S.has(d));
    const hard=miss.filter(d=>m.hard.has(d)||!META[d]||META[d].kind!=='bundle');
    return {miss,hard};
  }
  function brick(id,S,extra){
    const m=META[id], st=status(id,S);
    const cls=['brk',m.kind==='core'?'core':m.kind==='bundle'?'bundle':''];
    if(st.hard.length) cls.push('blocked');
    else if(st.miss.length) cls.push('degraded');
    if(extra) cls.push(extra);
    return `<button class="${cls.join(' ')}" data-id="${id}" type="button">${m.name}<span>${m.sub}</span></button>`;
  }
  function render(){
    const p=+ph.value, S=present();
    phl.textContent=`${p} — ${PHNAME[p]}`;
    let html='';
    // course 1: core
    html+=`<div class="course"><div class="chead"><b>Phase 1</b><span>Core Foundation</span><i>${CORE.length} worksheets · ~${(HOURS.core/HOURS.week).toFixed(1)} wk</i></div>
      <div class="bricks">${CORE.map(w=>brick(w[0],S)).join('')}</div></div>`;
    // course 2: enabled bundles
    const act=BUNDLES.filter(b=>on.has(b[0]));
    const nb=act.reduce((a,b)=>a+b[4].length,0);
    html+=`<div class="course"><div class="chead"><b>Optional</b><span>Feature bundles</span><i>${act.length} on · ${nb} worksheets · ~${((act.reduce((a,b)=>a+(HOURS.bundles[b[0]]||0),0)+(act.length?HOURS.bundleApp:0))/HOURS.week).toFixed(1)} wk</i></div>
      <div class="bricks">${act.length?act.flatMap(b=>b[4].map(w=>brick(w[0],S))).join(''):'<span class="wdetail" style="border:0;margin:0;padding:0;min-height:0">none enabled — switch one on above</span>'}</div></div>`;
    // phases
    PHASES.filter(x=>x[0]<=p).forEach(x=>{
      const n=x[2].reduce((a,w)=>a+(w[4]||1),0);
      html+=`<div class="course"><div class="chead"><b>Phase ${x[0]}</b><span>${x[1]}</span><i>${n} worksheets · ~${((HOURS.phases[x[0]]||0)/HOURS.week).toFixed(1)} wk</i></div>
        <div class="bricks">${x[2].map(w=>brick(w[0],S)).join('')}</div></div>`;
    });
    wall.innerHTML=html;
    // stats
    let built=0,blocked=0,degraded=0;
    S.forEach(id=>{const m=META[id]; if(!m)return; built+=m.count;
      const st=status(id,S); if(st.hard.length) blocked+=m.count; else if(st.miss.length) degraded+=m.count;});
    let hrs=HOURS.core+act0().reduce((a,b)=>a+(HOURS.bundles[b]||0),0)+(act0().length?HOURS.bundleApp:0)
      +PHASES.filter(x=>x[0]<=p).reduce((a,x)=>a+(HOURS.phases[x[0]]||0),0);
    stats.innerHTML=`<span>worksheets built <b>${built}</b> of 234</span>`
      +`<span>elapsed <b>${(hrs/HOURS.week).toFixed(1)}</b> weeks at 40 h/week · ~${Math.round(hrs)} h</span>`
      +(blocked?`<span class="warn">blocked <b>${blocked}</b> — a required worksheet isn't built yet</span>`:'')
      +(degraded?`<span>degraded <b>${degraded}</b> — an optional bundle they use is switched off</span>`:'');
  }
  function say(id){
    const S=present(), m=META[id], st=status(id,S);
    const nm=x=>META[x]?META[x].name:x;
    const up=(RDEP[id]||[]).filter(x=>S.has(x));
    detail.innerHTML=`<b>${m.name}</b> <span class="k">${m.sub}</span><br>`
      +`<span class="k">sits on</span> ${m.deps.length?m.deps.map(d=>S.has(d)?nm(d):`<span class="miss">${nm(d)} (not built)</span>`).join(' · '):'nothing — it can be the first worksheet in the system'}<br>`
      +`<span class="k">carries</span> ${up.length?up.map(nm).join(' · '):'nothing yet'}`;
    wall.classList.add('sel');
    wall.querySelectorAll('.brk').forEach(b=>{
      b.classList.toggle('on',b.dataset.id===id);
      b.classList.toggle('dep',m.deps.includes(b.dataset.id));
      b.classList.toggle('rdep',up.includes(b.dataset.id));
    });
  }
  function clear(){
    wall.classList.remove('sel');
    wall.querySelectorAll('.brk').forEach(b=>b.classList.remove('on','dep','rdep'));
    detail.innerHTML='<span class="k">Hover or tab to a brick to see what it sits on and what sits on it.</span>';
  }
  chips.innerHTML='<span class="lbl">feature bundles</span>'+BUNDLES.map(b=>
    `<button class="bchip" type="button" data-b="${b[0]}" aria-pressed="${on.has(b[0])}" title="${b[2]!=='—'?b[2]+' · ':''}needed by ${b[3]}">${b[1]} <span style="opacity:.6">${b[4].length}</span></button>`).join('');
  chips.addEventListener('click',e=>{const t=e.target.closest('.bchip'); if(!t)return;
    const k=t.dataset.b; on.has(k)?on.delete(k):on.add(k);
    t.setAttribute('aria-pressed',on.has(k)); render(); clear();});
  ph.addEventListener('input',()=>{render();clear();});
  wall.addEventListener('mouseover',e=>{const b=e.target.closest('.brk'); if(b)say(b.dataset.id);});
  wall.addEventListener('mouseleave',clear);
  wall.addEventListener('focusin',e=>{const b=e.target.closest('.brk'); if(b)say(b.dataset.id);});
  render(); clear();
})();

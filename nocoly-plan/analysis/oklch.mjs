const f=x=>x<=0.0031308?12.92*x:1.055*Math.pow(x,1/2.4)-0.055;
function hex(L,C,H){
  const h=H*Math.PI/180, a=C*Math.cos(h), b=C*Math.sin(h);
  const l_=L+0.3963377774*a+0.2158037573*b, m_=L-0.1055613458*a-0.0638541728*b, s_=L-0.0894841775*a-1.2914855480*b;
  const l=l_**3,m=m_**3,s=s_**3;
  let r= 4.0767416621*l-3.3077115913*m+0.2309699292*s;
  let g=-1.2684380046*l+2.6097574011*m-0.3413193965*s;
  let bb=-0.0041960863*l-0.7034186147*m+1.7076147010*s;
  const c=v=>{const q=Math.round(Math.min(1,Math.max(0,f(v)))*255);return q.toString(16).padStart(2,'0')};
  return '#'+(c(r)+c(g)+c(bb)).toUpperCase();
}
// hues: plum 325, teal 178, orange 55
console.log('LIGHT  L=0.56 C=0.13 ->', ['plum',325,'teal',178,'orange',55].filter((_,i)=>i%2).map((H,i)=>hex(0.56,0.13,H)).join(','));
for(const [name,H] of [['plum',325],['teal',178],['orange',55]]){
  console.log(`  light ${name.padEnd(7)}`, [0.54,0.56,0.58].map(L=>hex(L,0.13,H)).join(' '));
}
for(const [name,H] of [['plum',325],['teal',178],['orange',55]]){
  console.log(`  dark  ${name.padEnd(7)}`, [0.62,0.64,0.66].map(L=>hex(L,0.13,H)).join(' '));
}
// sequential plum ramp for heatmap, light mode: L 0.95 -> 0.50
console.log('SEQ light:', [0.955,0.90,0.82,0.72,0.60,0.50].map(L=>hex(L, L>0.9?0.035:0.14-(0.95-L)*0.03, 325)).join(','));
console.log('SEQ dark :', [0.30,0.38,0.46,0.54,0.62,0.70].map(L=>hex(L, 0.05+(L-0.30)*0.20, 325)).join(','));

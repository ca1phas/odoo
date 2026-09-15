const f=x=>x<=0.0031308?12.92*x:1.055*Math.pow(x,1/2.4)-0.055;
function hex(L,C,H){const h=H*Math.PI/180,a=C*Math.cos(h),b=C*Math.sin(h);
 const l_=L+0.3963377774*a+0.2158037573*b,m_=L-0.1055613458*a-0.0638541728*b,s_=L-0.0894841775*a-1.2914855480*b;
 const l=l_**3,m=m_**3,s=s_**3;
 const r=4.0767416621*l-3.3077115913*m+0.2309699292*s,g=-1.2684380046*l+2.6097574011*m-0.3413193965*s,bb=-0.0041960863*l-0.7034186147*m+1.7076147010*s;
 const c=v=>Math.round(Math.min(1,Math.max(0,f(v)))*255).toString(16).padStart(2,'0').toUpperCase();
 return '#'+c(r)+c(g)+c(bb);}
const H=325;
const L1=[0.955,0.895,0.825,0.745,0.655,0.560], C1=[0.020,0.045,0.070,0.095,0.115,0.130];
const L2=[0.255,0.320,0.395,0.470,0.550,0.635], C2=[0.030,0.055,0.078,0.098,0.115,0.130];
console.log('--light ramp (mono L desc):'); L1.forEach((L,i)=>console.log(`  ${i+1}  L=${L}  ${hex(L,C1[i],H)}`));
console.log('--dark ramp (mono L asc):');  L2.forEach((L,i)=>console.log(`  ${i+1}  L=${L}  ${hex(L,C2[i],H)}`));

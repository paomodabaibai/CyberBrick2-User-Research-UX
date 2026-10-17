// Execute in use_figma; replace __BOARD_SET__ with [0,1,2] or [3,4,5].
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('0:1'));
await Promise.all(['Regular','Bold'].map(style=>figma.loadFontAsync({family:'Noto Sans SC',style})));
const ids=[],changed=[],selection=__BOARD_SET__;
const panelIds=['146:11','146:12','146:14','146:15','146:17','146:18'];
const panels=await Promise.all(panelIds.map(id=>figma.getNodeByIdAsync(id)));
for(const i of selection) if(panels[i].children.length) throw new Error('Panel not empty: '+panelIds[i]);
const P={ink:'#173C47',muted:'#58727C',line:'#B5C7CB',pale:'#EEF4F4',red:'#D74F48',blue:'#2379CF',gold:'#E9B74A',wood:'#BDA17D',dark:'#284955'};
function rgb(hex){return {r:parseInt(hex.slice(1,3),16)/255,g:parseInt(hex.slice(3,5),16)/255,b:parseInt(hex.slice(5,7),16)/255};}
const fill=c=>[{type:'SOLID',color:rgb(c)}];
function remember(n){ids.push(n.id);return n;}
function rect(p,x,y,w,h,c=P.pale,s=null,sw=1,name='板件'){const n=remember(figma.createRectangle());p.appendChild(n);n.name=name;n.resize(w,h);n.x=x;n.y=y;n.fills=c?fill(c):[];n.strokes=s?fill(s):[];n.strokeWeight=sw;return n;}
function ellipse(p,cx,cy,r,c=null,s=P.ink,sw=2,name='圆'){const n=remember(figma.createEllipse());p.appendChild(n);n.name=name;n.resize(2*r,2*r);n.x=cx-r;n.y=cy-r;n.fills=c?fill(c):[];n.strokes=s?fill(s):[];n.strokeWeight=sw;return n;}
function txt(p,x,y,w,s,size=28,c=P.ink,bold=false){const n=remember(figma.createText());n.fontName={family:'Noto Sans SC',style:bold?'Bold':'Regular'};n.fontSize=size;n.lineHeight={unit:'PERCENT',value:135};n.characters=s;n.resize(w,Math.max(20,size*1.4));n.textAutoResize='HEIGHT';n.fills=fill(c);p.appendChild(n);n.x=x;n.y=y;n.name=s.slice(0,40);return n;}
function poly(p,pts,c=null,s=P.ink,sw=2,closed=true,name='尺寸线'){const minx=Math.min(...pts.map(q=>q[0])),miny=Math.min(...pts.map(q=>q[1]));const n=remember(figma.createVector());p.appendChild(n);n.vectorPaths=[{windingRule:'NONZERO',data:pts.map((q,i)=>(i?'L':'M')+(q[0]-minx)+' '+(q[1]-miny)).join(' ')+(closed?' Z':'')}];n.x=minx;n.y=miny;n.fills=c?fill(c):[];n.strokes=s?fill(s):[];n.strokeWeight=sw;n.name=name;return n;}
const line=(p,x,y,a,b,c=P.line,sw=2)=>poly(p,[[x,y],[a,b]],null,c,sw,false);
function arrow(p,x,y,a,b,c=P.ink,sw=3){line(p,x,y,a,b,c,sw);const q=Math.atan2(b-y,a-x),r=14;poly(p,[[a,b],[a-r*Math.cos(q-.45),b-r*Math.sin(q-.45)],[a-r*Math.cos(q+.45),b-r*Math.sin(q+.45)]],c,null);}
function dh(p,x1,x2,y,label,baseY=null,c=P.muted){if(baseY!==null){line(p,x1,baseY,x1,y+10,c,1);line(p,x2,baseY,x2,y+10,c,1);}line(p,x1,y,x2,y,c,1.5);line(p,x1-5,y+7,x1+5,y-7,c,1.5);line(p,x2-5,y+7,x2+5,y-7,c,1.5);const t=txt(p,(x1+x2)/2-130,y-42,260,label,25,c,true);t.textAlignHorizontal='CENTER';}
function dv(p,y1,y2,x,label,baseX=null,c=P.muted){if(baseX!==null){line(p,baseX,y1,x+10,y1,c,1);line(p,baseX,y2,x+10,y2,c,1);}line(p,x,y1,x,y2,c,1.5);line(p,x-7,y1+5,x+7,y1-5,c,1.5);line(p,x-7,y2+5,x+7,y2-5,c,1.5);const left=baseX!==null&&baseX>x;txt(p,left?Math.max(5,x-72):x+14,(y1+y2)/2-20,left?68:160,label,25,c,true);}
function stack(p,x,y,w,title,body,color=P.ink){const n=remember(figma.createAutoLayout('VERTICAL'));p.appendChild(n);n.name=title;n.resize(w,10);n.paddingLeft=22;n.paddingRight=22;n.paddingTop=20;n.paddingBottom=20;n.itemSpacing=12;n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.fills=fill(P.pale);n.x=x;n.y=y;const a=txt(n,0,0,w-44,title,29,color,true),b=txt(n,0,0,w-44,body,25,P.muted);return n;}
function header(p,num,title,sub){const n=remember(figma.createAutoLayout('VERTICAL'));p.appendChild(n);n.name='图题';n.resize(1808,10);n.itemSpacing=12;n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.fills=[];n.x=60;n.y=40;txt(n,0,0,1808,'CYBERBRICK 2.0  /  手工制作  /  '+num,20,P.muted,true);txt(n,0,0,1808,title,48,P.ink,true);txt(n,0,0,1808,sub,24,P.muted);}
function footer(p,s){line(p,60,1372,1868,1372);txt(p,60,1390,1808,s,20,P.muted);}
function table(p,x,y,widths,rows,font=25,rowH=66){const v=remember(figma.createAutoLayout('VERTICAL'));p.appendChild(v);v.name='尺寸表';v.resize(widths.reduce((a,b)=>a+b,0),10);v.itemSpacing=0;v.primaryAxisSizingMode='AUTO';v.counterAxisSizingMode='FIXED';v.fills=[];v.x=x;v.y=y;rows.forEach((row,i)=>{const h=remember(figma.createAutoLayout('HORIZONTAL'));v.appendChild(h);h.resize(widths.reduce((a,b)=>a+b,0),rowH);h.primaryAxisSizingMode='FIXED';h.counterAxisSizingMode='FIXED';h.paddingTop=12;h.paddingBottom=8;h.fills=fill(i===0?P.dark:(i%2?P.pale:'#FFFFFF'));row.forEach((s,j)=>{const cell=remember(figma.createAutoLayout('VERTICAL'));h.appendChild(cell);cell.resize(widths[j],rowH-20);cell.paddingLeft=12;cell.paddingRight=10;cell.primaryAxisSizingMode='FIXED';cell.counterAxisSizingMode='FIXED';cell.fills=[];txt(cell,0,0,widths[j]-22,String(s),font,i===0?'#FFFFFF':P.ink,i===0);});});return v;}
function svg(p,x,y,source,name){const n=figma.createNodeFromSvg(source);p.appendChild(n);n.x=x;n.y=y;n.name=name;ids.push(n.id,...n.findAll(()=>true).map(q=>q.id));return n;}
function map(p,variant){
 header(p,variant==='A'?'01':'02',variant==='A'?'完整墙布局 A｜照图摆墙':'开放通道 B｜优先试玩', '已确认场地 1260 × 1260  ·  单层平地  ·  原点左下，X向右、Y向上  ·  所有尺寸为 mm');
 const ox=154,oy=250,s=.70,W=1260*s;const point=(x,y)=>[ox+x*s,oy+(1260-y)*s];
 const r=(x,y,w,h,c,st=P.line,sw=1,n='')=>rect(p,ox+x*s,oy+(1260-y-h)*s,w*s,h*s,c,st,sw,n);
 for(let j=0;j<2;j++)for(let i=0;i<3;i++){r(i*420,j*630,420,630,(i+j)%2?'#F3F7F7':'#E7F0F0',P.line,2,'F'+(j*3+i+1));const [x,y]=point(i*420+35,j*630+45);txt(p,x,y-25,180,'F'+(j*3+i+1),19,P.muted);}
 // Routes are schematic center lines, not a claim of a validated steering radius.
 function route(color,mirror){const q=(x,y)=>{if(mirror){x=1260-x;y=1260-y;}return [x*s,(1260-y)*s];};let d;if(variant==='A'){const v=[[260,180],[810,180],[870,180],[870,250],[870,590],[870,650],[800,650],[320,650]].map(z=>q(...z));d=`M${v[0]} L${v[1]} Q${v[2]} ${v[3]} L${v[4]} Q${v[5]} ${v[6]} L${v[7]}`;}else {d=`M${q(260,180)} L${q(260,590)}`;}svg(p,ox,oy,`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${W}" viewBox="0 0 ${W} ${W}"><path d="${d}" fill="none" stroke="${color}" stroke-width="5" stroke-dasharray="12 10" stroke-linecap="round"/></svg>`,'主要路线示意');}
 route(P.red,false);route(P.blue,true);
 for(const a of [[0,0,1260,20],[0,1240,1260,20],[0,20,20,1220],[1240,20,20,1220]])r(...a,P.wood,P.wood,1,'木护沿 20占地×30高');
 const walls=[...Array.from({length:4},(_,i)=>({id:'LH'+(i+1),x:20+i*180,y:340,w:180,h:40,H:[60,80,100,80][i],omit:i<3})),{id:'LS',x:500,y:380,w:40,h:120,H:80}];walls.push(...walls.map(a=>({...a,id:a.id.replace('L','R'),x:1260-a.x-a.w,y:1260-a.y-a.h})));
 for(const a of walls){if(variant==='B'&&a.omit)continue;r(a.x,a.y,a.w,a.h,a.H===100?'#2F535F':a.H===60?'#72949D':'#4B717C',null,0,a.id+' / 高'+a.H);const [x,y]=point(a.x,a.y+a.h);txt(p,x+3,y+(a.h>40?30:1),Math.max(a.w*s,70),a.id,18,'#FFFFFF',true);}
 for(const [x,y,c,sgn,team] of [[260,180,P.red,1,'红'],[1000,1080,P.blue,-1,'蓝']]){const [cx,cy]=point(x,y);ellipse(p,cx,cy,90*s,null,c,4,team+'出生圈 Ø180');const horiz=variant==='A';r(x-(horiz?100:45),y-(horiz?45:100),horiz?200:90,horiz?90:200,horiz?'#F4E8E3':'#F1F4F3',c,1,team+'机器人约200×90');arrow(p,cx,cy,cx+(horiz?80*sgn:0),cy+(horiz?0:-80*sgn),c,4);txt(p,cx-100,cy+76,210,team+'出生',23,c,true);}
 for(const [x,y,c,sgn,team] of [[260,650,P.red,1,'红'],[1000,610,P.blue,-1,'蓝']]){const [cx,cy]=point(x,y);r(x-80,y+150*sgn-60,160,120,'#F7EFE2',c,2,team+'靶座');const pp=point(x,y+150*sgn);line(p,cx,cy,...pp,c,2);ellipse(p,cx,cy,35*s,c,c,2,team+'球 Ø70');txt(p,cx-75,cy+35,240,team+'球 Ø70',23,c,true);}
 dh(p,ox,ox+W,236,'1260',oy);dh(p,ox,ox+420*s,1190,'420',oy+W);dh(p,ox+420*s,ox+840*s,1190,'420',oy+W);dh(p,ox+840*s,ox+W,1190,'420',oy+W);dv(p,oy,oy+W,82,'1260',ox);dv(p,oy,oy+630*s,1076,'630',ox+W);dv(p,oy+630*s,oy+W,1076,'630',ox+W);
 const a=point(0,0);txt(p,a[0]-40,a[1]+13,170,'O (0,0)',20,P.muted);arrow(p,...a,a[0]+75,a[1],P.ink,2);arrow(p,...a,a[0],a[1]-75,P.ink,2);
 if(variant==='B'){const q=point(20,355),q2=point(500,355);dh(p,q[0],q2[0],q[1]-25,'入口净宽480');}
 stack(p,1190,250,670,'颜色就是攻击指令','红方从红圈出发 → 打红球（蓝方守护）\n蓝方从蓝圈出发 → 打蓝球（红方守护）\n球脱开上磁点、降到低位才计分。');
 stack(p,1190,510,670,variant==='A'?'A：10段墙全部装上':'B：拆掉6段横墙',variant==='A'?'LH1–4、LS + RH1–4、RS\n长墙端部通路500；出生带净深320。\n有绕行和转向，路线虚线仅作方向示意。':'拆 LH1、LH2、LH3、RH1、RH2、RH3。\n底脚一起拿走，保留 LH4、LS、RH4、RS。\n两侧入口净宽480，直进到同色球前。');
 table(p,1190,810,[195,475],[['中心点','坐标 X, Y'],['红出生 / 球','260,180  /  260,650'],['蓝出生 / 球','1000,1080 / 1000,610'],['红 / 蓝后柱','260,800  / 1000,460']],22,64);
 txt(p,1190,1180,670,'尺寸量到40宽墙脚外缘；圈是出生标记，200长机器人无需完全塞进Ø180圈内。',24,P.muted);
 footer(p,'实线板缝＝420×630分板；深色＝墙脚占地；虚线＝主要路线。走位与攻击净空仍需实机确认。');
}
function cutting(p){header(p,'03','一张雪弗板，裁出整套场地','店家代切优先  ·  全部板件厚5  ·  28片矩形＋20片可选小三角  ·  不用3D打印');
 const x=100,y=270,s=.40;rect(p,x,y,1220*s,2440*s,'#F7F9F7',P.ink,2,'1220×2440原板');
 for(let i=0;i<2;i++)for(let j=0;j<3;j++){rect(p,x+i*423*s,y+j*633*s,420*s,630*s,'#DCEAEA',P.line,2);txt(p,x+i*423*s+15,y+j*633*s+90,150,'底板\n420×630\n1片',25,P.ink,true);}
 rect(p,x+846*s,y,374*s,768*s,'#EFDDB2',P.gold,2);txt(p,x+855*s,y+75,135,'全部小件\n374宽余条\n约770长内',22,P.ink,true);dh(p,x,x+1220*s,225,'1220',y);dv(p,y,y+2440*s,80,'2440',x);
 txt(p,100,1274,500,'排料按3刀缝；商家依刀具调整。\n成品面积约1.824 m²，占整板约61%。',24,P.muted);
 table(p,710,250,[225,340,125,450],[['板件','裁切长×宽×厚','数量','装配后的用途'],['F 底板','420×630×5','6','3列×2行 → 1260方形'],['W60 竖片','180×55×5','2','装好总高60'],['W80 竖片','180×75×5','4','装好总高80'],['W100 竖片','180×95×5','2','装好总高100'],['WS 支墙','120×75×5','2','装好总高80'],['B180 底脚','180×40×5','8','横墙底脚'],['B120 底脚','120×40×5','2','支墙底脚'],['TBASE 靶座','160×120×5','2','球前没有凸起脚座']],25,74);
 stack(p,710,1040,550,'可选小三角 ×20','直角边15×30，厚5。\n每面墙前后各1片。\n先裁10片15×30，再对角切。');
 stack(p,1290,1040,560,'木条也让店家切','20×30护沿：420×6、610×4。\n20×20靶架：臂200×2，柱220毛坯×2。\n柱按实测再裁短。');
 footer(p,'板厚以实测为准：竖片高度＝墙总高−底脚实厚。5mm整板和木条优先代切；留余料做试粘和调整。');
}
function wall(p){header(p,'04','墙怎么粘｜底脚与竖片分开做','主墙沿用40宽占地  ·  竖片居中  ·  加强片不伸出脚座  ·  墙可拆换位置');
 const proj=(x,y,z)=>[180+2.9*x+1.35*y,760+.68*x-.68*y-2.9*z];
 function box(x,y,z,a,b,h,col){for(const [pts,c] of [[[[x,y,z],[x+a,y,z],[x+a,y,z+h],[x,y,z+h]],col],[[[x+a,y,z],[x+a,y+b,z],[x+a,y+b,z+h],[x+a,y,z+h]],'#6B8890'],[[[x,y,z+h],[x+a,y,z+h],[x+a,y+b,z+h],[x,y+b,z+h]],'#BDD0D5']])poly(p,pts.map(q=>proj(...q)),c,P.ink,2);}
 box(0,0,0,180,40,5,'#92ADB5');box(0,17.5,45,180,5,75,'#D8E7E9');
 poly(p,[proj(40,2.5,5),proj(40,17.5,5),proj(40,17.5,35)],'#90ABB4',P.ink,2);
 const a=proj(0,17.5,45),b=proj(0,17.5,5);arrow(p,a[0],a[1]+8,b[0],b[1]-10,P.gold,4);
 txt(p,85,220,900,'分开示意 / 以总高80的横墙为例',30,P.ink,true);
 txt(p,105,325,480,'竖片 180 × 75 × 5',31,P.ink,true);line(p,390,380,...proj(55,17.5,95),P.muted,2);
 txt(p,790,810,310,'底脚 180 × 40 × 5',27,P.ink,true);txt(p,100,905,860,'先将竖片粘在底脚正中，再贴前后加强片。\n黄色箭头表示装配方向，图中间距不是成品尺寸。',25,P.muted);
 txt(p,1140,220,650,'端面 / 装好后的真实厚度',30,P.ink,true);
 const fx=1260,fy=800,k=5;rect(p,fx,fy-25,200,25,'#91ADB5',P.ink,2);rect(p,fx+87.5,fy-400,25,375,'#D8E7E9',P.ink,2);poly(p,[[fx+12.5,fy-25],[fx+87.5,fy-25],[fx+87.5,fy-175]],'#A3BDC3',P.ink,2);
 dh(p,fx,fx+200,850,'40',fy);dh(p,fx,fx+87.5,920,'17.5',fy);dh(p,fx+112.5,fx+200,920,'17.5',fy);dv(p,fy-400,fy,1550,'总高80',fx+200);dv(p,fy-400,fy-25,1690,'竖片75',fx+112.5);
 txt(p,1240,317,450,'竖片厚5',27,P.ink,true);line(p,1358,370,fx+100,fy-390,P.muted,2);txt(p,1150,960,700,'底脚厚5；75 + 5 = 80。\n三角短边15，放得进17.5的侧边空间。',25,P.muted);
 table(p,80,1060,[245,330,285],[['总高','竖片高（厚5时）','对应件'],['60 / 80 / 100','55 / 75 / 95','横墙180长'],['80','75','支墙120长']],25,70);
 stack(p,1020,1080,830,'外围护沿：实木20×30，30朝上','南北各420×3；东西内侧各610×2。\n买1.2米×5根，或1米×7根；不能用6根1米代替。');
 footer(p,'接缝目标：缝≤0.5、高差≤0.2，背面透明胶≤0.1；底板必须由桌面全幅承托。结构胶先试余料并按产品要求固化。');
}
function target(p){header(p,'05','打脱后留在低位｜两套同样做','Ø70轻质软球＋磁吸定位＋细绳限位  ·  只晃动不计分  ·  人工挂回复位');
 const sx=310,gy=1120,k=3.0;const q=(y,z)=>[sx+y*k,gy-z*k];
 const rr=(y,z,w,h,col)=>{const a=q(y,z+h);return rect(p,...a,w*k,h*k,col,P.ink,2);};
 rr(90,0,120,5,'#C6DADD');rr(140,5,20,173,P.wood);rr(-20,178,200,20,P.wood);rr(-5,170,10,8,P.gold);
 ellipse(p,...q(0,135),35*k,P.red,P.red,3,'待击 球心135示例');ellipse(p,...q(40,55),35*k,'#FCEEEB',P.red,3,'低位 球心55');
 line(p,...q(0,170),...q(40,178),P.ink,3);line(p,...q(40,198),...q(87.2,198),P.ink,3);ellipse(p,...q(87.2,200),6,P.ink,null);
 const [dx,dy]=q(40,178),[,ey]=q(40,90);const cord=line(p,dx,dy,dx,ey,P.red,3);cord.dashPattern=[10,8];
 line(p,80,gy,1010,gy,P.ink,3);arrow(p,130,680,130,920,P.red,5);txt(p,70,590,200,'脱开后\n下降',28,P.red,true);
 txt(p,100,240,900,'侧视 / 示例H135、t8，单位mm',31,P.ink,true);txt(p,110,326,900,'臂200长，20×20木条；柱173为计算示例',28,P.ink,true);
 dh(p,...[q(-20,0)[0],q(180,0)[0]],470,'挑臂200',q(0,198)[1]);dv(p,q(0,178)[1],q(0,5)[1],1000,'柱173',q(160,0)[0]);
 dh(p,q(0,0)[0],q(150,0)[0],1220,'球投影 → 柱中心150',gy);dv(p,q(40,20)[1],gy,600,'20',q(40,20)[0]+100);
 txt(p,80,408,420,'待击球心 H=135*',27,P.red,true);line(p,275,450,...q(-25,145),P.muted,2);txt(p,335,960,420,'低位球心55',27,P.red,true);
 txt(p,1150,210,690,'俯视 / 底座全在球后',31,P.ink,true);const tx=1390,ty=638,sc=1.8;
 rect(p,tx-80*sc,ty-210*sc,160*sc,120*sc,'#F4EDDF',P.ink,2,'底座160×120');rect(p,tx-10*sc,ty-160*sc,20*sc,20*sc,P.wood,P.ink,2);line(p,tx,ty,tx,ty-150*sc,P.ink,2);ellipse(p,tx,ty,35*sc,P.red,P.red,2);dh(p,tx-80*sc,tx+80*sc,530,'160',ty-90*sc);dv(p,ty-210*sc,ty-90*sc,1745,'120',tx+80*sc);txt(p,1190,ty+85,650,'球前通行区不放凸起脚座',27,P.ink,true);
 stack(p,1130,805,720,'先实测，再裁柱长','t＝木臂底面到裸球顶的总距离。\n臂底U＝实测球心H＋35＋t。\n柱长＝U−5。例：H135、t8 → U178、柱173。',P.red);
 stack(p,1130,1090,720,'定绳长：把球底垫到20','珠在臂上、结在珠上；珠大于木孔，结大于珠孔。\n球底垫20，止挡珠抵孔上口后锁结。\n绳尾先裁300；不要直接按88裁总绳。');
 txt(p,80,1295,960,'球兜：宽10织带260长×2 / 球；钢圈贴硬帽，硬帽固定在织带上。磁铁留在木臂，不直接粘软球。',25,P.muted);
 footer(p,'*135与173均为示例：两种攻击的扫掠净空、磁力和绳路需试打。以t8计，220柱毛坯建议配H95～182；超范围先改架。');
}
function supplies(p){header(p,'06','采购、粘合、打印｜一次准备齐','采购量是一整套A/B共用  ·  推荐先做一套球靶试打  ·  墙面装饰最后贴');
 const rows=[['材料','整套数量 / 推荐规格'],['PVC发泡雪弗板','1220×2440×5，1张；请店家代切'],['外围实木条','20×30截面：1.2米×5根（或1米×7根）'],['靶架实木条','20×20截面：1米×1根'],['轻质泡棉/海绵球','同款Ø70，红、蓝各1个'],['小磁铁 / 钢垫圈','Ø8×2磁铁4枚；磁性钢圈外径12–16×2'],['织带 / 光滑绳','10宽棉带1.5米；约Ø1细绳1米'],['止挡珠 / 硬帽','外径≥10珠×2；20×20约1厚硬帽×2'],['小L角码','40×40约15宽×4；20×20约15宽×4'],['木螺钉','3×10，约24枚，勿穿出木条'],['胶粘材料','PVC兼容板材胶、高粘薄双面胶、布基胶带'],['透明胶 / 纸边料','≤0.1薄透明胶1卷；纸垫、开放收绳浅槽'],['打印纸','哑面背胶：A4 11张 或 A3 6张']];
 table(p,60,230,[330,820],rows,24,70);
 stack(p,1250,230,610,'打印设置','100% / 实际尺寸\n关闭“适合页面”。\nA3已经双拼，别再每张两页。\n先量100 mm校准线，再印其余页。');
 stack(p,1250,600,610,'需要的工具','钢尺、铅笔、剪刀、美工刀/垫板、砂纸、小钻、螺丝刀。\n预孔钻头1.5–2；绳导孔3–4。\n现场裁柱另需小手锯与夹具。');
 stack(p,1250,970,610,'装配顺序','① 一套球靶试打 → 复制第二套\n② 六底板拼平 → 固定护沿\n③ 竖片＋底脚＋加强片\n④ 按坐标摆墙和靶 → 描出生圈\n⑤ 先玩B，熟悉后再装完整A');
 txt(p,60,1210,1130,'已确认：1260场地可放下、单层平地、红打红/蓝打蓝、命中结果保留、本次手工制作。\n设计选值：5厚板、40宽墙脚、30高护沿、Ø70球。\n待实测：有效击打高度、过缝行走、转弯、磁力、细绳扫掠与围沿稳固。',25,P.muted);
 footer(p,'采购细目与纸质模板见本项目v07 PDF；下方A4/A3画框为可编辑查看稿，出纸仍用已校准的实尺PDF。');
}
const builders=[p=>map(p,'A'),p=>map(p,'B'),cutting,wall,target,supplies];
for(const i of selection){builders[i](panels[i]);changed.push(panels[i].id);}
return {createdNodeIds:ids,mutatedNodeIds:changed,panels:selection.map(i=>({id:panels[i].id,name:panels[i].name,descendants:panels[i].findAll(()=>true).length})),font:'Noto Sans SC',imageFilledNodes:0};

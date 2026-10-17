// Native editable print-art reconstruction from v07. Execute once with use_figma.
// Display scale: 2 px/mm. Print using the existing actual-size PDF, not Figma export.
const page = await figma.getNodeByIdAsync('0:1');
const printSet = __PRINT_SET__;
await figma.setCurrentPageAsync(page);
await Promise.all([
  figma.loadFontAsync({family:'Noto Sans SC',style:'Regular'}),
  figma.loadFontAsync({family:'Noto Sans SC',style:'Bold'})
]);
const roots = await Promise.all(['146:22','146:23'].map(id=>figma.getNodeByIdAsync(id)));
if (roots.some(n=>!n || n.type!=='FRAME')) throw new Error('Expected A4/A3 FRAME roots 146:22 and 146:23.');
if (roots[printSet].children.length) throw new Error('Print root is not empty; inspect canvas before a targeted retry.');
const createdNodeIds=[];
const S=2,PH=297,PT=25.4/72*S;
const C={ink:'#173c47',muted:'#5e727a',pale:'#edf3f2',line:'#cad8db',red:'#d74f48',blue:'#2379cf',yellow:'#f0be50'};
const paint=h=>[{type:'SOLID',color:{r:parseInt(h.slice(1,3),16)/255,g:parseInt(h.slice(3,5),16)/255,b:parseInt(h.slice(5,7),16)/255}}];
function add(p,n,name){p.appendChild(n);n.name=name;createdNodeIds.push(n.id);return n;}
function frame(p,name,x,y,w,h,fill='#ffffff'){const n=add(p,figma.createFrame(),name);n.resize(w,h);n.x=x;n.y=y;n.fills=paint(fill);n.clipsContent=true;return n;}
function rect(p,name,x,y,w,h,fill,stroke=null,weight=.5){const n=add(p,figma.createRectangle(),name);n.resize(w,h);n.x=x;n.y=y;n.fills=fill?paint(fill):[];n.strokes=stroke?paint(stroke):[];n.strokeWeight=weight;return n;}
function vector(p,name,pts,fill=null,stroke=null,weight=.5,closed=false){
  const minX=Math.min(...pts.map(q=>q[0])), minY=Math.min(...pts.map(q=>q[1]));
  const n=add(p,figma.createVector(),name);
  n.vectorPaths=[{windingRule:closed?'NONZERO':'NONE',data:pts.map((q,i)=>(i?'L':'M')+' '+(q[0]-minX)+' '+(q[1]-minY)).join(' ')+(closed?' Z':'')}];
  n.x=minX;n.y=minY;n.fills=fill?paint(fill):[];n.strokes=stroke?paint(stroke):[];n.strokeWeight=weight;return n;
}
function text(p,name,x,y,s,size=16,color=C.ink,bold=false,width=0,align='LEFT'){
  const n=add(p,figma.createText(),name);n.fontName={family:'Noto Sans SC',style:bold?'Bold':'Regular'};n.fontSize=size;n.lineHeight={unit:'PERCENT',value:130};n.fills=paint(color);n.characters=String(s);n.textAlignHorizontal=align;
  if(width){n.resize(width,n.height);n.textAutoResize='HEIGHT';}else n.textAutoResize='WIDTH_AND_HEIGHT';
  n.x=x;n.y=y;return n;
}
// Source coordinates are millimetres from the lower-left of a portrait A4.
const xy=(x,y)=>[x*S,(PH-y)*S];
function ml(p,x,y,a,b,col=C.line,sw=.6,name='线'){return vector(p,name,[xy(x,y),xy(a,b)],null,col,sw*PT);}
function mr(p,x,y,w,h,fill,stroke=null,sw=.6,name='矩形'){return rect(p,name,x*S,(PH-y-h)*S,w*S,h*S,fill,stroke,sw*PT);}
function mt(p,x,y,s,size=9,color=C.ink,bold=false,align='left',name='文字'){
  const w=align==='center'?Math.min(x,210-x)*S*2:align==='right'?x*S:(210-x)*S;
  const xx=align==='center'?x*S-w/2:align==='right'?x*S-w:x*S;
  return text(p,name,xx,(PH-y)*S-size*PT*.96,s,size*PT,color,bold,w,align.toUpperCase());
}
function mc(p,x,y,r,fill,stroke=null,sw=1,name='圆'){const n=add(p,figma.createEllipse(),name);n.resize(r*4,r*4);n.x=(x-r)*S;n.y=(PH-y-r)*S;n.fills=fill?paint(fill):[];n.strokes=stroke?paint(stroke):[];n.strokeWeight=sw*PT;return n;}
function mp(p,pts,fill,name='多边形'){return vector(p,name,pts.map(q=>xy(...q)),fill,null,.5,true);}
function arrow(p,x,y,a,b,color){ml(p,x,y,a,b,color,1.4,'出生朝向');const angle=Math.atan2(b-y,a-x),r=3;mp(p,[[a,b],[a-r*Math.cos(angle-.4),b-r*Math.sin(angle-.4)],[a-r*Math.cos(angle+.4),b-r*Math.sin(angle+.4)]],color,'方向箭头');}
function crops(p,x,y,w,h){for(const [xx,yy,ax,ay] of [[x,y,-1,-1],[x+w,y,1,-1],[x,y+h,-1,1],[x+w,y+h,1,1]]){ml(p,xx+ax*.7,yy,xx+ax*2.2,yy,C.muted,.4,'裁切记号');ml(p,xx,yy+ay*.7,xx,yy+ay*2.2,C.muted,.4,'裁切记号');}}
function arthead(p,num,label){
  mt(p,12,286,String(num).padStart(2,'0')+'  '+label,8,C.ink,true);
  mt(p,198,286,'A4 / 100% / 关闭适合页面',7,C.muted,false,'right');
  ml(p,12,12,112,12,C.ink,.8,'100 mm 校准线');
  for(const x of [12,62,112]) ml(p,x,10.5,x,13.5,C.ink,.7,'校准刻度');
  mt(p,62,6.8,'此线应量得100 mm',6.5,C.muted,false,'center');
  mt(p,198,6.8,'先量尺，再裁切；单面打印',6.5,C.muted,false,'right');
}
function face(p,x,y,w,h,ident){
  const f=frame(p,'贴图 / '+ident+' / '+w+'×'+h+' mm',x*S,(PH-y-h)*S,w*S,h*S,'#284955');
  for(let xx=0;xx<=w;xx+=15) vector(f,'工程格线',[[xx*S,0],[xx*S,(h-7)*S]],null,'#3b5e68',.35*PT);
  for(let yy=15;yy<h;yy+=15) vector(f,'工程格线',[[0,(h-yy)*S],[w*S,(h-yy)*S]],null,'#3b5e68',.35*PT);
  rect(f,'警示带',0,(h-7)*S,w*S,7*S,C.yellow);
  // These vectors are intentionally clipped by the exact sticker boundary.
  for(let xx=-10;xx<w+10;xx+=16) vector(f,'警示斜纹',[[xx*S,h*S],[(xx+6)*S,h*S],[(xx+13)*S,(h-7)*S],[(xx+7)*S,(h-7)*S]],'#263d44',null,.5,true);
  text(f,'CYBER / ARENA',16,24-(w>150?15:13)*PT*.96,'CYBER / ARENA',(w>150?15:13)*PT,'#ffffff',true);
  text(f,'机器人对战场',16,40-8*PT*.96,'机器人对战场',8*PT,'#b7dce2');
  vector(f,'标牌分隔',[[16,(h-14)*S],[(w-8)*S,(h-14)*S]],null,'#8bbdc5',.7*PT);
  text(f,'BATTLE FIELD',16,(h-18)*S-8*PT*.96,'BATTLE FIELD',8*PT,'#cfe7e8',false,(w-16)*S,'RIGHT');
  crops(p,x,y,w,h);
  mt(p,x,y+h+2.2,ident+' 贴面 '+w+' × '+h+'；切实线框；加强片胶位剪开露板',6.5,C.muted);
}
const pages=[];
const specs=[
 {label:'高60墙：4片双面贴图',w:177,h:52,ids:['LH1-正','LH1-背','RH1-正','RH1-背']},
 {label:'高80横墙：8片双面贴图',w:177,h:72,ids:['LH2-正','LH2-背','LH4-正']},
 {label:'高80横墙：8片双面贴图',w:177,h:72,ids:['LH4-背','RH2-正','RH2-背']},
 {label:'高80横墙：8片双面贴图',w:177,h:72,ids:['RH4-正','RH4-背']},
 {label:'高100墙：4片双面贴图',w:177,h:92,ids:['LH3-正','LH3-背']},
 {label:'高100墙：4片双面贴图',w:177,h:92,ids:['RH3-正','RH3-背']},
 {label:'支墙：4片双面贴图',w:117,h:72,ids:['LS-正','LS-背','RS-正']},
 {label:'支墙：4片双面贴图',w:117,h:72,ids:['RS-背']},
 {team:'红',color:C.red},{team:'蓝',color:C.blue},{signs:true}
];
function populate(p,i){
  const spec=specs[i];
  if(spec.ids){arthead(p,i+1,spec.label);spec.ids.forEach((id,k)=>face(p,16.5,271-(k+1)*(spec.h+8)+3,spec.w,spec.h,id));}
  else if(spec.team){
    const col=spec.color,team=spec.team;arthead(p,i+1,team+'方出生圆 / 优先作描线模板');
    mc(p,105,166,90,col,null,1,'出生圈外径 180 mm');mc(p,105,166,82,'#ffffff',null,1,'出生圈内径 164 mm');
    arrow(p,105,147,105,202,col);mt(p,105,127,team+'方出生',21,col,true,'center');mt(p,105,114,team+'方攻击'+team+'球',11,col,false,'center');
    mt(p,105,60,'外径180；内径164。薄贴或按圆描线，不做凸起圆环。',8,C.muted,false,'center');
    mt(p,105,50,'B朝向：红向上 / 蓝向下；摆放时旋转此页方向。',8,C.muted,false,'center');
    mt(p,105,40,'A朝向：红向右 / 蓝向左；箭头朝向随布局转动。',8,C.muted,false,'center');
  } else {
    arthead(p,i+1,'靶座标牌 / 底板背面编号');
    [[C.red,'红','蓝'],[C.blue,'蓝','红']].forEach(([col,team,enemy],j)=>{
      const x=20,y=214-j*62,w=150,h=50;
      mr(p,x,y,w,h,col,col,.6,team+'靶标牌 150×50 mm');
      mt(p,x+8,y+33,team+'方打这颗球',20,'#ffffff',true);mt(p,x+8,y+20,enemy+'方守护  /  脱开磁点并落到低位才计分',8,'#ffffff');
      mt(p,x+8,y+8,'摇晃不算 · 人工挂回复位',9,'#ffffff',true);crops(p,x,y,w,h);
      mt(p,x,y+h+2,'贴在靶座后方或外侧立面；不要贴到球上',6.5,C.muted);
    });
    for(let j=0;j<6;j++){const x=20+(j%3)*52,y=104-Math.floor(j/3)*26;mr(p,x,y,46,20,'#e7eff0',C.line,.6,'F'+(j+1)+'标签 46×20 mm');mt(p,x+23,y+11,'F'+(j+1),13,C.ink,true,'center');mt(p,x+23,y+3,'底板背面编号',6,C.muted,false,'center');crops(p,x,y,46,20);}
    mt(p,20,51,'F1 F2 F3 为南排；F4 F5 F6 为北排，从西向东排列。',8,C.muted);
  }
}
function infoCard(root,x,y,w,heading,body,color=C.ink){
  const n=add(root,figma.createAutoLayout('VERTICAL'),'说明 / '+heading);n.resize(w,100);n.x=x;n.y=y;n.paddingLeft=28;n.paddingRight=28;n.paddingTop=24;n.paddingBottom=24;n.itemSpacing=14;n.fills=paint('#ffffff');n.cornerRadius=12;n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';
  const title=text(n,'说明标题',0,0,heading,28,color,true,w-56);title.layoutSizingHorizontal='FILL';
  const t=text(n,'说明正文',0,0,body,23,C.muted,false,w-56);t.layoutSizingHorizontal='FILL';return n;
}
for(let r=0;r<roots.length;r++){
  if(r!==printSet) continue;
  const root=roots[r];root.fills=paint('#edf3f2');
  text(root,'图板标题',60,28,r?'10 / A3 双拼贴图 · 6 张横向纸':'09 / A4 贴图与模板 · 11 张纵向纸',44,C.ink,true);
  text(root,'比例提示',60,88,'仅作 Figma 查看：2 px = 1 mm。出纸请用同名实尺 PDF；不要从本图板直接打印。',24,C.red,true,2600);
}
for(let i=0;i<11;i++){
  if(printSet!==0) break;
  const p=frame(roots[0],'A4 / '+String(i+1).padStart(2,'0')+' / 210×297 mm',60+(i%6)*450,150+Math.floor(i/6)*624,420,594);
  populate(p,i);pages.push(p);
}
const a3Pages=[];
for(let i=0;i<6;i++){
  if(printSet!==1) break;
  const p=frame(roots[1],'A3 / '+String(i+1).padStart(2,'0')+' / 420×297 mm',60+(i%3)*870,150+Math.floor(i/3)*624,840,594);
  for(let j=0;j<2;j++){
    const source=i*2+j;if(source>=11)continue;
    const half=frame(p,'A4 内容 '+String(source+1).padStart(2,'0')+' / 不缩放',j*420,0,420,594);populate(half,source);
  }
  a3Pages.push(p);
}
for(let r=0;r<2;r++){
  if(r!==printSet) continue;
  const root=roots[r],x=r?2730:2800,w=r?1130:1060;
  let y=150;
  const blocks=[
    ['打印只选一套','A4 11 页，或 A3 横向 6 页。\nA3 已是两张 A4 原比例双拼；\n不要再次设置“每张两页”。',C.ink],
    ['100% 实际尺寸','关闭“适合页面 / 缩放到可打印区域”。\n单面、彩色、哑面背胶纸优先。\n先打一页，量 100 mm 校准线。',C.red],
    ['墙贴 20 片','177 × 52 mm：4 片\n177 × 72 mm：8 片\n177 × 92 mm：4 片\n117 × 72 mm：4 片',C.ink],
    ['圆与标牌','出生圈：外 Ø180 / 内 Ø164，各 1 张\n靶座牌：150 × 50 mm，红蓝各 1\n底板编号：46 × 20 mm，共 6 片',C.ink],
    ['贴之前先做这两件事','墙片胶接加强片的位置剪开，露出板材。\n出生圆优先作描线模板，不做凸起圆环。\nF 编号贴底板背面；标牌不要贴在球上。',C.ink]
  ];
  for(const [h,b,col] of blocks){const card=infoCard(root,x,y,w,h,b,col);y+=card.height+24;}
  if(y>1465) throw new Error('Info cards exceed planned board bounds: '+y);
}
roots[printSet].placeholder=false;
const bounds=[];
for(const root of [roots[printSet]])for(const n of root.children){bounds.push({id:n.id,name:n.name,x:n.x,y:n.y,width:n.width,height:n.height});if(n.x<0||n.y<0||n.x+n.width>root.width+.5||n.y+n.height>root.height+.5)throw new Error('Top-level child out of board: '+n.name);}
return {createdNodeIds,mutatedNodeIds:[roots[printSet].id],A4Pages:pages.map(n=>n.id),A3Pages:a3Pages.map(n=>n.id),wallFacesPerSet:20,displayPixelsPerMM:2,actualPrint:'Existing A4/A3 actual-size PDF only',boundsChecked:bounds.length,rootSize:[3920,1510]};

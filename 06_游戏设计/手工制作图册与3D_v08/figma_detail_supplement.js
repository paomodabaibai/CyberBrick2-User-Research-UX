// Native editable detail boards 11/12. Run once through use_figma.
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('0:1'));
await Promise.all(['Regular','Bold'].map(style=>figma.loadFontAsync({family:'Noto Sans SC',style})));
const root=await figma.getNodeByIdAsync('146:9');
if(!root||root.type!=='FRAME'||root.layoutMode!=='VERTICAL')throw new Error('Expected vertical auto-layout root 146:9. Inspect before retry.');
const ROW_NAME='补充图板 11–12 / 精确坐标与球靶孔位';
if(root.children.some(n=>n.name===ROW_NAME))throw new Error('Supplement row exists. Inspect and target repairs instead of duplicating.');
const ids=[];
const P={ink:'#173C47',muted:'#58727C',line:'#B5C7CB',pale:'#EEF4F4',red:'#D74F48',blue:'#2379CF',gold:'#E9B74A',wood:'#BDA17D',dark:'#284955'};
function rgb(hex){return {r:parseInt(hex.slice(1,3),16)/255,g:parseInt(hex.slice(3,5),16)/255,b:parseInt(hex.slice(5,7),16)/255};}
const fill=c=>[{type:'SOLID',color:rgb(c)}];
function remember(n){ids.push(n.id);return n;}
function rect(p,x,y,w,h,c=P.pale,s=null,sw=1,name='板件'){const n=remember(figma.createRectangle());p.appendChild(n);n.name=name;n.resize(w,h);n.x=x;n.y=y;n.fills=c?fill(c):[];n.strokes=s?fill(s):[];n.strokeWeight=sw;return n;}
function ellipse(p,cx,cy,r,c=null,s=P.ink,sw=2,name='圆'){const n=remember(figma.createEllipse());p.appendChild(n);n.name=name;n.resize(2*r,2*r);n.x=cx-r;n.y=cy-r;n.fills=c?fill(c):[];n.strokes=s?fill(s):[];n.strokeWeight=sw;return n;}
function txt(p,x,y,w,s,size=28,c=P.ink,bold=false){const n=remember(figma.createText());n.fontName={family:'Noto Sans SC',style:bold?'Bold':'Regular'};n.fontSize=size;n.lineHeight={unit:'PERCENT',value:135};n.characters=s;n.resize(w,Math.max(20,size*1.4));n.textAutoResize='HEIGHT';n.fills=fill(c);p.appendChild(n);n.x=x;n.y=y;n.name=s.slice(0,60);return n;}
function poly(p,pts,c=null,s=P.ink,sw=2,closed=true,name='尺寸线'){const minx=Math.min(...pts.map(q=>q[0])),miny=Math.min(...pts.map(q=>q[1]));const n=remember(figma.createVector());p.appendChild(n);n.vectorPaths=[{windingRule:'NONZERO',data:pts.map((q,i)=>(i?'L':'M')+(q[0]-minx)+' '+(q[1]-miny)).join(' ')+(closed?' Z':'')}];n.x=minx;n.y=miny;n.fills=c?fill(c):[];n.strokes=s?fill(s):[];n.strokeWeight=sw;n.name=name;return n;}
const line=(p,x,y,a,b,c=P.line,sw=2)=>poly(p,[[x,y],[a,b]],null,c,sw,false);
function arrow(p,x,y,a,b,c=P.ink,sw=3){line(p,x,y,a,b,c,sw);const q=Math.atan2(b-y,a-x),r=14;poly(p,[[a,b],[a-r*Math.cos(q-.45),b-r*Math.sin(q-.45)],[a-r*Math.cos(q+.45),b-r*Math.sin(q+.45)]],c,null);}
function dh(p,x1,x2,y,label,baseY=null,c=P.muted){if(baseY!==null){line(p,x1,baseY,x1,y+10,c,1);line(p,x2,baseY,x2,y+10,c,1);}line(p,x1,y,x2,y,c,1.5);line(p,x1-5,y+7,x1+5,y-7,c,1.5);line(p,x2-5,y+7,x2+5,y-7,c,1.5);const t=txt(p,(x1+x2)/2-130,y-42,260,label,24,c,true);t.textAlignHorizontal='CENTER';}
function stack(p,x,y,w,title,body,color=P.ink){const n=remember(figma.createAutoLayout('VERTICAL'));p.appendChild(n);n.name=title;n.resize(w,10);n.paddingLeft=22;n.paddingRight=22;n.paddingTop=20;n.paddingBottom=20;n.itemSpacing=12;n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.fills=fill(P.pale);n.x=x;n.y=y;txt(n,0,0,w-44,title,28,color,true);txt(n,0,0,w-44,body,24,P.muted);return n;}
function header(p,num,title,sub){const n=remember(figma.createAutoLayout('VERTICAL'));p.appendChild(n);n.name='图题';n.resize(1808,10);n.itemSpacing=12;n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.fills=[];n.x=60;n.y=40;txt(n,0,0,1808,'CYBERBRICK 2.0  /  手工制作  /  '+num,20,P.muted,true);txt(n,0,0,1808,title,48,P.ink,true);txt(n,0,0,1808,sub,24,P.muted);}
function footer(p,s){line(p,60,1372,1868,1372);txt(p,60,1390,1808,s,20,P.muted);}
function table(p,x,y,widths,rows,font=24,rowH=56){const v=remember(figma.createAutoLayout('VERTICAL'));p.appendChild(v);v.name='精确尺寸表';v.resize(widths.reduce((a,b)=>a+b,0),10);v.itemSpacing=0;v.primaryAxisSizingMode='AUTO';v.counterAxisSizingMode='FIXED';v.fills=[];v.x=x;v.y=y;rows.forEach((row,i)=>{const h=remember(figma.createAutoLayout('HORIZONTAL'));v.appendChild(h);h.resize(widths.reduce((a,b)=>a+b,0),rowH);h.primaryAxisSizingMode='FIXED';h.counterAxisSizingMode='FIXED';h.paddingTop=10;h.paddingBottom=8;h.fills=fill(i===0?P.dark:(i%2?P.pale:'#FFFFFF'));row.forEach((s,j)=>{const cell=remember(figma.createAutoLayout('VERTICAL'));h.appendChild(cell);cell.resize(widths[j],rowH-18);cell.paddingLeft=12;cell.paddingRight=10;cell.primaryAxisSizingMode='FIXED';cell.counterAxisSizingMode='FIXED';cell.fills=[];txt(cell,0,0,widths[j]-22,String(s),font,i===0?'#FFFFFF':P.ink,i===0);});});return v;}

const row=remember(figma.createAutoLayout('HORIZONTAL'));root.appendChild(row);row.name=ROW_NAME;row.resize(3920,1440);row.primaryAxisSizingMode='FIXED';row.counterAxisSizingMode='FIXED';row.itemSpacing=64;row.fills=[];
const boards=[];
for(const [num,title]of [[11,'墙脚坐标与边界'],[12,'木臂孔位与球兜装配']]){const n=remember(figma.createFrame());row.appendChild(n);n.name=String(num)+' / '+title;n.resize(1928,1440);n.fills=fill('#FFFFFF');n.clipsContent=false;boards.push(n);}

// Board 11: all bounding coordinates refer to outer foot/base edges, never wall center lines.
{
 const p=boards[0];
 header(p,'11','墙脚外缘坐标｜照表量，不猜中心线','全部单位 mm  ·  原点O为场地左下角  ·  X向右、Y向上  ·  H为脚座＋竖片的总高');
 const wallRows=[['件号','Xmin','Xmax','Ymin','Ymax','H'],
 ['LH1',20,200,340,380,60],['LH2',200,380,340,380,80],['LH3',380,560,340,380,100],['LH4',560,740,340,380,80],['LS',500,540,380,500,80],
 ['RH1',1060,1240,880,920,60],['RH2',880,1060,880,920,80],['RH3',700,880,880,920,100],['RH4',520,700,880,920,80],['RS',720,760,760,880,80]];
 table(p,60,230,[160,170,170,170,170,150],wallRows,25,70);
 txt(p,1120,230,748,'从同一个O量到脚座外缘',28,P.ink,true);
 txt(p,1120,276,748,'示例 LH2：X200～380；Y340～380。',24,P.muted);
 const ox=1260,oy=650,s=.72;
 arrow(p,ox,oy,1835,oy,P.ink,2);arrow(p,ox,oy,ox,350,P.ink,2);
 txt(p,1790,667,65,'+X',24,P.ink,true);txt(p,1276,337,100,'+Y',24,P.ink,true);txt(p,1110,620,150,'O (0,0)',24,P.ink,true);
 const xx=ox+200*s,yy=oy-380*s,ww=180*s,hh=40*s;
 rect(p,xx,yy,ww,hh,P.dark,P.ink,2,'LH2脚座 / X200–380 / Y340–380');
 txt(p,xx-30,yy-52,240,'LH2 脚座',28,P.ink,true);
 const a=line(p,ox,oy-340*s,xx,oy-340*s,P.muted,1.5);a.dashPattern=[8,6];
 const b=line(p,ox,yy,xx+ww,yy,P.muted,1.5);b.dashPattern=[8,6];
 const c=line(p,xx,oy,xx,yy,P.muted,1.5);c.dashPattern=[8,6];
 const d=line(p,xx+ww,oy,xx+ww,yy,P.muted,1.5);d.dashPattern=[8,6];
 dh(p,ox,xx,720,'Xmin 200',oy);dh(p,ox,xx+ww,790,'Xmax 380',oy);
 line(p,1165,oy,1165,oy-340*s,P.muted,1.5);line(p,1160,oy,1170,oy,P.muted,1.5);line(p,1160,oy-340*s,1170,oy-340*s,P.muted,1.5);
 txt(p,1100,535,150,'Ymin\n340',24,P.muted,true);
 line(p,1750,oy,1750,yy,P.muted,1.5);line(p,1745,oy,1755,oy,P.muted,1.5);line(p,1745,yy,1755,yy,P.muted,1.5);line(p,xx+ww,yy,1750,yy,P.line,1);
 txt(p,1770,490,90,'Ymax\n380',24,P.muted,true);
 txt(p,60,1030,990,'两块靶座占地 / 不包含球前通行区',28,P.ink,true);
 table(p,60,1080,[250,185,185,185,185],[['对象','Xmin','Xmax','Ymin','Ymax'],['红靶座',180,340,740,860],['蓝靶座',920,1080,400,520]],25,70);
 stack(p,1120,1140,748,'A / B 朝向和拆件','A：红朝 +X，蓝朝 −X；装全10段。\nB：红朝 +Y，蓝朝 −Y；移除\nLH1/2/3、RH1/2/3连同底脚。');
 stack(p,1120,860,748,'四边护沿外缘 / 四角不重叠','南：X 0～1260；Y 0～20\n北：X 0～1260；Y 1240～1260\n西：X 0～20；Y 20～1240\n东：X 1240～1260；Y 20～1240\n木条截面20×30：30向上，20占地。');
 footer(p,'坐标是制作标称值；胶厚与裁切偏差现场复核。B拆墙时底脚同时拿走，入口净宽480。完整数值以v07 README为准。');
}

// Board 12: arm measured from its physical front end; a separate exploded view explains the load path.
{
 const p=boards[1];
 header(p,'12','球靶局部尺寸｜孔、磁点、布兜怎么装','全部单位 mm  ·  挑臂20×20木条，长200  ·  尺寸从臂前端0量  ·  两套采用相同做法');
 txt(p,90,230,1060,'木臂俯视 / 虚线表示底面部件',28,P.ink,true);
 const x=140,y=330,k=5;
 rect(p,x,y,200*k,20*k,P.wood,P.ink,2,'木臂 200×20 俯视');
 line(p,x,y+50,x+1000,y+50,P.muted,1.5).dashPattern=[10,7];
 const magnet=ellipse(p,x+20*k,y+50,4*k,null,P.red,3,'底面磁铁 Ø8×2 / 前端距20');magnet.dashPattern=[5,4];
 ellipse(p,x+60*k,y+50,1.75*k,'#FFFFFF',P.ink,2,'导孔 Ø3–4 / 前端距60');
 const post=rect(p,x+160*k,y,20*k,20*k,null,P.ink,3,'底面柱顶20×20 / 中心170');post.dashPattern=[8,5];
 txt(p,150,278,240,'前端 0',24,P.ink,true);txt(p,385,278,260,'导孔 Ø3～4',24,P.ink,true);txt(p,880,278,270,'底面柱顶20×20',24,P.ink,true);
 txt(p,145,438,220,'磁点在底面',20,P.red,true);
 dh(p,x,x+1000,475,'臂全长 200',y+100);dh(p,x,x+100,530,'20',y+100,P.red);dh(p,x,x+300,585,'导孔 60',y+100);dh(p,x,x+850,640,'柱中心 170',y+100);
 txt(p,1230,230,630,'局部侧向 / 导孔贯通臂厚',28,P.ink,true);
 rect(p,1260,330,510,70,P.wood,P.ink,2,'局部木臂侧向');
 rect(p,1316,400,28,7,P.red,P.red,1,'磁铁留臂底');
 line(p,1450,310,1450,400,P.ink,3);line(p,1450,400,1420,458,P.ink,3);
 ellipse(p,1450,320,7,P.gold,P.ink,2,'臂上止挡珠');
 poly(p,[[1445,308],[1455,308],[1450,303]],P.ink,P.ink,1,true,'绳结');
 txt(p,1230,270,610,'上：珠在臂上、结在珠上',24,P.muted);txt(p,1230,480,620,'下：磁铁固定并包封；钢圈贴硬帽。\n磁点太强时，逐层加薄纸调吸力。',24,P.muted);
 line(p,1810,330,1810,400,P.muted,1.5);line(p,1805,330,1815,330,P.muted,1.5);line(p,1805,400,1815,400,P.muted,1.5);txt(p,1825,347,60,'20',24,P.muted,true);
 txt(p,1230,570,620,'从球投影量：导孔后40，后柱中心后150。\n这些是局部几何尺寸，实际扫掠净空仍要试打。',24,P.muted);
 line(p,60,680,1868,680,P.line,2);
 txt(p,60,705,910,'磁点与正交球兜 / 分开示意',28,P.ink,true);
 rect(p,247,780,66,16,P.red,P.red,1,'磁铁 Ø8×2 留在臂上');
 line(p,280,801,280,826,P.line,2).dashPattern=[5,4];
 ellipse(p,280,855,32,'#9FAFB2',P.ink,2,'钢垫圈外径12–16');ellipse(p,280,855,9,'#FFFFFF',P.ink,1,'钢圈孔3–4');
 line(p,280,891,280,915,P.line,2).dashPattern=[5,4];
 rect(p,230,925,100,10,'#E5EDEB',P.ink,2,'硬帽20×20约1厚');
 poly(p,[[247,941],[247,1000],[280,1030],[313,1000],[313,941]],null,P.gold,9,false,'织带顶端与球兜连接');
 ellipse(p,280,1140,100,P.red,P.red,2,'Ø70轻球');
 for(const sign of [-1,1]){const pts=Array.from({length:65},(_,i)=>{const a=i*Math.PI*2/64;return [280+66*Math.sin(a),1140-95*Math.cos(a)+sign*30*Math.sin(a)];});poly(p,pts,null,'#F6D48B',9,true,'经球顶与球底的正交承重织带 '+sign);}
 poly(p,[[320,951],[345,951],[375,1000],[420,1000]],null,P.ink,3,false,'细绳系帽旁织带');ellipse(p,320,951,5,P.ink,null,1,'系绳点');
 txt(p,440,760,500,'磁铁 Ø8 × 2 留在臂上',24,P.red,true);
 txt(p,440,830,500,'钢垫圈 外Ø12～16 / 孔Ø3～4\n钢圈随硬帽、球兜和球下落。',24,P.muted);
 txt(p,440,925,500,'硬帽 20 × 20，约1厚\n粘牢顶部织带；钢圈跨压胶带。',24,P.muted);
 txt(p,440,1010,500,'绳系帽旁织带\n承重走整圈布兜，不只粘软球皮。',24,P.muted);
 txt(p,440,1110,500,'织带 10 × 260，每球2段\n两圈正交，顶部重叠约40。\n底部交叉处也用布基胶带包牢。',24,P.muted);
 txt(p,100,1280,850,'球色使用本色或少量色带，不把软球包成厚硬纸壳。',24,P.muted);
 stack(p,1010,705,858,'角码与固定 / 每套','柱脚：40×40，左右各1（共2）。\n臂柱：20×20，前后各1（共2）。\n木螺钉3×10；预孔Ø1.5～2。\n按角码实孔定位，勿对穿或碰钉。\n靶座：薄高粘双面胶＋布基胶带跨压。');
 stack(p,1010,1000,858,'绳先裁300，再以低位调定','球底垫到20，珠抵导孔上口后锁结。\n珠≥Ø10且大于导孔；结大于珠孔。\n孔下88、上方余绳约47仅为示例。\n不可按88裁总绳；余绳收于臂顶开放浅槽。',P.red);
 txt(p,1010,1250,858,'巴掌不得勾绳；只晃动不计分。\nH135、U178、柱173为示例，按实机调整。',24,P.muted);
 footer(p,'球兜图为装配示意，间距不是成品尺寸。先完成一套试打再复制；臂高、磁力和绳路按实机调整。数值以v07 README为准。');
}

const bounds=boards.map(n=>({id:n.id,name:n.name,width:n.width,height:n.height,descendants:n.findAll(()=>true).length}));
const outOfBoard=[];
for(const board of boards){for(const child of board.children){if(child.x<-1||child.y<-1||child.x+child.width>board.width+1||child.y+child.height>board.height+1)outOfBoard.push({id:child.id,name:child.name,x:child.x,y:child.y,w:child.width,h:child.height});}}
return {createdNodeIds:ids,mutatedNodeIds:[root.id],rowId:row.id,boards:bounds,outOfBoard,font:'Noto Sans SC',imageFilledNodes:0,source:'v07 README',dimensions:'mm'};

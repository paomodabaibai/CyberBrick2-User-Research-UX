await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('0:1'));
await Promise.all(['Regular','Bold'].map(style=>figma.loadFontAsync({family:'Noto Sans SC',style})));
const view=__VIEW__, anchors=__ANCHORS__;
const parent=await figma.getNodeByIdAsync(view==='A'?'146:20':'146:21');
if(parent.children.length) throw new Error('3D panel is not empty; inspect before retry');
const ids=[];const rgb=h=>({r:parseInt(h.slice(1,3),16)/255,g:parseInt(h.slice(3,5),16)/255,b:parseInt(h.slice(5,7),16)/255});
const paint=h=>[{type:'SOLID',color:rgb(h)}];
const ink='#173C47',muted='#58727C',red='#D74F48',blue='#2379CF';
function text(p,x,y,w,s,size=26,color=ink,bold=false){const n=figma.createText();ids.push(n.id);n.fontName={family:'Noto Sans SC',style:bold?'Bold':'Regular'};n.fontSize=size;n.lineHeight={unit:'PERCENT',value:135};n.characters=s;n.resize(w,size*1.4);n.textAutoResize='HEIGHT';n.fills=paint(color);p.appendChild(n);n.x=x;n.y=y;n.name=s.slice(0,40);return n;}
function line(a,b,c=muted,width=2){const x=Math.min(a[0],b[0]),y=Math.min(a[1],b[1]);const n=figma.createVector();ids.push(n.id);parent.appendChild(n);n.vectorPaths=[{windingRule:'NONZERO',data:`M${a[0]-x} ${a[1]-y} L${b[0]-x} ${b[1]-y}`}];n.fills=[];n.strokes=paint(c);n.strokeWeight=width;n.x=x;n.y=y;n.name='引线 / 尺寸线';return n;}
function note(x,y,w,head,body,color=ink){const f=figma.createAutoLayout('VERTICAL');ids.push(f.id);parent.appendChild(f);f.name=head;f.resize(w,10);f.paddingLeft=f.paddingRight=20;f.paddingTop=f.paddingBottom=18;f.itemSpacing=12;f.primaryAxisSizingMode='AUTO';f.counterAxisSizingMode='FIXED';f.fills=paint('#EEF4F4');f.x=x;f.y=y;text(f,0,0,w-40,head,29,color,true);text(f,0,0,w-40,body,24,muted);}
const art=figma.createFrame();parent.appendChild(art);art.name='可编辑3D矢量 / 手工布局'+view;art.resize(1408,968);art.x=60;art.y=280;art.fills=[];art.clipsContent=false;ids.push(art.id);
const pt=k=>anchors[k].pixel_xy.map((v,i)=>v*.88+(i?280:60));
function dim(a,b,off,label){const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy),nx=-dy/len,ny=dx/len;const A=[a[0]+nx*off,a[1]+ny*off],B=[b[0]+nx*off,b[1]+ny*off];line(a,[A[0]+nx*8,A[1]+ny*8]);line(b,[B[0]+nx*8,B[1]+ny*8]);line(A,B);for(const q of[A,B])line([q[0]-5,q[1]+6],[q[0]+5,q[1]-6]);const t=text(parent,(A[0]+B[0])/2-85,(A[1]+B[1])/2-35,170,label,28,ink,true);t.textAlignHorizontal='CENTER';}
const O=pt('origin'),X=pt('x_end'),Y=pt('y_end'),Z=[X[0]+Y[0]-O[0],X[1]+Y[1]-O[1]];
dim(O,X,62,'1260');dim(X,Z,62,'1260');
text(parent,60,40,1808,'CYBERBRICK 2.0  /  手工制作  /  '+(view==='A'?'07':'08'),20,muted,true);
text(parent,60,82,1808,view==='A'?'整体3D A｜10段墙装齐':'整体3D B｜拆6段墙，留宽口',48,ink,true);
text(parent,60,156,1808,'单层平地，全部底板由桌面承托；3D展示装配关系，不代表已完成实机测试。单位mm。',24,muted);
text(parent,70,245,1200,view==='A'?'原图完整墙 · 六块平板 · 两套脱落球靶':'低转向摆法 · 同一套材料 · 改墙位就能复玩',28,ink,true);
for(let i=1;i<=6;i++){const q=pt('floor_f'+i);text(parent,i===5?973:q[0]-20,i===5?690:q[1]+18,80,'F'+i,20,muted,true);}
note(1470,245,390,'底板 ×6','每块420×630×5\n3列×2行＝1260方形\n地面没有高架或桥。');
note(1470,500,390,'主墙与护沿',view==='A'?'墙总高60 / 80 / 100\n竖片厚5，脚座宽40\n护沿20占地×30高。':'保留 LH4、LS、RH4、RS\n两侧入口净宽480\n护沿20占地×30高。');
note(1470,785,390,'球靶（示例）','软球Ø70，球心135*\n臂20×20×200\n柱20×20×173*\n底座160×120×5。',red);
note(1470,1115,390,'命中后','脱开磁点 → 降到低位\n球底离地20\n结果保留，人工复位。');
const rb=pt('red_ball'),bb=pt('blue_ball');
text(parent,90,355,430,'红方打红球 / 蓝方守护',27,red,true);line([435,402],[rb[0]-12,rb[1]-20],red,2);
text(parent,1000,350,430,'蓝方打蓝球 / 红方守护',27,blue,true);line([1280,405],[bb[0]+20,bb[1]-20],blue,2);
if(view==='A'){const q=pt('high_wall');text(parent,85,945,370,'高低墙60 / 80 / 100',25,ink,true);line([410,980],[q[0]-20,q[1]+12],muted,2);}else{dim(pt('gate_left'),pt('gate_right'),30,'净宽480');}
line([60,1372],[1868,1372]);text(parent,60,1390,1808,'*135球心与173柱长为模型参考；先测两种攻击的高度和扫掠，再调磁点、柱长与绳路。',20,muted);
return {createdNodeIds:ids,mutatedNodeIds:[parent.id],panelId:parent.id,artId:art.id,descendants:parent.findAll(()=>true).length,dimensions:'1260 square; floor 420x630x5; ball H135 example',imageFilledNodes:0};

// Targeted, repeatable repair after the first composition screenshot.
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('0:1'));
const root=await figma.getNodeByIdAsync('146:9');
const texts=root.findAllWithCriteria({types:['TEXT']});
const fonts=new Map();
for(const n of texts) for(const s of n.getStyledTextSegments(['fontName'])) fonts.set(JSON.stringify(s.fontName),s.fontName);
await Promise.all([...fonts.values()].map(f=>figma.loadFontAsync(f)));
const changed=[];
for(const n of texts){n.textAutoResize='HEIGHT';changed.push(n.id);}
async function setLine(id,a,b){const n=await figma.getNodeByIdAsync(id);const x=Math.min(a[0],b[0]),y=Math.min(a[1],b[1]);n.vectorPaths=[{windingRule:'NONZERO',data:`M ${a[0]-x} ${a[1]-y} L ${b[0]-x} ${b[1]-y}`}];n.x=x;n.y=y;changed.push(id);}
for(const ids of [['147:71','147:72','147:73','147:74','147:75','147:76'],['147:198','147:199','147:200','147:201','147:202','147:203']]){
 await setLine(ids[0],[154,250],[154,246]);await setLine(ids[1],[1036,250],[1036,246]);
 await setLine(ids[2],[154,236],[1036,236]);await setLine(ids[3],[149,243],[159,229]);await setLine(ids[4],[1031,243],[1041,229]);
 const label=await figma.getNodeByIdAsync(ids[5]);label.y=194;
}
for(const id of ['146:11','146:12']){const p=await figma.getNodeByIdAsync(id);for(const t of p.findAllWithCriteria({types:['TEXT']})) if(/^F[1-6]  420×630$/.test(t.characters)){t.characters=t.characters.slice(0,2);t.name=t.characters;}}
const foot=await figma.getNodeByIdAsync('147:417');foot.x=790;foot.y=810;foot.fontSize=27;foot.resize(310,40);foot.textAutoResize='HEIGHT';
const topHead=await figma.getNodeByIdAsync('147:530');topHead.y=210;
await setLine('147:535',[1246,476],[1246,540]);await setLine('147:536',[1534,476],[1534,540]);
await setLine('147:537',[1246,530],[1534,530]);await setLine('147:538',[1241,537],[1251,523]);await setLine('147:539',[1529,537],[1539,523]);
const d160=await figma.getNodeByIdAsync('147:540');d160.y=488;
const high=await figma.getNodeByIdAsync('151:48');high.y=945;
await setLine('151:49',[410,980],[540.6474,814.3467]);
const counts={};for(const n of root.findAll(()=>true))counts[n.type]=(counts[n.type]||0)+1;
const overflows=texts.filter(n=>n.x+n.width>n.parent.width+1||n.y+n.height>n.parent.height+1).map(n=>({id:n.id,text:n.characters,x:n.x,y:n.y,w:n.width,h:n.height,parent:n.parent.id,pw:n.parent.width,ph:n.parent.height}));
return {mutatedNodeIds:[...new Set(changed)],counts,textCount:texts.length,fonts:[...fonts.values()],overflows,root:{id:root.id,width:root.width,height:root.height}};

const fs = require('fs');
const path = require('path');
const {Document,Packer,Paragraph,TextRun,Footer,PageNumber,AlignmentType,HeadingLevel}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/docx');
const stem='milk_ARENA门店活动执行计划_v02_2026-11-03';
const text=fs.readFileSync(path.join(__dirname,stem+'.md'),'utf8');
const paragraphs=[];
let newPage=false;
for (const line of text.split(/\r?\n/)) {
 if(!line.trim()) continue;
 if(line==='<!-- page -->'){newPage=true;continue;}
 const title=line.startsWith('# '), subtitle=line.startsWith('## '), section=/^[一二三四五六七八九十]+、/.test(line), timeline=/^\d\d:\d\d—/.test(line);
 const clean=line.replace(/^##? /,'');
 paragraphs.push(new Paragraph({
  pageBreakBefore:newPage,keepNext:title||subtitle||section||timeline,
  heading:title?HeadingLevel.TITLE:section?HeadingLevel.HEADING_1:undefined,
  spacing:{before:section?140:timeline?70:0,after:title?100:subtitle?110:50,line:title?460:subtitle?340:section?340:300,lineRule:'exact'},
  children:[new TextRun({text:clean,bold:title||subtitle||section||timeline,size:title?36:subtitle?24:section?25:21,color:'182C3D',font:'微软雅黑'})]
 }));
 newPage=false;
}
const doc=new Document({creator:'milk组',title:'milk ARENA 拓竹门店活动执行计划',styles:{default:{document:{run:{font:'微软雅黑',size:21},paragraph:{spacing:{line:285}}}}},sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:850,bottom:850,left:1000,right:1000}}},footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[new TextRun({text:'milk ARENA｜2026.11.03 审核稿   ',size:18,color:'666666'}),new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},children:paragraphs}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync(path.join(__dirname,stem+'.docx'),b);console.log('DOCX saved',b.length);});

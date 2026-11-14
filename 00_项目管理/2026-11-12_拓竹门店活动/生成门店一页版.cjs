const fs=require('fs'),path=require('path');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,BorderStyle}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/docx');
const stem='milk_ARENA活动计划_门店一页版_v03_2026-11-04';
const text=fs.readFileSync(path.join(__dirname,stem+'.md'),'utf8');
const p=(s,opts={})=>new Paragraph({spacing:{before:0,after:55,line:285,lineRule:'exact'},...opts,children:[new TextRun({text:s,font:'微软雅黑',size:21,color:'183044',...(opts.run||{})})]});
const children=[];const rows=[];let tableDone=false;
function emitTable(){
 if(tableDone||!rows.length)return;
 const widths=[2350,7556];
 const border={style:BorderStyle.SINGLE,size:4,color:'D5DFE7'};
 children.push(new Table({width:{size:9906,type:WidthType.DXA},columnWidths:widths,rows:[['时段','安排'],...rows].map((r,i)=>new TableRow({cantSplit:true,tableHeader:i===0,children:r.map((s,j)=>new TableCell({width:{size:widths[j],type:WidthType.DXA},margins:{top:55,bottom:55,left:100,right:100},borders:{top:border,bottom:border,left:border,right:border},shading:{type:ShadingType.CLEAR,fill:i===0?'E7F0F5':'FFFFFF'},children:[p(s,{spacing:{after:0,line:270,lineRule:'exact'},run:{size:20,bold:i===0}})]}))}))}));tableDone=true;
}
for(const line of text.split(/\r?\n/)){
 if(!line.trim()||line==='门店活动计划 · 一页版'||line==='以下以正式开场为0分钟。')continue;
 if(/^(开场前|\d+—\d+分钟|结束后0—10分钟)/.test(line)){const split=line.indexOf('｜');rows.push([line.slice(0,split),line.slice(split+1)]);continue;}
 if(rows.length&&!tableDone)emitTable();
 if(line.startsWith('# ')){children.push(p(line.slice(2),{spacing:{after:120,line:420,lineRule:'exact'},run:{size:32,bold:true}}));continue;}
 const heading=/^[一二三]、/.test(line),em=line.startsWith('时间预留：');
 children.push(p(line,{keepNext:heading,spacing:{before:heading?100:0,after:55,line:heading?310:285,lineRule:'exact'},run:{bold:heading||em,size:heading?23:line.startsWith('2026年')?17:21,color:line.startsWith('2026年')?'687987':'183044'}}));
}
const doc=new Document({creator:'milk组',title:'milk ARENA门店活动计划一页版',sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:750,bottom:750,left:1000,right:1000}}},children}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync(path.join(__dirname,stem+'.docx'),b);console.log('DOCX saved');});

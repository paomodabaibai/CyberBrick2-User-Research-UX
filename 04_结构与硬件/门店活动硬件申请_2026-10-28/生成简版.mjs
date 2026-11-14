import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url));
const wb=Workbook.create();
const s=wb.worksheets.add('硬件需求表');s.showGridLines=false;
s.getRange('A1:B1').merge();s.getRange('A1').values=[['棋甲对决 · 硬件需求表']];
s.getRange('A2:B2').merge();s.getRange('A2').values=[['红色为优先需求；其他配件有则提供，没有可不提供。']];
const rows=[
['180°位置舵机（含配套舵盘及固定螺钉）',20,'只'],
['360°连续旋转舵机（含配套舵盘及固定螺钉）',3,'只'],
['CyberBrick 1 配套机器人电池',8,'套'],
['CyberBrick 1 电源开关 XA007／SW101（含配套供电线）',7,'套'],
['CyberBrick 1 配套电池固定配件／电池盒',4,'套'],
['CyberBrick 1 配套电池充电器及充电线',2,'套'],
['CyberBrick 1 D1接口转舵机三针接口转接线',3,'条'],
['M3×8mm机器螺丝',20,'颗'],['M3×10mm机器螺丝',20,'颗'],['M3×12mm机器螺丝',20,'颗'],
['M3×16mm低头机器螺丝',10,'颗'],['M3×20mm低头机器螺丝',10,'颗'],['M3×25mm低头机器螺丝',10,'颗'],
['M3普通六角螺母',40,'颗'],['M3防松螺母',20,'颗'],['M3平垫片',60,'片'],
['M3用间隔垫／隔套（厚约2mm）',12,'个'],['小号尼龙扎带（宽约2–2.5mm）',50,'根']];
s.getRange('A4:B4').values=[['物品详细名称','需要数量']];
s.getRange('A5:B22').values=rows.map(r=>r.slice(0,2));
s.getRange('A1:B22').format.font={name:'Arial',size:12,color:'#222222'};
s.getRange('A1:B22').format.verticalAlignment='center';
s.getRange('A1:A22').format.columnWidth=73;s.getRange('B1:B22').format.columnWidth=16;
s.getRange('A1:B1').format.rowHeight=38;s.getRange('A1').format.font={name:'Arial',size:18,bold:true};
s.getRange('A2:B2').format.rowHeight=30;s.getRange('A2').format.font={name:'Arial',size:11,color:'#666666'};
s.getRange('A4:B22').format.rowHeight=34;
s.getRange('A4:B4').format.fill='#253D50';s.getRange('A4:B4').format.font={name:'Arial',size:12,bold:true,color:'#FFFFFF'};
s.getRange('B4:B22').format.horizontalAlignment='center';
rows.forEach((r,i)=>{s.getRange(`B${i+5}`).setNumberFormat(`0"${r[2]}"`);if(i%2===0)s.getRange(`A${i+5}:B${i+5}`).format.fill='#F3F5F7';});
s.getRange('A5:B7').format.font={name:'Arial',size:12,bold:true,color:'#D51D2C'};
s.freezePanes.freezeRows(4);
await wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:'硬件需求表',range:'A5:B7',maxChars:800})).ndjson);
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(dir,'拓竹硬件需求表_简版.xlsx'));
const png=await wb.render({sheetName:'硬件需求表',range:'A1:B22',scale:1,format:'png'});
await fs.writeFile(path.join(dir,'简版检查.png'),new Uint8Array(await png.arrayBuffer()));

import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir=path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1'));
const out=decodeURIComponent(dir);
const wb=Workbook.create();
const s=wb.worksheets.add('发货需求表');s.showGridLines=false;
s.getRange('A2').values=[['棋甲对决 门店活动硬件需求表']];
s.getRange('A3').values=[['活动：2026年11月12日下午；现有2台，新增4台，总计红蓝各3台。场景与遥控器硬件不列入申请。']];
s.getRange('A4').values=[['本表由拓竹供货；20只180°、3只连续旋转舵机已确认，其余为建议补充，请确认后发货。']];
s.getRange('A5').values=[['收件人、电话、地址及到货日期：另行提供。舵机具体型号、尺寸和插头由双方确认。']];
const header=['序号','物料名称','规格与接口要求','装机/使用','备用','申请数量','单位','数量状态','用途与发货说明'];
s.getRange('A7:I7').values=[header];
const data=[
 [1,'180°位置舵机','180°定位型；优先按SG90意向，核对CB1接线与Otto安装',16,4,null,'只','已确认','新增4台各4只＋备用4只。此前拟用SG90；请确认供货型号，其他型号须先核对安装尺寸。'],
 [2,'360°连续旋转舵机','可持续正反转，回中停转；非360°位置型',2,1,null,'只','已确认','新增两台巴掌机各1只，另备1只；配合已验证D1转接和供电方案。'],
 [3,'机器人配套电池','与CB1接收端、电池盒、插头和充电方式匹配',4,4,null,'套','建议确认','新增4台装机4套，另4套轮换；按机器人用电池计，不重复申请遥控器电池。'],
 [4,'电池盒/电池固定配件','与申请电池和CB1接收端匹配',4,0,null,'套','库存待核对','供新增4台，已有则不重复；电源开关另列，避免漏发。'],
 [5,'巴掌D1舵机转接线','CB1 D1端至所配连续旋转舵机，确认S/V/G顺序',2,1,null,'条','建议确认','新增两台巴掌机＋1条备用；请按既有有效接法核对，不凭插头外形配线。'],
 [6,'配套充电设备及供电线','按所供电池的官方充电方案配置',2,0,null,'套','充电方式待确认','供轮换充电；如电池盒已有充电功能或现有设备足够，可取消或改发对应供电线。'],
 [7,'舵盘及原配固定螺钉','匹配所供20只位置舵机＋3只连续旋转舵机',23,0,null,'套','随舵机配套','每只舵机至少配所需舵盘、中心螺钉及安装螺钉；已包含则不另算一批舵机。'],
 [8,'M3机器螺丝组合','M3×8/10/12各20，M3×16/20/25各10；铰点优先低头',90,0,null,'颗','建议，有货请配','备料量，非最终逐孔BOM；六台装配/升级共用，新版结构确认后核定长度。'],
 [9,'M3普通六角螺母','配M3机器螺丝；供可拆结构螺母槽',40,0,null,'颗','建议，有货请配','用于身体与顶部模块等固定；不要用舵机中心螺钉替代。'],
 [10,'M3防松螺母','用于拳头曲柄和连杆活动铰点',20,0,null,'颗','建议，有货请配','与垫片/隔套配合，拧紧后仍应保留关节转动自由度。'],
 [11,'M3平垫片','匹配M3螺丝',60,0,null,'片','建议，有货请配','固定点和活动铰点备用；实际叠层厚度决定螺钉长度。'],
 [12,'M3间隔垫/隔套','通孔适配M3，约2mm厚；外径待避碰核对',12,0,null,'个','建议，有货请配','三台拳头共6处铰点，额外备6个；可按最终尺寸打印替代。'],
 [13,'CB1物理电源开关模块','XA007/SW101，XH2.54 2Pin；配两端供电线',6,1,null,'套','建议按缺口配发','六台各1＋备用1，扣除可用现货；与电池串联，非K4按钮。官方许用3A，需核对总负载。'],
 [14,'小扎带','宽约2–2.5mm，长度按理线和电机固定需求配',50,0,null,'根','建议，有货请配','内部线束和电机固定备用；不勒压端子与运动机构。'],];
s.getRange(`A8:I${7+data.length}`).values=data;
for(let i=0;i<data.length;i++)s.getRange(`F${8+i}`).formulas=[[`=SUM(D${8+i}:E${8+i})`]];
const end=7+data.length;
s.getRange(`A7:I${end}`).format.font={name:'Arial',size:11,color:'#222222'};
s.getRange(`A7:I${end}`).format.verticalAlignment='center';
s.getRange(`A8:I${end}`).format.wrapText=true;
s.getRange(`A8:I${end}`).format.rowHeight=69;
s.getRange('A7:I7').format.fill='#263B50';s.getRange('A7:I7').format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};
s.getRange('A7:I7').format.rowHeight=30;s.getRange('A7:I7').format.horizontalAlignment='center';
s.getRange('A2').format.font={name:'Arial',size:16,bold:true};
s.getRange('A3:A5').format.font={name:'Arial',size:11,color:'#444444'};
const widths={A:7,B:24,C:41,D:11,E:8,F:11,G:7,H:18,I:58};
for(const [c,width]of Object.entries(widths))s.getRange(`${c}1:${c}${end}`).format.columnWidth=width;
s.getRange(`D8:F${end}`).setNumberFormat('0');s.getRange(`D8:G${end}`).format.horizontalAlignment='center';
s.getRange(`F8:F${end}`).format.font={name:'Arial',size:11,bold:true};
s.getRange('H10:H13').format.fill='#FFF0CB';
for(let row=8;row<=end;row++)if(row%2===0)s.getRange(`A${row}:G${row}`).format.fill='#F1F4F7';
s.freezePanes.freezeRows(7);
const t=wb.worksheets.add('发送前核对');t.showGridLines=false;
t.getRange('A2').values=[['发送前核对与待补物料']];
t.getRange('A3').values=[['以下不计入已确定发货数量。先核对库存，仅缺少时再加入申请。']];
t.getRange('A5:F5').values=[['项目','新增最低需求','单位','当前状态','需要确认的内容','处理建议']];
const checks=[
 ['机器人接收端＋驱动底板',4,'套','未清点','遥控器硬件齐全不必然包含机器人接收端','确认新增4台都配齐，避免只收到舵机却无法控制'],
 ['拳头电机＋完整减速机构',2,'套','未清点','现有成功实机使用的电机、减速器和输出轴型号','已有则不申请；缺少时整套补发，不能只有裸电机'],
 ['Ø3×64mm光滑导杆',4,'根','未清点','两台新增拳头机各2根；此前已购数量待核对','现货足够则不用发'],
 ['信号、供电和延长线',null,'批','未清点','四台新增机器人内部接线是否齐全，长度、端子和线序','优先原厂匹配线；按实际缺口补，不默认每只舵机一条转接'],
 ['M2附件及M3补充规格',null,'批','已有一盒，需配套','活动铰点用防松螺母与间隔垫；舵机中心螺钉随原配','M3已列主表建议备料量；核对现货后扣减，M2按旧巴掌连接件另核对'],
 ['电池数量与充电方案',8,'套','建议，待确认','申请8套是否够、是否含电池盒、是否能独立换电','4套新增装机＋4套轮换；电池盒和充电设备不重复计数'],
 ['舵机型号与机械适配',null,'项','待确认','腿部180°位置型；巴掌连续旋转型；实物尺寸、舵盘及插头','请拓竹先确认型号/尺寸；不要沿用此前30只统一换新的旧口径'],
 ['发货联系人与地址',null,'项','待填写','收件人、电话、地址、预计到货日','留出活动前装配和调试时间，由双方确认日期'],
];
t.getRange(`A6:F${5+checks.length}`).values=checks;
t.getRange(`A5:F${5+checks.length}`).format.font={name:'Arial',size:11,color:'#222222'};t.getRange(`A6:F${5+checks.length}`).format.wrapText=true;t.getRange(`A6:F${5+checks.length}`).format.rowHeight=66;t.getRange(`A5:F${5+checks.length}`).format.verticalAlignment='center';t.getRange('A5:F5').format.fill='#263B50';t.getRange('A5:F5').format.font={name:'Arial',size:11,color:'#FFFFFF',bold:true};t.getRange('A5:F5').format.horizontalAlignment='center';t.getRange('A2').format.font={name:'Arial',size:16,bold:true};t.getRange('A3').format.font={name:'Arial',size:11,color:'#444444'};
for(const [c,width]of Object.entries({A:30,B:16,C:8,D:24,E:56,F:58}))t.getRange(`${c}1:${c}14`).format.columnWidth=width;
t.getRange('B6:B13').setNumberFormat('0');t.getRange('B6:C13').format.horizontalAlignment='center';
await wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:'发货需求表',range:'A7:I10',maxChars:1600,tableMaxCols:9})).ndjson);
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(out,'拓竹门店活动_硬件发货需求表_2026-10-28.xlsx'));
try{const preview=await wb.render({sheetName:'发货需求表',range:'A2:I21',scale:1,format:'png'});await fs.writeFile(path.join(out,'申请表检查.png'),new Uint8Array(await preview.arrayBuffer()));console.log('RENDER_OK');}catch(e){console.log('RENDER_FAILED',String(e).slice(0,220));}
console.log('OUTPUT',out);



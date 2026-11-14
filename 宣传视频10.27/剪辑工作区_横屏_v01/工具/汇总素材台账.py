from pathlib import Path
import json,html
W=Path(__file__).resolve().parents[1]
rows=json.loads((W/'01_素材分析/视频音频清单.json').read_text(encoding='utf8'))
notes={
 'V01':('打印过程','屏幕拍摄打印过程，6秒。可作制作氛围，不将其当成特定零件的打印证明。','备选'),
 'V02':('完整双机对战','横屏全场，两个操控者与球靶同框；含走位、对抗和调试停顿。优先挑43秒后或其他稳定动作，不照搬故障对白。','重点'),
 'V03':('巴掌特写','竖拍，巴掌旋转与机器人近景；约2.5—6.5秒较干净，后段有手机伸入。','重点'),
 'V04':('拳头移动与击球','横拍红色机器人通过场地接近球靶；68.5—73.5秒可见接触及球体脱落。适合真实操作闭环。','重点'),
 'V05':('近身对战与战舞','竖拍双机交锋，含身体倒下、人工扶正和玩笑；约72秒附近提到胜利舞蹈。可取短动作，不剪成不存在的全程稳定性。','重点'),
 'V06':('近距离双机交锋','竖拍，手部曾介入复位；可挑无人手遮挡的几秒。','备选'),
 'V07':('拳头攻击特写','竖拍低机位拳头往复，手柄操控者可见；后段接近灯光，有眩光。','重点'),
 'V08':('巴掌功能近景','竖拍，由远到近展示巴掌，机位晃动较明显。','备选'),
 'V09':('课堂环境','早期课堂全景与投影，非最终产品使用场景；一分钟成果片优先级低。','过程'),
 'V10':('课堂人物镜头','早期同学侧面聊天，机器人不在画面主体。','不优先'),
 'V11':('课堂人物与操作','同学在桌边操作手机与电脑，可作过程，但不当最终遥控功能证明。','过程'),
 'V12':('课堂人物镜头','等待、交谈与转头，成果演示关联较弱。','不优先'),
 'V13':('课堂人物镜头','早期课堂人物表情与聊天，最终片不必使用。','不优先'),
 'V14':('套件开箱','课堂上拿取组件与包装，可用于开箱、制作起点。','过程'),
 'V15':('课堂讨论','无音轨，拿取组件与同学互动。','过程'),
 'V16':('课堂讨论','无音轨，几位组员在桌边交流。','过程'),
 'V17':('早期组装与设计讨论','31分37秒长实录，包含卡牌/桌游设想、无线与主板数量、套件约束、外观、腿部和两类攻击机构讨论，伴随组装。杂谈较多，不宜作为成片旁白。','过程'),
 'V18':('巴掌装配讲解','约3分钟，桌边组装巴掌、连接件和舵机，有接近镜头的手部细节。','过程'),
 'V19':('巴掌装配短镜头','2秒，无音轨。适合作为制作过程一闪而过的插入镜头。','重点'),
 'V20':('团队装配','10秒，无音轨。两位组员在桌前安装身体与巴掌。','过程'),
 'V21':('团队调试','约7秒，无音轨。桌面零件与组员操作，可拼制作蒙太奇。','过程'),
 'V22':('规则讲解与比赛','开头约0—26秒讲述红蓝双方从起点穿过中场、接近对应球靶，过程中可以阻拦对手。讲解者对胜负表述有即时修正；约38秒倒计时开始，后段近身交锋。','重点'),
 'V23':('巴掌近景','竖拍，机器人由远到近，约7—11秒有挥掌近景，镜头有倾斜。','备选'),
 'V24':('配套界面原型录屏','无可识别讲话，手机界面展示发现、发布、商品/组件、机器人操作等设计。仅标界面原型，不声称真实交易或手机控机器人已实现。','可单独展示'),
 'V25':('早期遥控联调','书桌上用紫色手柄控制巴掌机器人，电脑与代码同框。可说明真实开发调试过程。','过程'),
 'V26':('重复文件','与V25逐字节相同，复用V25转写和画面索引；不删除原件。','重复'),
 'V27':('汇报与老师反馈录音','约24分42秒。包含场地运输与简化、活动/课程、玩法扩展、模块与社区界面、耐玩性与产品易用性等讨论，后段有现场试玩声音。老师建议及未来方案与实机已完成能力需分开。','资料依据'),
 'V28':('真人围观试玩竖机位','多人围桌、操作紫色手柄，含笑声与教学、倒下及扶正。适合呈现场景与上手过程。','重点'),
 'V29':('真人操控短镜头','约2.6秒竖拍，操控者、手柄与场地同框。','备选'),
 'V30':('真人围观试玩横机位','约2分44秒，全场与人物同框，围观者笑声和反应丰富；约80—90秒适合表现真实参与感。','重点'),
 'V31':('遥控教学压缩版','竖拍短镜头，组员指导新操作者；与V32是相近事件不同文件。','备选'),
 'V32':('遥控教学原始版','短片，紫色手柄交到另一位同学手上，旁边有人指导和观看；适合说明可以换人玩。','重点')}
text=['# 逐个素材内容摘要','', '本次共32个视频/音频文件，约83.4分钟。新文件夹26个，项目补充6个。1份逐字节重复，5份无音轨；26份独立有声音素材已完成本地机器转写。','',
 '画面检查采用逐文件带时间码抽样，重点片段进一步密集采帧；不是全部83分钟逐帧通看。机器转写尚未逐字听校，专有名词、多人对白与噪声段需复核。原始文件不删除、不改名。','',
 '## 建议优先讨论的剪辑方向','',
 '1. 成果演示：双人操控 → 走位 → 巴掌与拳头 → 击球脱落 → 真人试玩。以V04、V22、V30为骨架。',
 '2. 制作故事：用V14/V17—V21和照片解释从零件到两台机器，成片需要更多时长。',
 '3. 完整项目介绍：增加配套界面原型与未来玩法，但明确它们的验证状态。',
 '当前60秒仅为可修改结构参考，未锁定成片长度。先看摘要与参考，再确定时长。','']
cards=[]
for r in rows:
 id=r['id'];title,summary,tag=notes[id]
 txt=W/'02_逐段转写'/f'{id}.txt';trans=txt.read_text(encoding='utf8') if txt.exists() else '暂无转写文件'
 text += [f"## {id} {title}",f"- 文件：{r['name']}",f"- 时长：{r['duration']:.1f}秒；优先级：{tag}",f'- 内容：{summary}',f"- 原件：{r['path']}",f'- 转写：02_逐段转写/{id}.txt','']
 image=W/'01_素材分析'/f'{id}_画面索引.jpg'
 if not image.exists() and r.get('duplicate_of'):image=W/'01_素材分析'/f"{r['duplicate_of']}_画面索引.jpg"
 img=f'<a href="{image.as_uri()}"><img loading="lazy" src="{image.as_uri()}" alt="{id}画面抽样"></a>' if image.exists() else '<p class="empty">音频资料</p>'
 cards.append(f'''<article data-search="{html.escape(id+' '+title+' '+tag+' '+summary)}"><header><b>{id} · {html.escape(title)}</b><span>{r['duration']:.1f}s · {tag}</span></header><p>{html.escape(summary)}</p>{img}<details><summary>展开带时间码转写</summary><pre>{html.escape(trans)}</pre></details><p class="path">{html.escape(r['path'])}</p><a href="{Path(r['path']).as_uri()}">打开原素材</a></article>''')
(W/'逐个素材内容摘要.md').write_text('\n'.join(text),encoding='utf8')
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>棋甲对决 素材审阅</title><style>body{margin:0;background:#101724;color:#e5edf8;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1200px;margin:auto;padding:28px}h1{font-size:32px}input{box-sizing:border-box;width:100%;padding:14px;background:#202e42;color:white;border:1px solid #678;border-radius:8px}article{background:#1b2738;border-radius:12px;padding:24px;margin:22px 0}header{display:flex;justify-content:space-between;gap:20px}header b{font-size:22px}header span{color:#8be0df}img{max-width:100%;max-height:660px;display:block;margin:12px auto}a{color:#8be0df}pre{white-space:pre-wrap;font:14px/1.7 "Microsoft YaHei";max-height:460px;overflow:auto;padding:16px;background:#101724}.path{font-size:12px;color:#9ba9ba;overflow-wrap:anywhere}video{width:100%;max-height:650px}.notice{background:#25364d;padding:18px;border-radius:10px}.empty{padding:30px;text-align:center}</style><main><h1>棋甲对决 素材审阅</h1><p>32个视频/音频文件 · 本地机器转写 · 逐文件画面抽样</p><p class="notice">时长尚未定稿。下面的60秒只是讨论结构与素材取舍的参考；正式交付以达芬奇分轨时间线继续修改。机器转写未逐字听校。Figma中的NFC、绕障竞速等属于后续设想。</p><h2>结构参考 非定稿</h2><video controls preload="metadata" src="PREVIEW"></video><p>没有添加新配音或商业配乐。保留轻量现场声，标题可在工程里调整；当前预览与原生Text+的排版可能稍有不同。</p><h2>逐条素材</h2><input id="search" placeholder="搜索：击球 / 试玩 / 巴掌 / 装配 / V04"><section>CARDS</section><script>document.querySelector('#search').addEventListener('input',e=>{let q=e.target.value.toLowerCase();document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.search.toLowerCase().includes(q))})</script></main></html>'''
page=page.replace('PREVIEW',(W/'06_预览/横屏结构参考_60秒_非定稿.mp4').as_uri()).replace('CARDS',''.join(cards))
(W/'先看这里_素材审阅.html').write_text(page,encoding='utf8')
print('Summary and review page created')

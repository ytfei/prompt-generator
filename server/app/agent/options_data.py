"""14 维度选项定义与内置预设（与 PRD 5.1 / docs/PRD.md 对齐）。

由 GET /api/options 下发给前端，是选项系统的唯一数据源。
prompt 字段为写入最终提示词的片段；ratio 字段为用途推荐的画幅。
"""

GROUPS: dict[str, dict] = {
    "usage": {
        "name": "🎯 用途场景",
        "hint": "决定推荐的画幅比例",
        "multi": False,
        "options": [
            {"label": "公众号首图", "prompt": "适配公众号头图的横幅封面构图，视觉冲击力强", "ratio": "2.35:1"},
            {"label": "公众号次图", "prompt": "正文内嵌插图，构图完整独立", "ratio": "1:1"},
            {"label": "文章配图", "prompt": "正文宽幅插图，与文字内容呼应", "ratio": "16:9"},
            {"label": "海报封面", "prompt": "竖版海报构图，信息层次分明", "ratio": "3:4"},
            {"label": "自由创作", "prompt": "", "ratio": ""},
        ],
    },
    "ratio": {
        "name": "📐 画幅比例",
        "hint": "选用途后自动推荐，可手动修改",
        "multi": False,
        "options": [
            {"label": r, "prompt": "", "ratio": r}
            for r in ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "2.35:1"]
        ],
    },
    "style": {
        "name": "🎨 画面风格",
        "hint": "决定整体视觉语言",
        "multi": False,
        "options": [
            {"label": "写实摄影", "prompt": "超写实摄影风格，画面逼真如专业单反拍摄", "ratio": ""},
            {"label": "电影感", "prompt": "电影级画面质感，戏剧化打光与叙事感构图", "ratio": ""},
            {"label": "日系动漫", "prompt": "日系动漫插画风格，线条干净色彩清新", "ratio": ""},
            {"label": "国风水墨", "prompt": "中国水墨画风，写意笔触与留白意境", "ratio": ""},
            {"label": "新中式插画", "prompt": "新中式国风插画，传统元素现代表达", "ratio": ""},
            {"label": "扁平插画", "prompt": "扁平化矢量插画，几何形状与简洁色块", "ratio": ""},
            {"label": "手绘水彩", "prompt": "水彩手绘风格，颜料晕染通透自然", "ratio": ""},
            {"label": "3D渲染", "prompt": "C4D三维渲染风格，立体精致富有体积感", "ratio": ""},
            {"label": "黏土风", "prompt": "黏土定格动画质感，手工捏制可爱圆润", "ratio": ""},
            {"label": "毛毡布艺", "prompt": "羊毛毡布艺质感，毛茸茸温暖柔软", "ratio": ""},
            {"label": "像素艺术", "prompt": "复古像素艺术风格", "ratio": ""},
            {"label": "赛博朋克", "prompt": "赛博朋克风格，霓虹光与未来都市", "ratio": ""},
            {"label": "蒸汽波", "prompt": "蒸汽波美学，复古电子与迷幻色彩", "ratio": ""},
            {"label": "极简主义", "prompt": "极简主义风格，元素克制构图干净", "ratio": ""},
            {"label": "超现实主义", "prompt": "超现实主义风格，梦幻荒诞充满想象", "ratio": ""},
            {"label": "油画", "prompt": "古典油画风格，厚重笔触层次丰富", "ratio": ""},
            {"label": "儿童绘本", "prompt": "儿童绘本插画风格，温暖童趣", "ratio": ""},
            {"label": "商业摄影", "prompt": "高端商业摄影风格，产品级精致布光", "ratio": ""},
            {"label": "胶片摄影", "prompt": "135胶片摄影质感，颗粒细腻，色调温润怀旧", "ratio": ""},
            {"label": "微缩世界", "prompt": "微缩模型摄影风格，移轴镜头下的精致小人国场景", "ratio": ""},
            {"label": "等距插画", "prompt": "等距视角2.5D插画，几何模块化场景，细节丰富", "ratio": ""},
            {"label": "线描艺术", "prompt": "极简线条画，单色细线勾勒，大量留白", "ratio": ""},
            {"label": "木刻版画", "prompt": "木刻版画风格，粗犷刀痕与高对比黑白", "ratio": ""},
            {"label": "剪纸风", "prompt": "多层剪纸拼贴风格，层叠纸张与柔和投影", "ratio": ""},
            {"label": "双重曝光", "prompt": "双重曝光效果，剪影与景象交融叠影，虚实相生", "ratio": ""},
            {"label": "拼贴艺术", "prompt": "复古拼贴艺术，剪报纹理与错位元素，荒诞趣味", "ratio": ""},
            {"label": "蒸汽朋克", "prompt": "蒸汽朋克风格，黄铜齿轮与蒸汽机械，维多利亚质感", "ratio": ""},
            {"label": "暗黑奇幻", "prompt": "暗黑奇幻风格，哥特式阴郁氛围与神秘光影", "ratio": ""},
            {"label": "概念艺术", "prompt": "影视概念艺术风格，宏大场景设定，氛围细腻", "ratio": ""},
            {"label": "低多边形", "prompt": "Low Poly 低多边形风格，几何面块与渐变光影", "ratio": ""},
            {"label": "霓虹灯管", "prompt": "霓虹灯管艺术，发光线条勾勒，暗背景高对比", "ratio": ""},
            {"label": "大理石雕塑", "prompt": "大理石雕塑质感，古典造型与石材纹理，庄重而永恒", "ratio": ""},
            {"label": "长曝光", "prompt": "长曝光摄影，丝绢般的水流与云轨，时间流动感", "ratio": ""},
            {"label": "炭笔素描", "prompt": "炭笔素描风格，粗粝笔触与丰富的灰阶层次", "ratio": ""},
        ],
    },
    "genre": {
        "name": "🏛 艺术流派参考",
        "hint": "叠加在风格之上的美学参照",
        "multi": False,
        "options": [
            {"label": "印象派", "prompt": "印象派光影笔触，莫奈式笔意", "ratio": ""},
            {"label": "浮世绘", "prompt": "日本浮世绘版画风格", "ratio": ""},
            {"label": "包豪斯", "prompt": "包豪斯设计语言，几何与功能之美", "ratio": ""},
            {"label": "孟菲斯", "prompt": "孟菲斯设计风格，明快撞色与趣味图形", "ratio": ""},
            {"label": "波普艺术", "prompt": "波普艺术风格，高饱和复制感", "ratio": ""},
            {"label": "敦煌壁画", "prompt": "敦煌壁画风格，矿物色彩与飘逸线条", "ratio": ""},
            {"label": "瑞士国际主义", "prompt": "瑞士国际主义美学，网格与秩序感", "ratio": ""},
            {"label": "新艺术运动", "prompt": "新艺术运动风格，有机曲线与装饰纹样", "ratio": ""},
            {"label": "装饰艺术", "prompt": "Art Deco 装饰艺术风格，对称几何与金色线条，奢华摩登", "ratio": ""},
            {"label": "表现主义", "prompt": "表现主义风格，粗犷扭曲的笔触与浓烈色彩，蒙克式情绪张力", "ratio": ""},
            {"label": "抽象表现主义", "prompt": "抽象表现主义，泼洒滴流的行动绘画肌理，波洛克式", "ratio": ""},
            {"label": "色域绘画", "prompt": "色域绘画风格，大面积色块朦胧晕染边界，罗斯科式沉浸感", "ratio": ""},
            {"label": "象征主义", "prompt": "象征主义风格，隐喻与梦境意象并置，神秘而有暗示性", "ratio": ""},
            {"label": "浪漫主义", "prompt": "浪漫主义风格，戏剧性的天空与崇高自然，透纳式光影", "ratio": ""},
            {"label": "巴洛克", "prompt": "巴洛克风格，强烈的明暗对比与华丽细节，卡拉瓦乔式戏剧感", "ratio": ""},
            {"label": "立体主义", "prompt": "立体主义风格，多视角几何解构与拼贴，毕加索式", "ratio": ""},
            {"label": "未来主义", "prompt": "未来主义风格，速度线与动能爆发，充满运动张力", "ratio": ""},
            {"label": "构成主义", "prompt": "构成主义风格，几何色块与对角线构图，海报式视觉张力", "ratio": ""},
            {"label": "点彩派", "prompt": "点彩派风格，细密并置的色点在远处融合成画，修拉式", "ratio": ""},
            {"label": "拜占庭马赛克", "prompt": "拜占庭马赛克风格，金底镶嵌拼贴，庄严的仪式感", "ratio": ""},
            {"label": "波斯细密画", "prompt": "波斯细密画风格，精密图案与浓郁矿物色，平面装饰性构图", "ratio": ""},
            {"label": "侘寂美学", "prompt": "侘寂美学，不完美与无常之美，朴素幽寂的留白", "ratio": ""},
            {"label": "街头涂鸦", "prompt": "街头涂鸦风格，喷绘肌理与大胆撞色，叛逆的街道能量", "ratio": ""},
        ],
    },
    "mood": {
        "name": "🌡 情绪氛围",
        "hint": "画面的情绪温度",
        "multi": False,
        "options": [
            {"label": "治愈温暖", "prompt": "氛围治愈温暖，令人安心", "ratio": ""},
            {"label": "宁静平和", "prompt": "宁静平和，安静舒缓", "ratio": ""},
            {"label": "欢快活力", "prompt": "欢快有活力，充满生机", "ratio": ""},
            {"label": "浪漫梦幻", "prompt": "浪漫梦幻，柔和唯美", "ratio": ""},
            {"label": "忧郁孤独", "prompt": "情绪忧郁孤独，安静中带一丝落寞", "ratio": ""},
            {"label": "神秘悬疑", "prompt": "神秘悬疑，引人探究", "ratio": ""},
            {"label": "紧张压迫", "prompt": "紧张有压迫感，张力十足", "ratio": ""},
            {"label": "史诗恢弘", "prompt": "史诗般恢弘大气", "ratio": ""},
            {"label": "科幻冷感", "prompt": "冷静克制的科技未来感", "ratio": ""},
            {"label": "怀旧复古", "prompt": "怀旧复古，带年代记忆感", "ratio": ""},
            {"label": "幽默趣味", "prompt": "幽默诙谐，轻松有趣", "ratio": ""},
            {"label": "蓄势待发", "prompt": "静默中蕴含巨大张力，如满弓待发，一触即发", "ratio": ""},
            {"label": "希望微光", "prompt": "黑暗中透出一缕微光，充满转机与希望", "ratio": ""},
            {"label": "凯旋胜利", "prompt": "荣耀高光的胜利时刻，意气风发", "ratio": ""},
            {"label": "焦虑不安", "prompt": "躁动纷乱，心绪不宁的紧绷感", "ratio": ""},
            {"label": "悲壮苍凉", "prompt": "苍茫辽阔中带着悲壮与寂寥", "ratio": ""},
            {"label": "迷茫彷徨", "prompt": "方向未知的恍惚与不安，雾中前行", "ratio": ""},
            {"label": "空灵禅意", "prompt": "超脱空灵，禅意悠远，物我两忘", "ratio": ""},
            {"label": "孤高冷傲", "prompt": "清冷孤高，遗世独立的疏离感", "ratio": ""},
            {"label": "荒诞超脱", "prompt": "超现实的荒诞感，冷静旁观世间荒谬", "ratio": ""},
            {"label": "庄严肃穆", "prompt": "庄重肃穆，带有仪式感与敬畏感", "ratio": ""},
            {"label": "热血激燃", "prompt": "热血沸腾的燃系能量，斗志昂扬", "ratio": ""},
            {"label": "疲惫倦怠", "prompt": "倦怠低电量，慢下来的疲惫与松弛", "ratio": ""},
            {"label": "甜美软萌", "prompt": "软萌甜美，粉嫩可爱的治愈感", "ratio": ""},
            {"label": "诡异惊悚", "prompt": "背脊发凉的诡异与阴森，似有暗流涌动", "ratio": ""},
        ],
    },
    "light": {
        "name": "💡 光线",
        "hint": "对出图质感影响极大",
        "multi": False,
        "options": [
            {"label": "黄金时刻", "prompt": "清晨或黄昏黄金时刻的光线，柔和金黄", "ratio": ""},
            {"label": "蓝调时刻", "prompt": "蓝调时刻的清冷天光", "ratio": ""},
            {"label": "自然柔光", "prompt": "自然柔光，明亮通透", "ratio": ""},
            {"label": "逆光剪影", "prompt": "逆光剪影，轮廓发光", "ratio": ""},
            {"label": "伦勃朗光", "prompt": "伦勃朗式侧光，立体而富有戏剧性", "ratio": ""},
            {"label": "影棚布光", "prompt": "影棚专业布光，主体突出背景干净", "ratio": ""},
            {"label": "霓虹灯光", "prompt": "霓虹灯光晕染，色彩迷离", "ratio": ""},
            {"label": "烛光暖光", "prompt": "烛光暖光，昏黄温馨", "ratio": ""},
            {"label": "月光清辉", "prompt": "清冷月光静静洒落", "ratio": ""},
            {"label": "体积光", "prompt": "体积光丁达尔效应，光束穿透感", "ratio": ""},
            {"label": "正午硬光", "prompt": "正午硬光，阴影锐利对比强烈", "ratio": ""},
        ],
    },
    "tone": {
        "name": "🌈 色调配色",
        "hint": "",
        "multi": False,
        "options": [
            {"label": "自然真实", "prompt": "色调自然真实，还原肉眼观感", "ratio": ""},
            {"label": "暖调", "prompt": "整体暖色调，橙黄为主", "ratio": ""},
            {"label": "冷调", "prompt": "整体冷色调，蓝青为主", "ratio": ""},
            {"label": "高饱和", "prompt": "高饱和浓郁色彩，视觉冲击力强", "ratio": ""},
            {"label": "低饱和莫兰迪", "prompt": "低饱和莫兰迪色系，高级柔和", "ratio": ""},
            {"label": "黑白单色", "prompt": "黑白单色，质感纯粹", "ratio": ""},
            {"label": "胶片复古", "prompt": "复古胶片色调，颗粒与暖调褪色感", "ratio": ""},
            {"label": "霓虹撞色", "prompt": "霓虹撞色，互补色强烈碰撞", "ratio": ""},
            {"label": "同色系渐变", "prompt": "同色系渐变过渡，和谐统一", "ratio": ""},
        ],
    },
    "comp": {
        "name": "🖼 构图",
        "hint": "",
        "multi": False,
        "options": [
            {"label": "居中构图", "prompt": "主体居中构图，稳定聚焦", "ratio": ""},
            {"label": "三分法", "prompt": "三分法构图，主体置于黄金分割点", "ratio": ""},
            {"label": "对称构图", "prompt": "对称构图，秩序感强", "ratio": ""},
            {"label": "引导线", "prompt": "引导线构图，视线汇聚向主体", "ratio": ""},
            {"label": "框架式", "prompt": "框架式构图，前景包裹主体", "ratio": ""},
            {"label": "大面积留白", "prompt": "大面积留白，主体精炼突出", "ratio": ""},
            {"label": "对角线", "prompt": "对角线构图，动感十足", "ratio": ""},
            {"label": "重复图案", "prompt": "重复图案构图，富有韵律感", "ratio": ""},
        ],
    },
    "shot": {
        "name": "🔎 景别与视角",
        "hint": "",
        "multi": False,
        "options": [
            {"label": "微距", "prompt": "微距视角，细节纤毫毕现", "ratio": ""},
            {"label": "特写", "prompt": "特写镜头，主体充满画面", "ratio": ""},
            {"label": "近景", "prompt": "近景景别", "ratio": ""},
            {"label": "中景", "prompt": "中景景别", "ratio": ""},
            {"label": "全景", "prompt": "全景画面", "ratio": ""},
            {"label": "远景大场面", "prompt": "远景大场面，气势开阔", "ratio": ""},
            {"label": "俯视", "prompt": "俯视角度拍摄", "ratio": ""},
            {"label": "鸟瞰", "prompt": "高空鸟瞰视角", "ratio": ""},
            {"label": "仰视", "prompt": "仰视角度，主体显得高大", "ratio": ""},
            {"label": "平视", "prompt": "平视视角，自然亲切", "ratio": ""},
            {"label": "第一人称", "prompt": "第一人称主观视角", "ratio": ""},
        ],
    },
    "bg": {
        "name": "🏞 背景环境",
        "hint": "",
        "multi": False,
        "options": [
            {"label": "纯色背景", "prompt": "纯色简约背景", "ratio": ""},
            {"label": "渐变背景", "prompt": "柔和渐变背景", "ratio": ""},
            {"label": "虚化光斑", "prompt": "背景虚化，焦外光斑柔和", "ratio": ""},
            {"label": "室内场景", "prompt": "室内场景，富有生活气息", "ratio": ""},
            {"label": "自然户外", "prompt": "自然户外环境，山川草木", "ratio": ""},
            {"label": "城市街景", "prompt": "城市街景，人间烟火气", "ratio": ""},
            {"label": "抽象几何", "prompt": "抽象几何背景，现代感强", "ratio": ""},
            {"label": "桌面工作台", "prompt": "整洁的桌面工作台场景", "ratio": ""},
            {"label": "星空宇宙", "prompt": "星空宇宙背景，深邃浩瀚", "ratio": ""},
            {"label": "水下世界", "prompt": "水下世界，光影摇曳", "ratio": ""},
        ],
    },
    "texture": {
        "name": "🧵 质感材质",
        "hint": "",
        "multi": False,
        "options": [
            {"label": "哑光", "prompt": "哑光质感，细腻不反光", "ratio": ""},
            {"label": "光泽", "prompt": "光泽质感，反光通透", "ratio": ""},
            {"label": "金属", "prompt": "金属质感，冷峻坚硬", "ratio": ""},
            {"label": "玻璃", "prompt": "玻璃质感，晶莹剔透", "ratio": ""},
            {"label": "木质", "prompt": "木质纹理，温润自然", "ratio": ""},
            {"label": "织物", "prompt": "织物纹理，柔软亲肤", "ratio": ""},
            {"label": "纸张", "prompt": "纸张肌理，手作温度感", "ratio": ""},
            {"label": "胶片颗粒", "prompt": "胶片颗粒质感", "ratio": ""},
            {"label": "平滑数字", "prompt": "平滑数字质感，干净利落", "ratio": ""},
        ],
    },
    "text": {
        "name": "✏️ 文字与留白",
        "hint": "公众号配图常需预留标题位",
        "multi": False,
        "options": [
            {"label": "无文字要求", "prompt": "", "ratio": ""},
            {"label": "留白放标题", "prompt": "画面预留干净的留白区域，方便后期叠加标题文字", "ratio": ""},
            {"label": "含标题文字", "prompt": "画面中包含清晰的标题文字，字体设计精致、无乱码", "ratio": ""},
            {"label": "少量点缀文字", "prompt": "画面中含少量点缀性文字元素", "ratio": ""},
        ],
    },
    "creative": {
        "name": "🎲 创意自由度",
        "hint": "控制 Agent 的发挥程度",
        "multi": False,
        "options": [
            {"label": "严格遵循", "prompt": "严格依据上述描述呈现，不做额外发挥", "ratio": ""},
            {"label": "平衡", "prompt": "", "ratio": ""},
            {"label": "充分发挥", "prompt": "在保持主题的前提下，大胆补充富有想象力的细节", "ratio": ""},
        ],
    },
    "negative": {
        "name": "🚫 排除内容",
        "hint": "可多选",
        "multi": True,
        "options": [
            {"label": "文字乱码", "prompt": "画面中不出现乱码文字", "ratio": ""},
            {"label": "水印", "prompt": "无水印、无logo", "ratio": ""},
            {"label": "低质量", "prompt": "无模糊、无噪点、无低质量细节", "ratio": ""},
            {"label": "肢体畸形", "prompt": "人物肢体结构正常自然", "ratio": ""},
            {"label": "过度复杂", "prompt": "画面不过度杂乱，主体清晰", "ratio": ""},
        ],
    },
}

_PRESET_BASE = {
    "usage": "公众号首图",
    "ratio": "2.35:1",
    "text": "留白放标题",
    "negative": ["文字乱码", "水印", "低质量"],
}


def _fin(key: str, label: str, theme_hint: str, **overrides) -> dict:
    """财经行情首图预设：首图规格 + 主题提示语（暗示涨跌等语义由主题传达）。"""
    sel = {**_PRESET_BASE, "creative": "充分发挥"}
    sel.update(overrides.pop("selections_extra", {}))
    return {
        "key": key,
        "label": label,
        "category": "财经行情首图",
        "theme_hint": theme_hint,
        "selections": sel,
    }


PRESETS: list[dict] = [
    {
        "key": "tech",
        "label": "公众号 · 科技感封面",
        "category": "通用",
        "selections": {
            "usage": "公众号首图",
            "ratio": "2.35:1",
            "style": "3D渲染",
            "mood": "科幻冷感",
            "light": "体积光",
            "tone": "霓虹撞色",
            "comp": "居中构图",
            "bg": "抽象几何",
            "texture": "光泽",
            "text": "留白放标题",
            "creative": "充分发挥",
            "negative": ["水印", "低质量"],
        },
    },
    {
        "key": "warm",
        "label": "公众号 · 治愈插画",
        "category": "通用",
        "selections": {
            "usage": "文章配图",
            "ratio": "16:9",
            "style": "手绘水彩",
            "mood": "治愈温暖",
            "light": "黄金时刻",
            "tone": "暖调",
            "comp": "大面积留白",
            "shot": "中景",
            "bg": "自然户外",
            "texture": "纸张",
            "text": "留白放标题",
            "creative": "平衡",
            "negative": ["文字乱码", "水印", "低质量"],
        },
    },
    {
        "key": "photo",
        "label": "公众号 · 写实摄影配图",
        "category": "通用",
        "selections": {
            "usage": "公众号次图",
            "ratio": "1:1",
            "style": "写实摄影",
            "mood": "怀旧复古",
            "light": "自然柔光",
            "tone": "胶片复古",
            "comp": "三分法",
            "shot": "中景",
            "bg": "虚化光斑",
            "texture": "胶片颗粒",
            "text": "无文字要求",
            "creative": "平衡",
            "negative": ["水印", "低质量", "肢体畸形"],
        },
    },
    # ── 财经行情首图（涨）：亢奋 / 生长 / 苏醒 ──
    _fin(
        "fin-bull-run", "牛市狂奔 · 红色热情",
        "一望无际的原野上，千万朵红花在同一瞬间迸裂绽放，花瓣裹挟着热浪向天空翻涌而上，"
        "炽烈、膨胀、势不可挡的欢腾感，画面以炽热的红色与金色为主调",
        selections_extra={
            "style": "超现实主义", "mood": "史诗恢弘", "light": "黄金时刻",
            "tone": "高饱和", "comp": "对角线", "bg": "自然户外", "texture": "光泽",
        },
    ),
    _fin(
        "fin-golden-stairs", "稳健上行 · 拔节生长",
        "雨后的竹林里，新笋顶开泥土层层拔节，晨光穿透薄雾洒在湿润的土地上，"
        "安静而笃定的生长力量，节节向上的秩序感",
        selections_extra={
            "style": "新中式插画", "mood": "治愈温暖", "light": "黄金时刻",
            "tone": "暖调", "comp": "引导线", "bg": "自然户外", "texture": "纸张",
        },
    ),
    _fin(
        "fin-thaw", "触底回暖 · 破冰晨光",
        "漫长寒冬后的第一缕暖阳照在雪原上，冰棱尖端悬着一滴将落未落的水珠，"
        "石缝里一点嫩绿顶开残雪，微距镜头下的苏醒瞬间，冷与暖在画面中交汇",
        selections_extra={
            "style": "写实摄影", "mood": "治愈温暖", "light": "黄金时刻",
            "tone": "暖调", "shot": "特写", "comp": "居中构图",
            "bg": "自然户外", "texture": "玻璃",
        },
    ),
    # ── 财经行情首图（跌）：失重 / 消逝 ──
    _fin(
        "fin-crash", "暴跌恐慌 · 悬坠瞬间",
        "倾覆的水晶吊灯从高空坠落，在触地前的瞬间被定格，无数碎片向四周炸开又悬停半空，"
        "冷蓝色的光从裂缝里漏出来，失重、尖锐、屏住呼吸的恐慌感",
        selections_extra={
            "style": "超现实主义", "mood": "紧张压迫", "light": "蓝调时刻",
            "tone": "冷调", "comp": "居中构图", "bg": "渐变背景", "texture": "玻璃",
        },
    ),
    _fin(
        "fin-grind-down", "阴跌不止 · 迷雾消逝",
        "深秋的森林里最后一片枯叶在灰白浓雾中缓慢飘坠，四周是落尽叶子的沉默树干，"
        "天光一点点变暗，缓慢、疲惫、无声消耗的钝感",
        selections_extra={
            "style": "手绘水彩", "mood": "忧郁孤独", "light": "蓝调时刻",
            "tone": "冷调", "comp": "大面积留白", "bg": "自然户外", "texture": "哑光",
        },
    ),
    # ── 财经行情首图（情绪冰点 / 观望）──
    _fin(
        "fin-freezing-point", "情绪冰点 · 绝对零度",
        "一朵盛放的红花被封冻在巨大透明的冰层深处，姿态定格在最鲜艳绽放的瞬间，"
        "四周是望不到边的雪原，没有一丝风，死一般寂静中被冻结的生机",
        selections_extra={
            "style": "3D渲染", "mood": "宁静平和", "light": "月光清辉",
            "tone": "冷调", "comp": "居中构图", "bg": "自然户外", "texture": "玻璃",
        },
    ),
    _fin(
        "fin-wait-and-see", "多空观望 · 如履薄冰",
        "一只脚轻轻踩在结冰的湖面上，冰面纹丝未裂，脚边的水汽在冷空气中凝成薄雾，"
        "湖面之下隐约可见深不见底的暗色，进退两难、屏息试探的静止瞬间",
        selections_extra={
            "style": "写实摄影", "mood": "神秘悬疑", "light": "蓝调时刻",
            "tone": "低饱和莫兰迪", "shot": "近景", "comp": "大面积留白",
            "bg": "自然户外", "texture": "玻璃",
        },
    ),
    # ── 财经行情首图（博弈 / 风险）──
    _fin(
        "fin-greed-fear", "贪婪与恐惧 · 一桌两界",
        "同一场盛大晚宴的长桌两端：一端烛火通明、酒杯高举碰响，"
        "另一端蜡烛燃尽、餐盘空置积灰，桌子正中央最后一支烛火在两股气流的拉扯间剧烈摇晃，"
        "繁华与冷寂只隔一张桌面的荒诞感",
        selections_extra={
            "style": "超现实主义", "mood": "神秘悬疑", "light": "烛光暖光",
            "tone": "高饱和", "comp": "对称构图", "bg": "室内场景", "texture": "织物",
        },
    ),
    _fin(
        "fin-overheat", "市场过热 · 临界之沸",
        "炉火上的一壶水即将沸腾，壶盖被顶得微微跳动，白色蒸汽从缝隙嘶嘶喷出，"
        "壶身映出灼热的红光，临界点前最后一刻的燥热、紧绷与不安",
        selections_extra={
            "style": "3D渲染", "mood": "紧张压迫", "light": "烛光暖光",
            "tone": "暖调", "shot": "特写", "comp": "居中构图",
            "bg": "室内场景", "texture": "金属",
        },
    ),
    # ── 财经行情首图（中性）──
    _fin(
        "fin-neutral-data", "财经复盘 · 月下秩序",
        "退潮后的滩涂上，鹅卵石按大小整齐排列延伸至远方，月光为每一颗石头镶上冷静的银边，"
        "潮水退去后浮现的秩序与克制，适合复盘与深度分析类文章的头图",
        selections_extra={
            "style": "极简主义", "mood": "宁静平和", "light": "月光清辉",
            "tone": "冷调", "comp": "重复图案", "bg": "自然户外", "texture": "哑光",
        },
    ),
]

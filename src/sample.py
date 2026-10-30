"""样刊内容：不联网、不调模型时用来验证排版与面板。

仅在 --mock 模式下使用，生产流程不会走到这里。
"""

ENGLISH_MD = """## 01｜Global shipping costs ease as new container capacity comes online

**Source**｜BBC News　**Words**｜186　**Est.**｜18 min

### ¶1
Ocean freight rates on the main Asia-to-Europe route have fallen for a sixth consecutive week, as newly delivered container ships enter service faster than older tonnage is retired. The benchmark rate is now roughly a third below its peak in early summer, a decline that shipping analysts describe as orderly rather than abrupt.

亚洲至欧洲主干航线的海运运价已连续第六周下跌，原因是新交付的集装箱船投入运营的速度，快于老旧运力退役的速度。基准运价目前比初夏高点低约三分之一，航运分析师称这轮下跌是"有序的"而非"骤降"。

> 生词｜**consecutive** *adj.* 连续的；**tonnage** *n.* （船舶）吨位，运力总量；**benchmark** *n.* 基准；**abrupt** *adj.* 突然的，急剧的

### ¶2
Carriers had ordered record numbers of vessels during the pandemic, when a shortage of capacity pushed spot prices to extraordinary levels. Those orders are now being fulfilled, and the resulting supply is arriving into a market where demand has cooled but not collapsed.

疫情期间，运力短缺把即期运价推到极高水平，航运公司因此订造了创纪录数量的船舶。这些订单如今陆续交付，新增运力进入的是一个需求已经降温、但并未崩塌的市场。

> 生词｜**carrier** *n.* 承运人，航运公司；**vessel** *n.* 船舶；**spot price** *n.* 即期价格；**fulfil** *v.* 履行，兑现（订单）

## 02｜Cities are turning empty offices into housing, slowly

**Source**｜The Guardian　**Words**｜142　**Est.**｜12 min

### ¶1
More than a dozen cities have introduced incentives to convert vacant office buildings into apartments, but the pace of actual construction remains far slower than the political rhetoric suggests. Planning approvals have risen sharply, while completions have barely moved.

十多个城市已推出激励措施，鼓励把空置写字楼改造成公寓，但实际建设进度远慢于官方表态所暗示的速度。规划审批数量大幅上升，竣工量却几乎没有变化。

> 生词｜**incentive** *n.* 激励措施；**vacant** *adj.* 空置的；**rhetoric** *n.* 言辞，说辞；**completion** *n.* （工程的）竣工

### ¶2
The obstacle is rarely political will. Office floors tend to be too deep for residential layouts, plumbing risers are in the wrong place, and the maths often fails once fire regulations and acoustic standards are applied to a building designed for desk work.

障碍很少出在政治意愿上。写字楼的进深对住宅户型来说通常太大，上下水立管的位置不对，而且一旦把消防规范和隔声标准套用到一栋为办公而设计的建筑上，账往往就算不过来了。

> 生词｜**obstacle** *n.* 障碍；**layout** *n.* 布局，户型；**riser** *n.* （管道）立管；**acoustic** *adj.* 声学的，隔音的
"""

FINANCE_MD = """### 降准之后，先看这三个数字

央行宣布下调金融机构存款准备金率 0.25 个百分点，释放长期资金约 5000 亿元。新闻只有一句话，但它沿着「银行—企业—居民」这条链条往下走，会在不同环节留下痕迹。

### 一、钱是怎么被"放"出来的

存款准备金是银行每收一笔存款必须上交给央行的一部分，剩下的才能拿去放贷。降准就是把这个比例调低，同一笔存款里可以用于放贷的部分变多。

> **名词注释**
> - **存款准备金率**：银行吸收存款后必须按比例上缴央行的部分。用法：说「降准 0.25 个百分点」，指的是这个比例下调 0.25%。
> - **流动性**：市场上可动用的资金充裕程度。用法：资金多、拆借容易，叫「流动性宽松」。

### 二、三个先动的指标

第一个是银行间市场的资金价格。第二个是同业存单发行利率。第三个是信贷投放的结构，而不是总量——企业中长期贷款有没有起来，比总量更能说明钱去了哪里。

### 三、对普通人意味着什么

降准不直接改变存款利率，但它会先压低银行的负债成本，再传导到贷款利率。传导有时滞，通常要看下一个季度的信贷数据。

> **名词注释**
> - **同业存单**：银行之间互相借钱的凭证。用法：它的利率是观察银行资金松紧的高频窗口。
> - **企业中长期贷款**：期限一年以上的企业借款，通常对应真实投资。用法：这个数字回升，说明企业在扩产而不是补现金流。
"""

TRAVEL_MD = """### 县域旅游订单增速跑赢一线：谁在承接这股客流

暑期数据里有一个结构性变化：三四线及县域目的地的住宿订单增速明显高于一线城市，客单价却只有一线的一半左右。这不是简单的"消费降级"，而是供给端先发生了变化。

### 上游：资源方在重新定价

县域目的地的核心资源是景区经营权与在地文化内容。过去这些资源由地方平台公司持有，定价粗放；现在越来越多由专业运营方托管，开始按客流分层定价，工作日与周末的价差被拉开。

> **名词注释**
> - **景区经营权**：对景区进行开发、运营并收费的权利，通常由地方政府通过招标或协议授予。用法：谈县域旅游时，先问经营权在谁手上。
> - **在地文化内容**：目的地独有的非遗、民俗、饮食等可被产品化的素材。用法：它是县域目的地做差异化的底层资产。

### 中游：渠道在下沉，但不是简单复制

OTA 的下沉策略不是把一线产品打折卖，而是把"周边两小时车程"做成独立品类。这改变了搜索逻辑：用户不再搜目的地，而是搜时间半径。

### 下游：客群变了

主力客群从"打卡型"转向"遛娃型"和"陪伴型"。这类客群对住宿的确定性要求高，对网红打卡点不敏感，反而愿意为"房间干净、早餐本地化"付费。

> **名词注释**
> - **时间半径**：以出发地为圆心、按可接受车程划定的出行范围。用法：两小时高铁圈、三小时自驾圈都是时间半径的表述。
> - **客单价**：单个订单的平均成交金额。用法：订单量涨、客单价跌，说明客群结构在下移。
"""

CONSUMER_MD = """### 一套骨瓷的利润，是怎么在四个环节里分掉的

家居餐具是个看起来传统、实际上正在被重做的赛道。以一套出厂价 120 元的 20 件骨瓷为例，它在到达消费者手里之前，要经过四次加价。

### 从代工到品牌，差的是哪一步

同样的产线，给海外品牌代工时单件利润 3~5 元；换成自有品牌在内容电商卖，单件利润可以到 20 元以上。差的不是工艺，是"谁承担库存风险、谁拥有定价权"。

> **名词注释**
> - **代工（OEM）**：按品牌方要求生产并贴上对方商标。用法：说"这家工厂做代工"，指它不拥有品牌。
> - **动销**：商品从货架真正卖到消费者手里的速度。用法：压货但不动销，是渠道最怕的状态。

### 渠道变了，品类逻辑也跟着变

内容电商让"成套购买"变成"单件试买"。这直接改变了产品结构：过去卖 20 件套礼盒，现在卖 2 人食、4 人食的小套装，SKU 数量翻倍，起订量下降。

> **名词注释**
> - **SKU**：最小库存管理单位，一个规格就是一个 SKU。用法：SKU 翻倍意味着备货与清仓的复杂度同步上升。
"""

# 自动化操作规程（2026-11 实测校准）

执行任何浏览器操作前先读本规程。工具：browser-skill 的 bsk CLI。

## 0. 环境准备（标准启动流程）

1. bsk 守护进程以**后台任务**方式启动：`bsk daemon start --foreground`（run_in_background）；此后所有客户端命令带 `BSK_AUTO_START=0`。
2. `bsk status --json` 确认 Chrome 已连接。
3. 动作被拒并提示需要 observation 时：`bsk sync --json` 取 `observation_id`，以 `--observation <id>` 重放动作。
4. 页面元素在无障碍树中不可见时，用 CSS 选择器操作（`bsk fill/click --selector`）。
5. 目检页面状态：`bsk screenshot --out <png>` + Read 看图；**截图后核对文件时间戳**，未更新则等待页面稳定后重试。

## 1. 百度采集规程（免登录）

| 操作 | 规程 |
|---|---|
| 下拉词挖掘 | `GET https://www.baidu.com/sugrec?prod=pc&wd=<urlencode词>` → JSON `g[].q`；程序化挖词的标准入口 |
| 相关搜索 | bsk 打开 `https://www.baidu.com/s?wd=<词>`，读取右侧「相关搜索」布局表内链接文本；点「换一换」刷新一批 |
| SERP 竞价计数 | 逐条统计带「广告」标识的链接（vom 中为 `link "广告"`）；当前实测阈值：5 条即红海信号 |
| 真实结果域名 | `curl -A <UA> "https://www.baidu.com/s?wd=<词>&rn=20"`，解析 HTML 中 `mu="..."` 属性（已捆绑 `scripts/serp_domains.py`）；curl 不返回广告，广告数以浏览器 vom 为准 |
| 标题更新 | 修改标题后经百度搜索资源平台提交收录，多 IP 查排名验证 |
| 收录量 | 当前 SERP 页面已无「相关结果约 N 个」文案，收录规模从 5118 获取 |

## 1.5 挖词与清洗脚本

- `scripts/mine_sugrec.py`：sugrec BFS 关联查询。种子词来自阶段 0 的候选清单；单查询返回 10 词，多轮滚雪球放大规模。运行环境需 jieba（`pip install jieba`，脚本不能用 `python -I` 运行）；首跑 jieba 构建缓存较慢属正常。
- `scripts/clean_words.py`：阶段 2 清洗（对象词白名单内置，代表词取最短）。
- `scripts/serp_domains.py`：SERP 竞品域名批量提取。

## 2. 5118 采集规程（登录态）

- 入口：首页导航「关键词挖掘」；全网版落地页 `https://www.5118.com/`（小红书版为 `/ci/xhs`）。旧路径（/seo/lengthywords、/keywords、/newtide）已停用，统一从首页导航进入。
- 搜索流程：点击「关键词挖掘」→ 等 ≥6s → fill 输入框 → 点「搜 索」→ 等待结果标题出现。
- 结果页标题为「<实际命中词> 长尾关键词挖掘」，按后缀匹配并把实际命中词记入 CSV。
- 长尾词总量：vom 中「相关长尾词共找到」前 ~25 行内的 emphasis 数字节点（全网版两个数字：总量+有指数；小红书版一个数字：总量）。
- 数据表为虚拟渲染，行级精确数据经 API 获取（`apis.5118.com`：/keyword/word 长尾词 ¥0.006/次、/weight 权重、/keywordparam 搜索量 ¥0.008/次）；网页版用于抽样目检。
- 结果表复制/导出为会员特权，按服务条款使用，经用户提供的 API Key 完成批量取数。

## 3. 爱站查询规程（基础数据免登录）

- 综合查询：`https://www.aizhan.com/cha/<domain>/` → 百度 PC/移动、360、必应、神马权重，ALEXA，备案，域名年龄，PC/移动词数。
- 深度数据展示「登录后可查看更多」时，请用户登录爱站账号。

## 4. 用户配合场景

到达以下步骤时，说明原因并请用户完成登录后继续：

| 站点 | 用途 |
|---|---|
| 5118.com | 网页版深挖/翻页 |
| ziyuan.baidu.com | 收录提交/站点绑定 |
| tongji.baidu.com | 添加站点获取统计代码 |
| zhihu.com | 引流发文（建议小号） |
| 5118 API Key | 批量 API 调用（付费按次） |

## 5. 数据纪律

- 脚本抓 SERP 间隔 ≥3-5s，失败退避；官方 API 优先于爬虫。
- 所有数据落 UTF-8 CSV，标注来源与抓取时间。

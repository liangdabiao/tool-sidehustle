# 自动化操作手册（2026-11 实测验证）

执行浏览器操作前必读。工具：browser-skill 的 bsk CLI。

## 0. bsk 环境注意事项（本机 Windows 实测）

- bsk 守护进程不能从普通 Bash 沙盒自动拉起（Job Object 限制）。先在**后台任务**里启动：`bsk daemon start --foreground`（run_in_background），然后所有客户端命令带 `BSK_AUTO_START=0`。
- 严格观察模式：`open`/`click` 等动作若报 "needs an explicit current observation"，先 `bsk sync --json` 取 `observation_id`，再 `--observation <id>` 重放动作。
- 页面无障碍树里找不到输入框时：用 CSS 选择器兜底（bsk fill/click 支持 `--selector`）。
- 目检页面状态优先 `bsk screenshot --out <png>`，图片用 Read 看，比猜 DOM 可靠。

## 1. 百度（全部免登录）

| 操作 | 方法 |
|---|---|
| 下拉词（程序化挖词首选） | `GET https://www.baidu.com/sugrec?prod=pc&wd=<urlencode词>` → JSON `g[].q`。已验证可用 |
| 相关搜索 | bsk 打开 `https://www.baidu.com/s?wd=<词>`，抓右侧 LayoutTable「相关搜索」内链接文本；「换一换」可刷新一批 |
| SERP 广告识别 | 广告条目带「广告」标识链接（`link "广告"`）；实测「在线图片压缩」有 5 条广告 → 触发竞价≥5 规则 |
| 百度快照 | **已下线**，原文快照投诉流程作废；标题更新改走搜索资源平台收录提交 |

## 1.5 挖词脚本（免登录，已冒烟验证）

`scripts/mine_sugrec.py`：sugrec BFS 关联查询。实测种子「在线 图片」一轮产出 在线图片压缩/编辑/翻译/去水印/文字提取/尺寸修改… 等词 + 全局词频表。
用法：`python mine_sugrec.py --seeds "在线 工具" --max-queue 500 --out words.csv`（建议 `pip install jieba`，缺失时降级二元词窗）。首跑 jieba 建缓存较慢属正常。

## 2. 5118（网页版未登录可查询；导出/复制/高级特权需付费会员；API 需 Key）

- 入口：`https://www.5118.com` → 「关键词挖掘」，或直接搜「5118 关键词挖掘」。标签页：挖长尾词 / 挖相关词 / 挖移动流量词 / 挖全网下拉词 / 关键词动态趋势 / 关键词综合查询。
- 输入框：`bsk fill --selector "input[placeholder*='搜索']" --value "在线 工具"`；点击按钮文案「搜 索」，再点「挖词」（若出现二次确认）。
- 结果页：标题「<词> 长尾关键词挖掘」，显示「相关长尾词共找到 N 条记录[有指数：M]」；列含 竞价公司数量/长尾词数量/流量指数/移动指数/360指数/PC日检索量/移动日检索量/竞价价格 等。实测「在线 工具」→ 94,905 条。
- 未登录限制：可浏览前若干行；「复制数据下载，尽在高级特权」→ 导出需升级会员。
- API（批量场景）：`POST https://apis.5118.com/keyword/word`（长尾词，单次最大 5000 条，约 ¥0.006/次）、`/weight`（权重）、`/keywordparam`（搜索量，约 ¥0.008/次）。**执行前向用户索要 API Key。**
- 网页定位跳转注意：`/seo/lengthywords`、`/keywords` 等旧 URL 已 404/重定向，从首页导航进入最稳。

## 3. 爱站（基础查询免登录）

- 综合查询：`https://www.aizhan.com/cha/<domain>/` → 百度 PC/移动权重、360、必应、神马、头条权重，ALEXA 排名，备案信息，域名年龄，PC/移动词数。
- 部分深度数据「登录后可查看更多」→ 需要时请用户登录爱站账号。

## 4. 需要用户登录后才能继续的操作

| 站点 | 用途 | 提示用户方式 |
|---|---|---|
| 5118.com | 网页版深挖/翻页 | 「请在浏览器登录 5118（免费注册），完成后告诉我」 |
| ziyuan.baidu.com | 收录提交/站点绑定 | 「请登录百度账号并完成站点验证」 |
| tongji.baidu.com | 装统计代码前的站点添加 | 同上百度账号 |
| zhihu.com | 引流发文 | 「请登录知乎（建议小号），完成后告诉我」 |
| 5118 API | 批量 API 调用 | 「请提供 5118 API Key（付费按次）」 |

## 5. 数据抓取纪律

- 尊重站点频率限制：脚本抓 SERP 间隔 ≥3-5s，失败退避；能走官方 API 就不走爬虫。
- 5118 数据仅用于研究筛选，遵守其服务条款；不要试图绕过付费导出限制。
- 所有抓取数据落 CSV（UTF-8），标注来源与抓取时间。

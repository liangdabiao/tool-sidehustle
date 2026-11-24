#!/usr/bin/env python
"""免登录长尾词挖掘：基于百度下拉接口(sugrec)的关联查询 BFS。

对应 SOP 阶段1「关联查询」算法：
  主词入队 -> 查下拉词 -> 每个长尾词分词 -> 提取新词缀 -> 主词+词缀组合入队 -> 循环至队列空。

用法（在 sidehustle-work/01_mining/ 下）:
  python mine_sugrec.py --seeds "在线 工具" "器 下载" --max-queue 2000 --out words.csv
产物:
  words.csv   word,depth,source          挖到的全部词
  freq.csv    token,count                全局词频(阶段2清洗用: top词=无效词表来源)
仅用标准库；请求间隔默认 1.5s，勿调太小。百度接口偶发限流：失败退避重试 3 次。
"""
import argparse, csv, json, queue, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"}
STOP = set(("的了是在和与及或什么的呢吗吧啊嘛么如何为怎么怎样怎么样哪个哪些哪里多少"
            "几有没不很最更比较特别非常十分就才只都也还又再被把将给对向从到在关于按照根据"
            "通过使用进行可以能够需要应该必须免费版软件工具在线app小程序最新官方正版下载安装"))
TOKEN_RE = re.compile(r"[\u4e00-\u9fa5A-Za-z0-9]+")

try:
    import jieba  # pip install jieba，推荐：分词质量直接影响词缀挖掘质量
    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False


def sugrec(word, retries=3):
    url = "https://www.baidu.com/sugrec?prod=pc&wd=" + urllib.parse.quote(word)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            return [g["q"] for g in (data.get("g") or []) if g.get("q")]
        except Exception as e:
            if i == retries - 1:
                print(f"[warn] {word!r} failed: {e}", file=sys.stderr)
                return []
            time.sleep(2 * (i + 1))
    return []


def split_tokens(word):
    """分词提取词缀：有 jieba 用 jieba；否则 CJK 串切二元词窗 + 字母数字整段。"""
    tokens = []
    for seg in TOKEN_RE.findall(word):
        if re.fullmatch(r"[A-Za-z0-9]+", seg):
            tokens.append(seg.lower())
        elif _HAS_JIEBA:
            tokens.extend(t for t in jieba.cut(seg) if t.strip())
        else:  # 降级：二元词窗
            tokens.extend(seg[i:i + 2] for i in range(len(seg) - 1))
    out = []
    for t in tokens:
        t = t.lower().strip()
        if t and t not in STOP and not all(c in STOP for c in t):
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", required=True, help="起始词，如 '在线 工具'")
    ap.add_argument("--out", default="words.csv")
    ap.add_argument("--freq-out", default="freq.csv")
    ap.add_argument("--max-queue", type=int, default=2000, help="最多入队组合数（成本上限）")
    ap.add_argument("--interval", type=float, default=1.5, help="请求间隔秒")
    args = ap.parse_args()

    main_word = args.seeds[0].split()[0]  # 主词 = 第一个种子词的首段
    word_q = queue.Queue()
    for s in args.seeds:
        word_q.put(s)
    seen_words = set(args.seeds)
    seen_tokens = set()
    freq = {}
    rows = []
    depth_of = {s: 0 for s in args.seeds}

    while not word_q.empty() and len(seen_tokens) <= args.max_queue:
        word_now = word_q.get()
        words = sugrec(word_now)
        time.sleep(args.interval)
        for w in words:
            rows.append((w, depth_of.get(word_now, 0), "sugrec"))
            for t in split_tokens(w):
                freq[t] = freq.get(t, 0) + 1
                if t in seen_tokens:
                    continue
                seen_tokens.add(t)
                # 主词 + 新词缀 组合入队
                combo = f"{main_word} {t}"
                if combo not in seen_words:
                    seen_words.add(combo)
                    depth_of[combo] = depth_of.get(word_now, 0) + 1
                    word_q.put(combo)
        print(f"[{len(seen_tokens)} combos] '{word_now}' -> {len(words)} words", file=sys.stderr)

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["word", "depth", "source"])
        w.writerows(rows)
    with open(args.freq_out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["token", "count"])
        for t, c in sorted(freq.items(), key=lambda x: -x[1]):
            w.writerow([t, c])
    print(f"done: {len(rows)} words -> {args.out}; {len(freq)} tokens -> {args.freq_out}")


if __name__ == "__main__":
    main()

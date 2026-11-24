#!/usr/bin/env python
"""SERP 竞品域名提取（免登录，curl 百度 HTML 的 mu= 属性）。
实测要点：广告不会下发给 curl（广告数用浏览器 bsK vom 抓）；mu= 是各结果真实域名。
用法: python serp_domains.py "音频在线裁剪" "markdown转word" --out domains.csv
"""
import argparse, csv, re, subprocess, time, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
BAIDU = ("baidu.com", "bdstatic.com", "bdimg.com", "bcebos.com", "baidubce.com",
         "mbd.baidu", "baijiahao", "bdspan", "pg-creative")


def fetch_domains(word, delay=3.0):
    url = "https://www.baidu.com/s?wd=" + urllib.parse.quote(word) + "&rn=20"
    html = subprocess.run(["curl", "-s", "-m", "15", "-A", UA, url],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="ignore").stdout
    if len(html) < 10000:
        print(f"[warn] {word}: 页面过短({len(html)}B)，可能被风控", flush=True)
        return []
    ds = []
    for m in re.findall(r'mu="([^"]+)"', html):
        d = re.sub(r"^https?://", "", m).split("/")[0]
        if d and d != "null" and "+" not in d and \
           not any(d == b or d.endswith("." + b) for b in BAIDU) and d not in ds:
            ds.append(d)
    time.sleep(delay)
    return ds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="+")
    ap.add_argument("--out", default="domains.csv")
    ap.add_argument("--delay", type=float, default=3.0)
    args = ap.parse_args()

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["word", "domain_count", "domains"])
        for word in args.words:
            ds = fetch_domains(word, args.delay)
            w.writerow([word, len(ds), "|".join(ds)])
            print(f"{word}: {len(ds)} domains -> {ds[:5]}", flush=True)
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()

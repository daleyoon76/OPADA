import json, re, subprocess, urllib.request, sys, html, pathlib

QUESTION = ("아래 온비드 공매 물건에 입찰하려고 합니다. 어떤 서류를 언제까지 준비해야 하는지 "
            "알려 주세요. 입찰 전에 내야 하는 서류와 낙찰된 뒤에 내는 서류를 구분해서 알려 주세요.")

def token():
    r = subprocess.run(["gcloud","auth","application-default","print-access-token"],
                       capture_output=True, text=True)
    if r.returncode: sys.exit("ADC 토큰 실패")
    return r.stdout.strip()

def vertex(prompt, tok):
    ep = ("https://aiplatform.googleapis.com/v1/projects/reliable-fort-480706-s6"
          "/locations/global/publishers/google/models/gemini-3.1-flash-lite:generateContent")
    body = json.dumps({"contents":[{"role":"user","parts":[{"text":prompt}]}],
                       "generationConfig":{"temperature":0.2,"maxOutputTokens":2048}}).encode()
    req = urllib.request.Request(ep, data=body, method="POST",
        headers={"Content-Type":"application/json","Authorization":"Bearer "+tok})
    with urllib.request.urlopen(req, timeout=240) as r:
        d = json.load(r)
    try:
        return "".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"])
    except Exception:
        return "[파싱 실패] " + json.dumps(d, ensure_ascii=False)[:300]

def page_text(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read().decode("utf-8","replace")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>"," ",raw)
    t = re.sub(r"(?s)<[^>]+>"," ",t)
    return re.sub(r"[ \t ]+"," ",re.sub(r"\n{2,}","\n",html.unescape(t))).strip()

key, url = sys.argv[1], sys.argv[2]
tok = token()
out = {"url": url}
out["B"] = vertex(f"{QUESTION}\n\n물건 링크: {url}", tok)
txt = page_text(url)
out["page_chars"] = len(txt)
out["C"] = vertex(f"{QUESTION}\n\n물건 링크: {url}\n\n아래는 그 페이지에서 읽은 본문입니다.\n\n{txt[:60000]}", tok)
pathlib.Path(f"/tmp/opada-cmp/{key}.json").write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding="utf-8")
print(f"{key}: 본문 {out['page_chars']}자 · B {len(out['B'])}자 · C {len(out['C'])}자")

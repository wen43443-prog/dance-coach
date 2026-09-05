# -*- coding: utf-8 -*-
"""轮询等待 GitHub Pages 发布新版本（内容哈希与本地一致）"""
import hashlib
import time
import urllib.request

LOCAL = 'index.html'
URL = 'https://wen43443-prog.github.io/dance-coach/index.html'

want = hashlib.sha256(open(LOCAL, 'rb').read()).hexdigest()
print('本地期望:', want[:16])
for i in range(30):
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'dance-frame-check', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=20) as r:
            got = hashlib.sha256(r.read()).hexdigest()
        if got == want:
            print(f'第 {i+1} 次轮询：线上已是最新版本 ✓')
            break
        print(f'第 {i+1} 次轮询：线上仍是旧版 {got[:16]}，等待…')
    except Exception as e:
        print(f'第 {i+1} 次轮询失败: {e}')
    time.sleep(15)
else:
    print('超时：线上未更新，请检查 GitHub Actions/构建状态')

# -*- coding: utf-8 -*-
"""比对线上文件与本地文件的 SHA256，确保部署一致"""
import hashlib

def h(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

pairs = [
    ('index.html', r'_verify\index.html'),
    ('sw.js', r'_verify\sw.js'),
    ('manifest.webmanifest', r'_verify\manifest.webmanifest'),
]
bad = 0
for local, remote in pairs:
    a, b = h(local), h(remote)
    ok = a == b
    bad += (not ok)
    print(('OK  ' if ok else 'DIFF ') + local, a, b)
print('ALL MATCH' if bad == 0 else 'MISMATCH FOUND')

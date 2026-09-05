# -*- coding: utf-8 -*-
"""零下载核验部署：本地计算 git blob sha，与 GitHub 仓库树比对"""
import hashlib
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def token():
    with open(os.path.join(HERE, '.deploy-token.json'), encoding='utf-8') as f:
        return json.load(f)['token']


def blob_sha(path):
    data = open(path, 'rb').read()
    return hashlib.sha1(b'blob %d\x00' % len(data) + data).hexdigest()


FILES = [
    'index.html', 'manifest.webmanifest', 'sw.js',
    'icons/icon-192.png', 'icons/icon-512.png',
    'ai/pose/pose.js', 'ai/pose/pose_solution_packed_assets_loader.js',
    'ai/pose/pose_solution_packed_assets.data', 'ai/pose/pose_solution_simd_wasm_bin.js',
    'ai/pose/pose_solution_simd_wasm_bin.wasm', 'ai/pose/pose_solution_wasm_bin.js',
    'ai/pose/pose_solution_wasm_bin.wasm', 'ai/pose/pose_web.binarypb',
    'ai/pose/pose_landmark_full.tflite', 'ai/pose/pose_landmark_lite.tflite',
    'README.md', 'iPhone使用指南.md', '本地服务器.py', '启动手机访问服务器.bat',
    '一键发布更新.py', '校验发布一致性.py', '等待发布完成.py', '对比本地与线上.py',
    '生成应用图标.py',
]

tok = token()
req = urllib.request.Request(
    'https://api.github.com/repos/wen43443-prog/dance-coach/git/trees/HEAD?recursive=1',
    headers={'User-Agent': 'diag', 'Authorization': 'Bearer ' + tok})
with urllib.request.urlopen(req, timeout=60) as r:
    tree = {it['path']: it['sha'] for it in json.load(r)['tree']}

bad = 0
for f in FILES:
    local = blob_sha(f)
    remote = tree.get(f)
    ok = local == remote
    bad += (not ok)
    print(('OK  ' if ok else 'DIFF') + ' ' + f, local[:12], (remote or 'MISSING')[:12])
print('全部一致 ✓' if bad == 0 else f'{bad} 个文件不一致 ✗')

# -*- coding: utf-8 -*-
"""舞帧 · GitHub Pages 一键部署
用法:
  python 一键发布更新.py start    # 生成验证码，用户在 github.com/login/device 输入（首次）
  python 一键发布更新.py finish   # 自动部署：优先用已保存的授权，没有则等网页授权
  python 一键发布更新.py push     # 用已保存的授权重新上传（更新版本用）
"""
import base64
import hashlib
import json
import os
import socket
import sys
import time
import urllib.request
import urllib.parse

# 强制走 IPv4：国内网络对 github.com 的 IPv6 常为黑洞路由，IPv4 反而通
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_getaddrinfo

CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI 官方公开 client_id
SCOPE = "public_repo"
API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))
DEVICE_FILE = os.path.join(HERE, ".deploy-device.json")
TOKEN_FILE = os.path.join(HERE, ".deploy-token.json")
# 网站运行文件（相对 dance-coach 根目录）
SITE_FILES = [
    ("index.html", os.path.join(HERE, "index.html")),
    ("manifest.webmanifest", os.path.join(HERE, "manifest.webmanifest")),
    ("sw.js", os.path.join(HERE, "sw.js")),
    ("icons/icon-192.png", os.path.join(HERE, "icons", "icon-192.png")),
    ("icons/icon-512.png", os.path.join(HERE, "icons", "icon-512.png")),
    ("ai/pose/pose.js", os.path.join(HERE, "ai", "pose", "pose.js")),
    ("ai/pose/pose_solution_packed_assets_loader.js", os.path.join(HERE, "ai", "pose", "pose_solution_packed_assets_loader.js")),
    ("ai/pose/pose_solution_packed_assets.data", os.path.join(HERE, "ai", "pose", "pose_solution_packed_assets.data")),
    ("ai/pose/pose_solution_simd_wasm_bin.js", os.path.join(HERE, "ai", "pose", "pose_solution_simd_wasm_bin.js")),
    ("ai/pose/pose_solution_simd_wasm_bin.wasm", os.path.join(HERE, "ai", "pose", "pose_solution_simd_wasm_bin.wasm")),
    ("ai/pose/pose_solution_wasm_bin.js", os.path.join(HERE, "ai", "pose", "pose_solution_wasm_bin.js")),
    ("ai/pose/pose_solution_wasm_bin.wasm", os.path.join(HERE, "ai", "pose", "pose_solution_wasm_bin.wasm")),
    ("ai/pose/pose_web.binarypb", os.path.join(HERE, "ai", "pose", "pose_web.binarypb")),
    ("ai/pose/pose_landmark_full.tflite", os.path.join(HERE, "ai", "pose", "pose_landmark_full.tflite")),
    ("ai/pose/pose_landmark_lite.tflite", os.path.join(HERE, "ai", "pose", "pose_landmark_lite.tflite")),
]
# 仓库文档与工具（随 push 一并同步；不含密钥/测试素材）
DOC_FILES = [
    ("README.md", os.path.join(HERE, "README.md")),
    ("iPhone使用指南.md", os.path.join(HERE, "iPhone使用指南.md")),
    ("本地服务器.py", os.path.join(HERE, "本地服务器.py")),
    ("启动手机访问服务器.bat", os.path.join(HERE, "启动手机访问服务器.bat")),
    ("一键发布更新.py", os.path.join(HERE, "一键发布更新.py")),
    ("校验发布一致性.py", os.path.join(HERE, "校验发布一致性.py")),
    ("等待发布完成.py", os.path.join(HERE, "等待发布完成.py")),
    ("对比本地与线上.py", os.path.join(HERE, "对比本地与线上.py")),
    ("生成应用图标.py", os.path.join(HERE, "生成应用图标.py")),
]
FILES = SITE_FILES  # 兼容旧引用（index.html 在首位）


def http(method, url, data=None, headers=None, timeout=30, retries=3):
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
    hdrs = {"User-Agent": "dance-frame-deploy", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    last_err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                try:
                    return resp.status, json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    return resp.status, raw
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                return e.code, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return e.code, raw
        except Exception as e:  # 网络抖动重试
            last_err = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"网络请求失败: {url} ({last_err})")


def start():
    st, resp = http("POST", "https://github.com/login/device/code",
                    data=urllib.parse.urlencode({"client_id": CLIENT_ID, "scope": SCOPE}).encode(),
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    if st != 200:
        print("生成验证码失败:", resp)
        sys.exit(1)
    with open(DEVICE_FILE, "w", encoding="utf-8") as f:
        json.dump(resp, f)
    print()
    print("=" * 52)
    print("  第 1 步：手机或电脑打开这个页面")
    print("      " + resp["verification_uri"])
    print()
    print("  第 2 步：输入这个验证码（10 分钟内有效）")
    print()
    print("          >>>  " + resp["user_code"] + "  <<<")
    print()
    print("  输入并点击 Authorize 授权后，回来运行:")
    print("      python 一键发布更新.py finish")
    print("=" * 52)


def api_req(method, path, token, data=None):
    headers = {"Authorization": "Bearer " + token}
    return http(method, API + path, data=data, headers=headers)


def load_saved_token():
    """已保存的授权仍有效则返回，否则 None"""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            tok = json.load(f)["token"]
        st, _ = api_req("GET", "/user", tok)
        if st == 200:
            return tok
    except Exception:
        pass
    return None


def deploy_with_token(token):
    st, me = api_req("GET", "/user", token)
    if st != 200:
        print("获取账号信息失败:", me)
        sys.exit(1)
    owner = me["login"]
    print("✓ 账号:", owner)

    # 建仓库（已存在则直接用）
    repo = "dance-coach"
    st, r = api_req("GET", f"/repos/{owner}/{repo}", token)
    if st == 200:
        print("✓ 仓库已存在，直接使用")
    else:
        st, r = api_req("POST", "/user/repos", token,
                        data={"name": repo, "private": False, "auto_init": True,
                              "description": "舞帧 · 舞蹈慢动作拆解 (dance frame coach PWA)"})
        if st not in (201, 202):
            print("建仓库失败:", r)
            sys.exit(1)
        print("✓ 仓库已创建")

    # 上传文件（网站 + 文档；跳过远端已有且内容一致的，避免重复传大模型）
    st, tree = api_req("GET", f"/repos/{owner}/{repo}/git/trees/HEAD?recursive=1", token)
    remote = {}
    if st == 200 and isinstance(tree, dict):
        remote = {it['path']: it['sha'] for it in tree.get('tree', [])}

    def local_blob_sha(path):
        with open(path, 'rb') as f:
            data = f.read()
        return hashlib.sha1(b'blob %d\x00' % len(data) + data).hexdigest()

    for path, local in SITE_FILES + DOC_FILES:
        want = local_blob_sha(local)
        if remote.get(path) == want:
            print('✓ 未变更，跳过', path)
            continue
        with open(local, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        st, old = api_req("GET", f"/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}", token)
        put = {"message": "deploy " + path, "content": content}
        if st == 200 and isinstance(old, dict) and old.get("sha"):
            put["sha"] = old["sha"]
        st2, r2 = api_req("PUT", f"/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}", token, data=put)
        if st2 not in (200, 201):
            print(f"上传 {path} 失败:", r2)
            sys.exit(1)
        print("✓ 已上传", path)

    # 开通 Pages
    st, r = api_req("POST", f"/repos/{owner}/{repo}/pages", token,
                    data={"source": {"branch": "main", "path": "/"}})
    if st in (201, 202):
        print("✓ Pages 已开通，等待构建…")
    elif st == 409:
        print("✓ Pages 已开通过，等待构建…")
    else:
        print("开通 Pages 返回:", st, r, "（有时需在仓库 Settings→Pages 手动开启）")

    # 轮询验证网址（校验内容哈希，确保新版本真正发布）
    url = f"https://{owner}.github.io/{repo}/"
    print("验证", url)
    want = hashlib.sha256(open(FILES[0][1], "rb").read()).hexdigest()
    for i in range(30):
        time.sleep(10)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dance-frame-deploy",
                                                       "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                got = hashlib.sha256(resp.read()).hexdigest()
            if got == want:
                print()
                print("=" * 52)
                print("  部署成功（内容已验证）！你的 iPhone 用 Safari 打开：")
                print("      " + url)
                print("  然后 分享 → 添加到主屏幕 即可当 App 使用")
                print("=" * 52)
                return
            print(f"  构建中…({(i + 1) * 10}s)")
        except Exception:
            print(f"  构建中…({(i + 1) * 10}s)")
    print("超时未验证成功，请过几分钟手动打开:", url)


def finish():
    tok = load_saved_token()
    if tok:
        print("✓ 使用已保存的授权，无需再输验证码")
        deploy_with_token(tok)
        return

    with open(DEVICE_FILE, "r", encoding="utf-8") as f:
        dev = json.load(f)
    print("等待你在网页上完成授权…（最多等 12 分钟，可随时 Ctrl+C）")
    token = None
    deadline = time.time() + 12 * 60
    interval = dev.get("interval", 5)
    while time.time() < deadline and not token:
        time.sleep(interval)
        st, resp = http("POST", "https://github.com/login/oauth/access_token",
                        data=urllib.parse.urlencode({
                            "client_id": CLIENT_ID,
                            "device_code": dev["device_code"],
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        }).encode(),
                        headers={"Content-Type": "application/x-www-form-urlencoded"})
        if st == 200 and resp.get("access_token"):
            token = resp["access_token"]
        elif resp.get("error") not in ("authorization_pending", "slow_down"):
            print("授权失败:", resp.get("error_description", resp))
            sys.exit(1)
    if not token:
        print("验证码已过期，请重新运行: python 一键发布更新.py start")
        sys.exit(1)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"token": token}, f)
    print("✓ 授权成功")

    deploy_with_token(token)


def push():
    tok = load_saved_token()
    if not tok:
        print("没有已保存的授权，请先运行: python 一键发布更新.py finish")
        sys.exit(1)
    deploy_with_token(tok)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "start":
        start()
    elif cmd == "finish":
        finish()
    elif cmd == "push":
        push()
    else:
        print(__doc__)

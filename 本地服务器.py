# -*- coding: utf-8 -*-
"""本地静态服务器：启动后在手机浏览器输入屏幕上显示的地址即可打开舞帧。"""
import http.server
import mimetypes
import os
import socket
import sys

PORT = 8899
os.chdir(os.path.dirname(os.path.abspath(__file__)))
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("text/javascript", ".js")

ipv4s = set()
try:
    for info in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET):
        ip = info[4][0]
        if not ip.startswith("127."):
            ipv4s.add(ip)
except Exception:
    pass

print()
print("=" * 46)
print("  舞帧 · 舞蹈慢动作拆解  已启动")
print("=" * 46)
print("  本机使用:      http://localhost:%d" % PORT)
for ip in sorted(ipv4s):
    print("  手机请打开:    http://%s:%d" % (ip, PORT))
print()
print("  手机需与电脑连接同一个 Wi-Fi；")
print("  按 Ctrl+C 停止服务。")
print("=" * 46)
print()

try:
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), http.server.SimpleHTTPRequestHandler)
    srv.serve_forever()
except KeyboardInterrupt:
    sys.exit(0)

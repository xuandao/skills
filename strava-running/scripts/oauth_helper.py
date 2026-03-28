#!/usr/bin/env python3
"""
Strava OAuth 授权助手
自动完成授权流程，获取包含 activity:read_all 权限的 refresh_token
"""

import json
import webbrowser
import http.server
import socketserver
import urllib.parse
import requests
from pathlib import Path

# 配置
CONFIG_FILE = Path(__file__).parent.parent / "references" / "strava_config.json"
PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}/callback"

# 需要的权限
SCOPES = "read_all,profile:read_all,activity:read_all"


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    """处理 OAuth 回调"""
    code = None

    def do_GET(self):
        if "/callback" in self.path:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)

            if 'code' in params:
                OAuthHandler.code = params['code'][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>授权成功!</h1>
                    <p>可以关闭此窗口并返回终端查看结果。</p>
                </body>
                </html>
                """)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed. No code received.")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 静音日志


def get_authorization_code(config):
    """打开浏览器获取授权 code"""

    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={config['client_id']}&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"approval_prompt=force&"
        f"scope={SCOPES}"
    )

    print("=" * 60)
    print("Strava OAuth 授权")
    print("=" * 60)
    print(f"\n即将打开浏览器，请完成授权...")
    print(f"\n如果浏览器没有自动打开，请手动访问:")
    print(f"{auth_url}\n")

    # 启动本地服务器等待回调
    with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
        httpd.allow_reuse_address = True

        # 打开浏览器
        webbrowser.open(auth_url)

        print("等待授权回调...")
        while OAuthHandler.code is None:
            httpd.handle_request()

    return OAuthHandler.code


def exchange_code_for_token(config, code):
    """用 code 换取 access_token 和 refresh_token"""

    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
        }
    )

    if response.status_code != 200:
        print(f"错误: {response.text}")
        return None

    return response.json()


def main():
    config = load_config()

    print("当前配置:")
    print(f"  client_id: {config['client_id']}")
    print(f"  client_secret: {config['client_secret'][:10]}...")
    print(f"  refresh_token: {config['refresh_token'][:20]}...")

    # 获取授权 code
    code = get_authorization_code(config)
    print(f"\n获取到 code: {code[:20]}...")

    # 换取 token
    print("\n换取 token...")
    tokens = exchange_code_for_token(config, code)

    if not tokens:
        print("❌ 换取 token 失败")
        return

    print(f"\n✅ 授权成功!")
    print(f"\n新的 token 信息:")
    print(f"  access_token: {tokens['access_token'][:30]}...")
    print(f"  refresh_token: {tokens['refresh_token'][:30]}...")
    print(f"  expires_at: {tokens['expires_at']}")

    # 更新配置
    config["refresh_token"] = tokens["refresh_token"]
    save_config(config)

    print(f"\n✅ 已更新 {CONFIG_FILE}")
    print("\n现在可以正常使用 strava-running skill 了!")


if __name__ == "__main__":
    main()

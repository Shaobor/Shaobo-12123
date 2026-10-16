"""Local help pages for the 12123 integration."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView


CAPTURE_TUTORIAL_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>12123 登录抓包教程</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f4f7fb;
      --card: #fff;
      --text: #172033;
      --muted: #667085;
      --primary: #078fc2;
      --primary-dark: #05739b;
      --border: #dbe3ec;
      --code: #edf5f9;
      --warn-bg: #fff7e6;
      --warn-border: #f59e0b;
      --danger-bg: #fff1f2;
      --danger-border: #ef4444;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #111827;
        --card: #1f2937;
        --text: #f8fafc;
        --muted: #aab5c5;
        --primary: #38bdf8;
        --primary-dark: #7dd3fc;
        --border: #374151;
        --code: #0f2531;
        --warn-bg: #3a2a0b;
        --warn-border: #fbbf24;
        --danger-bg: #3d1820;
        --danger-border: #fb7185;
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px 14px 40px;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      line-height: 1.65;
    }
    .container { max-width: 760px; margin: 0 auto; }
    .hero, .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, .08);
    }
    .hero { padding: 24px; margin-bottom: 16px; }
    h1 { margin: 0 0 4px; font-size: 24px; }
    h2 { margin: 0 0 10px; font-size: 18px; }
    h3 { margin: 0 0 6px; font-size: 16px; }
    p { margin: 6px 0; }
    .sub, .note { color: var(--muted); font-size: 14px; }
    .tag {
      display: inline-block; margin: 0 6px 6px 0; padding: 3px 9px;
      border-radius: 999px; background: rgba(8, 145, 178, .13);
      color: var(--primary-dark); font-size: 12px; font-weight: 700;
    }
    .card { padding: 18px 20px; margin-top: 14px; }
    .step { padding: 13px 0; border-top: 1px solid var(--border); }
    .step:first-of-type { border-top: 0; padding-top: 0; }
    .number {
      display: inline-flex; align-items: center; justify-content: center;
      width: 25px; height: 25px; margin-right: 7px; border-radius: 8px;
      background: var(--primary); color: #fff; font-size: 13px; font-weight: 800;
    }
    code, pre {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    code { padding: 2px 5px; border-radius: 5px; background: var(--code); color: var(--primary-dark); }
    pre {
      overflow-x: auto; padding: 11px 13px; border-radius: 9px;
      background: var(--code); color: var(--text); font-size: 12px; white-space: pre-wrap;
      word-break: break-all;
    }
    .warning, .danger {
      margin: 12px 0; padding: 12px 14px; border-radius: 11px;
      font-size: 14px;
    }
    .warning { background: var(--warn-bg); border-left: 4px solid var(--warn-border); }
    .danger { background: var(--danger-bg); border-left: 4px solid var(--danger-border); }
    .field {
      display: flex; gap: 10px; align-items: flex-start; margin: 9px 0;
    }
    .field b { min-width: 155px; }
    .footer { margin-top: 18px; text-align: center; }
    .btn {
      border: 0; border-radius: 10px; padding: 10px 15px; color: #fff;
      background: var(--primary); cursor: pointer; font-size: 14px; font-weight: 700;
    }
    .btn:hover { background: var(--primary-dark); }
    a { color: var(--primary-dark); }
    @media (max-width: 560px) {
      .field { display: block; }
      .field b { display: block; margin-bottom: 3px; }
      h1 { font-size: 21px; }
    }
  </style>
</head>
<body>
<main class="container">
  <section class="hero">
    <h1>12123 登录抓包教程</h1>
    <p class="sub">用于首次绑定车主账号或重新登录。教程页面由 12123 集成在本机提供，不需要访问第三方教程站。</p>
    <div style="margin-top:12px">
      <span class="tag">iOS</span><span class="tag">Android</span>
      <span class="tag">Stream / StormSniffer / HttpCanary / Reqable</span>
    </div>
  </section>

  <section class="card">
    <div class="danger"><b>隐私提醒</b><br>
      只抓取并填写你自己的 12123 账号。设备 ID、身份证号、mobileSessionId 和 token 都属于敏感凭据，<b>不要截图发群、不要提交 GitHub、不要写进日志或教程</b>。抓包完成后可清理抓包记录。</div>
    <div class="warning"><b>这次要找的请求</b><br>
      在抓包列表搜索 <code>ssoProxy/login</code>，完整地址通常是：<br>
      <code>https://gab.122.gov.cn/eapp/m/ssoProxy/login</code><br>
      这是 12123 的正式登录请求；不要把普通刷新接口、消息接口或 <code>silentLogin</code> 当作首次登录抓包。</div>
  </section>

  <section class="card">
    <h2>操作步骤</h2>
    <div class="step">
      <h3><span class="number">1</span>准备手机抓包</h3>
      <p>在手机上安装抓包工具，启动本地 VPN/抓包服务，并按工具提示安装 CA 证书。iOS 还要在“设置 → 通用 → 关于本机 → 证书信任设置”中开启对该证书的完全信任；如果系统或 App 不允许 HTTPS 解密，不要尝试绕过安全校验。</p>
    </div>
    <div class="step">
      <h3><span class="number">2</span>重新登录 12123</h3>
      <p>先清空旧抓包记录，再打开官方 12123 App，执行一次完整登录。请确保抓包从打开登录页之前就已经开始，避免只抓到后续刷新请求。</p>
    </div>
    <div class="step">
      <h3><span class="number">3</span>定位登录请求</h3>
      <p>在抓包工具中搜索 <code>gab.122.gov.cn</code> 或 <code>ssoProxy/login</code>，打开 <code>POST /eapp/m/ssoProxy/login</code>。优先选择刚刚登录产生、返回 <code>HTTP/1.1 200 OK</code> 的那一条。</p>
      <p class="note">如果只看到 401/403、普通业务接口或 silentLogin，请重新清空记录并完整登录一次。</p>
    </div>
    <div class="step">
      <h3><span class="number">4</span>提取四个字段</h3>
      <div class="field"><b>设备 ID（device_id）</b><span>从登录请求中复制设备标识：<b>iOS 为 40 位十六进制，安卓为 16 位十六进制</b>。按抓包原值完整复制，不能截短，也不要把空格或偏移地址带进去。</span></div>
      <div class="field"><b>身份证号码</b><span>直接填写本人 18 位身份证号码（末位可为 X）。不再填写登录响应密文，也不需要处理 HEX；不同版本的 App 加密格式可能不同，由后端完成后续登录处理。</span></div>
      <div class="field"><b>mobileSessionId</b><span>从该登录请求的响应头复制，字段名大小写按原值填写。</span></div>
      <div class="field"><b>token</b><span>从同一条登录请求的响应头复制完整 <code>token-...</code> 值，不要只复制前缀或截断。</span></div>
    </div>
    <div class="step">
      <h3><span class="number">5</span>回到 Home Assistant</h3>
      <p>在 12123 集成的“绑定车主账号”页面，把四个字段分别粘贴后提交。集成会先调用后端验证，验证成功后自动获取车主档案并创建实体；页面显示的车主姓名会按规则脱敏。</p>
    </div>
  </section>

  <section class="card">
    <h2>常见问题</h2>
    <p><b>提示 E101023 / 认证信息无效：</b>通常是 token、mobileSessionId 不是同一条登录请求，或 token 已过期。重新清空记录并完整登录，把同一条请求的三个抓包字段和身份证号码一起提交。</p>
    <p><b>提示登录校验失败：</b>检查身份证号码是否为本人有效的 18 位号码，iOS 设备 ID 是否误按 16 位截断。</p>
    <p><b>登录后仍没有实体：</b>先确认后端已更新并可访问，再在 HA 中重载 12123 集成；不要把本教程页面里的示例文字当成真实凭据。</p>
  </section>

  <div class="footer"><button class="btn" onclick="window.close();history.back();">返回 Home Assistant</button></div>
</main>
</body>
</html>
"""


class JiaoguanCaptureTutorialView(HomeAssistantView):
    """Serve the local 12123 login-capture tutorial."""

    url = "/api/12123/capture_tutorial"
    name = "api:12123:capture_tutorial"
    requires_auth = False

    async def get(self, request):
        """Return the tutorial page without exposing any account data."""
        return web.Response(text=CAPTURE_TUTORIAL_HTML, content_type="text/html", status=200)

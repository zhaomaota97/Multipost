"""可观察的小红书登录：用户手动登录，实时打印真实 URL / cookie / 页面标志，
成功后保存登录态，并暴露登录后的真实页面结构以便修正检测逻辑。"""
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b  # noqa: E402

LOGIN_URL = "https://creator.xiaohongshu.com/login"

with b.session("xiaohongshu", headless=False) as (ctx, page):
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=40000)
    print("请在窗口里用【手机号+验证码】登录。我每 3 秒报告一次状态……\n")

    saved = False
    for i in range(60):  # 最多看 180 秒
        page.wait_for_timeout(3000)
        url = page.url
        try:
            ncookie = len(ctx.cookies())
        except Exception:
            ncookie = -1
        on_login = "/login" in url
        print(f"[{i*3:3d}s] url={url}  cookies={ncookie}  在登录页={on_login}")

        if not on_login and ncookie > 0:
            page.wait_for_timeout(1500)
            b.save_state(ctx, "xiaohongshu")
            print(f"\n>>> 已检测到登录并保存登录态（{len(ctx.cookies())} 个 cookie）。")
            print(">>> 登录后真实 URL:", page.url)
            # 探测登录后页面的可见入口文本，供修正 is_logged_in
            for kw in ["发布笔记", "发布", "数据中心", "创作灵感", "笔记管理", "首页", "我的"]:
                try:
                    if page.get_by_text(kw).count():
                        print(f"    页面含文本『{kw}』")
                except Exception:
                    pass
            saved = True
            break

    if not saved:
        print("\n>>> 未检测到登录成功（可能没登进去）。最后 URL:", page.url)
    page.wait_for_timeout(2000)

"""探测小红书创作平台登录页：有哪些登录方式/标签页/二维码，是否区分创作者与商家。"""
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

CANDIDATES = [
    "https://creator.xiaohongshu.com/login",
    "https://creator.xiaohongshu.com/",
]

with b.session("xiaohongshu", headless=False) as (ctx, page):
    for url in CANDIDATES:
        print("\n" + "=" * 70)
        print("打开:", url)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            print("  goto 出错:", e)
            continue
        page.wait_for_timeout(5000)
        print("  最终 URL:", page.url)

        # 可见的关键文本
        for kw in ["创作者", "商家", "登录", "扫码", "下载", "千帆", "蒲公英", "专业号", "手机号", "企业"]:
            try:
                c = page.get_by_text(kw).count()
                if c:
                    print(f"  文本『{kw}』x{c}")
            except Exception:
                pass

        # 标签页/按钮
        print("  --- 可见按钮/标签文本 ---")
        try:
            texts = page.evaluate(
                """() => {
                    const out = [];
                    document.querySelectorAll("button, a, [role=tab], .tab, [class*='tab']").forEach(el => {
                        const r = el.getBoundingClientRect();
                        const t = (el.innerText||'').trim();
                        if (r.width>0 && r.height>0 && t && t.length<20) out.push(t);
                    });
                    return [...new Set(out)].slice(0, 30);
                }"""
            )
            for t in texts:
                print("   •", t)
        except Exception as e:
            print("   (出错:", e, ")")

        # 二维码图片
        try:
            qr = page.locator("img[class*='qrcode'], canvas, img[src*='qr']").count()
            print("  二维码类元素:", qr)
        except Exception:
            pass

        page.screenshot(path=str(ROOT / "logs" / f"xhs_login_{CANDIDATES.index(url)}.png"), full_page=True)

    print("\n已截图 logs/xhs_login_*.png；15 秒后关闭，可手动观察登录窗口。")
    page.wait_for_timeout(15000)

"""诊断视频号发表页：定位 iframe 内的文件上传框与上传触发按钮。"""
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import browser as b  # noqa: E402

URL = "https://channels.weixin.qq.com/platform/post/create"

with b.session("weixin_channels", headless=False) as (ctx, page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)

    # 轮询等待任意 frame 出现 input[type=file]
    target = None
    for _ in range(20):
        page.wait_for_timeout(1500)
        for fr in page.frames:
            try:
                if fr.locator('input[type="file"]').count() > 0:
                    target = fr
                    break
            except Exception:
                pass
        if target:
            break

    print("当前 URL:", page.url)
    print("找到含 input[type=file] 的 frame:", target.url if target else "无")

    for i, fr in enumerate(page.frames):
        print(f"\n=== frame {i}: {fr.url} ===")
        try:
            allin = fr.locator("input")
            print("  input 总数:", allin.count())
            for j in range(min(allin.count(), 15)):
                el = allin.nth(j)
                print(f"    input[{j}] type={el.get_attribute('type')} "
                      f"accept={el.get_attribute('accept')} class={el.get_attribute('class')}")
        except Exception as e:
            print("  (读取 input 出错:", e, ")")
        for txt in ["上传", "发表视频", "上传视频", "添加", "拖拽"]:
            try:
                c = fr.get_by_text(txt).count()
                if c:
                    print(f"  文本『{txt}』x{c}")
            except Exception:
                pass

    page.screenshot(path=str(Path(__file__).resolve().parent.parent / "logs" / "debug_channels.png"), full_page=True)
    print("\n已截图 logs/debug_channels.png")

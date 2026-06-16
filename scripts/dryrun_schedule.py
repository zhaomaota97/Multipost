"""定时发表演练：用合法未来整点时间，真实走完定时设置，但不点「发表」。"""
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b  # noqa: E402
from app.publishers import _utils as u  # noqa: E402
from app.publishers.weixin_channels import WeixinChannelsPublisher  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("dryrun")

vids = [p for p in (ROOT / "videos").iterdir() if p.suffix.lower() in {".mp4", ".mov", ".m4v"}]
video = str(vids[0])
# 取“明天同一整点”，确保是合法的未来时间
publish_at = (datetime.now() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
print("视频:", video, "| 目标定时:", publish_at)

pub = WeixinChannelsPublisher()
with b.session("weixin_channels", headless=False) as (ctx, page):
    page.goto(pub.create_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    page.locator('input[type="file"]').first.set_input_files(video)
    log.info("等待上传完成…")
    pub._wait_upload_done(page)
    log.info("上传完成，填写描述…")
    ed = u.first_visible(page, ["div.input-editor"], 10000)
    if ed:
        ed.click(); page.keyboard.type("定时演练-请勿发布")

    log.info(">>> 调用 _set_schedule …")
    pub._set_schedule(page, log, publish_at)

    # 读取“发表时间”框现值，验证是否设成功
    val = page.locator("input[placeholder='请选择发表时间']").first.input_value()
    log.info(f">>> 发表时间框当前值: {val!r}")
    page.screenshot(path=str(ROOT / "logs" / "dryrun_schedule.png"), full_page=True)
    log.info("已截图 logs/dryrun_schedule.png（未发表）。5 秒后关闭。")
    page.wait_for_timeout(5000)

import logging, sys
from datetime import datetime, timedelta
from pathlib import Path
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b
from app.publishers import _utils as u
from app.publishers.douyin import DouyinPublisher
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log=logging.getLogger("dry")
vids=[p for p in (ROOT/"videos").iterdir() if p.suffix.lower() in {".mp4",".mov",".m4v"}]
pub=DouyinPublisher()
publish_at=(datetime.now()+timedelta(hours=3)).replace(second=0,microsecond=0)  # 合法未来时间
with b.session("douyin", headless=False) as (ctx,page):
    page.goto(pub.upload_url, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(3000)
    fi=u.first_visible(page,["div[class^='container'] input","input[type=file]"],10000)
    fi.set_input_files(str(vids[0]))
    u.first_visible(page,["[class^='long-card'] div:has-text('重新上传')","text=重新上传"],120000)
    page.wait_for_timeout(2000)
    ti=u.first_visible(page,["input[placeholder*='作品标题']","input[type='text']"],8000)
    if ti: u.fill_editor(ti,"定时校验-请勿发布")
    log.info(f">>> 目标定时 {publish_at:%Y-%m-%d %H:%M}")
    pub._set_schedule(page, log, publish_at)
    page.screenshot(path=str(ROOT/"logs"/"dryrun_douyin_sched.png"), full_page=True)
    log.info("已截图（未发布）。5 秒后关闭。")
    page.wait_for_timeout(5000)

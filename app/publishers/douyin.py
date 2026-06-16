"""抖音（抖音创作服务平台）发布器。

后台地址：https://creator.douyin.com
选择器参考开源项目 social-auto-upload（MIT）uploader/douyin_uploader 实战验证版本。
"""
from datetime import datetime, timedelta

from playwright.sync_api import Page

from .base import BasePublisher, PublishError
from . import _utils as u


class DouyinPublisher(BasePublisher):
    platform_key = "douyin"
    platform_name = "抖音"
    login_url = "https://creator.douyin.com/"
    home_url = "https://creator.douyin.com/creator-micro/home"
    upload_url = "https://creator.douyin.com/creator-micro/content/upload"

    def is_logged_in(self, page: Page) -> bool:
        # 未登录：出现扫码登录 / 二维码
        if u.any_visible(page, ["text=扫码登录", "text=二维码", "img[class*='qrcode']"], 2500):
            return False
        # 已登录：停在创作者后台（首页/发布等）
        if "creator.douyin.com/creator-micro" in page.url:
            return True
        return u.any_visible(page, ["text=作品管理", "text=内容管理", "text=发布视频"], 4000)

    def do_publish(self, page, logger, *, video_path, title, description, tags, publish_at):
        logger.info(f"[{self.platform_name}] 进入上传页：{self.upload_url}")
        page.goto(self.upload_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 1) 上传视频
        logger.info(f"[{self.platform_name}] 上传视频文件：{video_path}")
        file_input = u.first_visible(
            page, ["div[class^='container'] input", "input[type=file]"], 10000
        )
        if not file_input:
            shot = u.screenshot(page, f"{self.platform_key}_nofileinput")
            raise PublishError(f"未找到上传输入框，截图：{shot}")
        file_input.set_input_files(video_path)

        # 2) 等待跳转到发布页 + 上传完成（出现“重新上传”）
        logger.info(f"[{self.platform_name}] 等待跳转到发布页并完成上传……")
        done = u.first_visible(
            page,
            ["[class^='long-card'] div:has-text('重新上传')", "text=重新上传"],
            self.upload_timeout_ms(),
        )
        # 上传失败检测
        if u.any_visible(page, ["div.progress-div > div:has-text('上传失败')"], 1500):
            shot = u.screenshot(page, f"{self.platform_key}_uploadfail")
            raise PublishError(f"平台提示上传失败，截图：{shot}")
        if not done:
            shot = u.screenshot(page, f"{self.platform_key}_upload")
            raise PublishError(f"视频上传超时或失败，截图：{shot}")
        logger.info(f"[{self.platform_name}] 视频上传完成。")
        page.wait_for_timeout(2000)

        # 3) 标题：作品标题为描述区第一个文本输入框
        title_input = u.first_visible(
            page, ["input[placeholder*='作品标题']", "input[type='text']"], 8000
        )
        if title_input and title:
            logger.info(f"[{self.platform_name}] 填写标题：{title[:30]}")
            u.fill_editor(title_input, title[:30])

        # 4) 正文 + 话题：.zone-container[contenteditable='true']
        editor = u.first_visible(
            page, [".zone-container[contenteditable='true']", "div[contenteditable='true']"], 6000
        )
        if editor:
            editor.click()
            if description:
                logger.info(f"[{self.platform_name}] 填写简介。")
                page.keyboard.type(description)
            for tag in tags or []:
                logger.info(f"[{self.platform_name}] 添加话题 #{tag}")
                page.keyboard.type(f" #{tag}")
                page.wait_for_timeout(1200)
                page.keyboard.press("Space")

        # 5) 定时发布
        if publish_at:
            self._set_schedule(page, logger, publish_at)

        # 6) 发布
        page.wait_for_timeout(1500)
        try:
            publish_btn = page.get_by_role("button", name="发布", exact=True)
            if publish_btn.count() == 0 or not publish_btn.first.is_visible():
                raise PublishError("未找到「发布」按钮")
            logger.info(f"[{self.platform_name}] 点击发布。")
            publish_btn.first.click()
        except PublishError:
            shot = u.screenshot(page, f"{self.platform_key}_nopublishbtn")
            raise PublishError(f"未找到「发布」按钮，截图：{shot}")
        page.wait_for_timeout(4000)

        if "content/manage" in page.url or u.any_visible(page, ["text=发布成功", "text=作品管理"], 6000):
            logger.info(f"[{self.platform_name}] ✅ 发布成功。")
        else:
            shot = u.screenshot(page, f"{self.platform_key}_result")
            logger.info(f"[{self.platform_name}] ⚠️ 未确认到成功提示，请人工核对。截图：{shot}")

    def _set_schedule(self, page: Page, logger, publish_at: datetime):
        # 抖音定时需在约 2 小时~14 天内；不足 2 小时会被平台拒绝，自动顺延。
        min_time = datetime.now() + timedelta(hours=2, minutes=5)
        if publish_at < min_time:
            logger.info(
                f"[{self.platform_name}] ⚠️ 定时时间 {publish_at:%Y-%m-%d %H:%M} 不足 2 小时，"
                f"抖音不接受，已自动顺延为 {min_time:%Y-%m-%d %H:%M}。"
            )
            publish_at = min_time
        target = publish_at.strftime("%Y-%m-%d %H:%M")
        logger.info(f"[{self.platform_name}] 设置定时发布：{target}")
        radio = u.first_visible(
            page, ["[class^='radio']:has-text('定时发布')", "text=定时发布"], 5000
        )
        if not radio:
            logger.info(f"[{self.platform_name}] ⚠️ 未找到定时选项，将按立即发布处理。")
            return
        radio.click()
        page.wait_for_timeout(1200)
        date_input = u.first_visible(
            page,
            [".semi-input[placeholder='日期和时间']", "input[placeholder='日期和时间']", ".semi-datepicker input"],
            5000,
        )
        if not date_input:
            logger.info(f"[{self.platform_name}] ⚠️ 未找到时间输入框，请人工设置定时。")
            return
        # Semi UI 受控输入：必须 click → 全选 → 输入 → 回车（fill 清不掉默认值）
        date_input.click()
        page.keyboard.press("Control+a")
        page.keyboard.type(target)
        page.keyboard.press("Enter")
        page.wait_for_timeout(800)
        # 校验是否真的设进去了
        try:
            val = date_input.input_value()
            if target in (val or ""):
                logger.info(f"[{self.platform_name}] 定时时间已设置为：{val}")
            else:
                logger.info(
                    f"[{self.platform_name}] ⚠️ 定时时间可能未设置成功，框内现值为：{val!r}（目标 {target}），请人工核对。"
                )
        except Exception:  # noqa: BLE001
            pass

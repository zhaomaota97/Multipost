"""视频号（微信视频号助手）发布器。

后台地址：https://channels.weixin.qq.com/platform
选择器参考开源项目 social-auto-upload（MIT）uploader/tencent_uploader 实战验证版本，
平台改版后若失效，日志会记录卡在哪步并自动截图到 logs/。
"""
from datetime import datetime

from playwright.sync_api import Page

from .base import BasePublisher, PublishError
from . import _utils as u


class WeixinChannelsPublisher(BasePublisher):
    platform_key = "weixin_channels"
    platform_name = "视频号"
    login_url = "https://channels.weixin.qq.com/"
    home_url = "https://channels.weixin.qq.com/platform"
    create_url = "https://channels.weixin.qq.com/platform/post/create"

    def is_logged_in(self, page: Page) -> bool:
        # 主判据：URL。未登录会停在/跳回 login 页；登录后进入 /platform 工作台。
        url = page.url or ""
        if "login" in url:
            return False
        if "/platform" in url:
            return True
        # 兜底：看是否出现工作台元素，且无二维码
        if u.any_visible(page, ["div.login-qrcode-wrap", "img.qrcode"], 1500):
            return False
        return u.any_visible(
            page, ["div:has-text('发表视频')", "text=内容管理", "text=动态管理"], 3000
        )

    def do_publish(self, page, logger, *, video_path, title, description, tags, publish_at):
        logger.info(f"[{self.platform_name}] 进入发表页：{self.create_url}")
        page.goto(self.create_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 1) 上传视频：跨所有 iframe 查找上传框，找不到则刷新重试一次
        logger.info(f"[{self.platform_name}] 定位视频上传框……")
        file_input = self._find_file_input(page, 45000)
        if file_input is None:
            logger.info(f"[{self.platform_name}] 首次未找到上传框，刷新页面重试……")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            file_input = self._find_file_input(page, 45000)
        if file_input is None:
            shot = u.screenshot(page, f"{self.platform_key}_nofileinput")
            raise PublishError(f"未找到视频上传框（页面可能未正常加载），截图：{shot}")
        logger.info(f"[{self.platform_name}] 上传视频文件：{video_path}")
        file_input.set_input_files(video_path)

        # 2) 等待上传完成：发表按钮去掉 disabled 类即视为就绪
        logger.info(f"[{self.platform_name}] 等待视频上传与解析完成（可能较久）……")
        if not self._wait_upload_done(page):
            shot = u.screenshot(page, f"{self.platform_key}_upload")
            raise PublishError(f"视频上传超时或失败，截图：{shot}")
        logger.info(f"[{self.platform_name}] 视频上传完成。")

        # 3) 描述编辑器：标题 + 正文 + 话题，都打进 div.input-editor
        editor = u.first_visible(page, ["div.input-editor", "div[contenteditable='true']"], 10000)
        if editor:
            editor.click()
            if title:
                logger.info(f"[{self.platform_name}] 填写标题/描述。")
                page.keyboard.type(title)
            if description:
                page.keyboard.press("Enter")
                page.keyboard.type(description)
            for tag in tags or []:
                logger.info(f"[{self.platform_name}] 添加话题 #{tag}")
                page.keyboard.type(f" #{tag}")
                page.wait_for_timeout(1200)
                page.keyboard.press("Enter")

        # 4) 短标题（可选）
        try:
            short = page.get_by_text("短标题", exact=True).locator("..").locator(
                "xpath=following-sibling::div"
            ).locator('span input[type="text"]')
            if title and short.count() > 0 and short.first.is_visible():
                logger.info(f"[{self.platform_name}] 填写短标题。")
                short.first.fill(title[:16])
        except Exception:  # noqa: BLE001
            pass

        # 5) 定时发表
        if publish_at:
            self._set_schedule(page, logger, publish_at)

        # 6) 发表
        page.wait_for_timeout(1500)
        publish_btn = u.first_visible(
            page, ["div.form-btns button:has-text('发表')", "button:has-text('发表')"], 8000
        )
        if not publish_btn:
            shot = u.screenshot(page, f"{self.platform_key}_nopublishbtn")
            raise PublishError(f"未找到「发表」按钮，截图：{shot}")
        logger.info(f"[{self.platform_name}] 点击发表。")
        publish_btn.click()
        page.wait_for_timeout(4000)

        if "post/list" in page.url or u.any_visible(page, ["text=发表成功", "text=内容管理"], 6000):
            logger.info(f"[{self.platform_name}] ✅ 发表成功。")
        else:
            shot = u.screenshot(page, f"{self.platform_key}_result")
            logger.info(f"[{self.platform_name}] ⚠️ 未确认到成功提示，请人工核对。截图：{shot}")

    def _find_file_input(self, page: Page, timeout_ms: int):
        """在主文档及所有 iframe 里轮询查找视频上传 input[type=file]。"""
        waited, step = 0, 1500
        while waited < timeout_ms:
            for fr in page.frames:
                try:
                    loc = fr.locator('input[type="file"]')
                    if loc.count() > 0:
                        return loc.first
                except Exception:  # noqa: BLE001
                    continue
            page.wait_for_timeout(step)
            waited += step
        return None

    def _wait_upload_done(self, page: Page) -> bool:
        deadline = self.upload_timeout_ms()
        waited, step = 0, 2000
        while waited < deadline:
            try:
                btn = page.get_by_role("button", name="发表")
                if btn.count() > 0:
                    cls = btn.first.get_attribute("class") or ""
                    if "weui-desktop-btn_disabled" not in cls:
                        return True
            except Exception:  # noqa: BLE001
                pass
            page.wait_for_timeout(step)
            waited += step
        return False

    def _set_schedule(self, page: Page, logger, publish_at: datetime):
        """设置定时发表。视频号的时间控件：
        - 「发表时间」是只读输入框，点击弹出日历，需在日历里点选日期单元格；
        - 时间为**整点粒度**（只能选小时，分钟恒为 00）。
        """
        logger.info(
            f"[{self.platform_name}] 设置定时发表：{publish_at:%Y-%m-%d} {publish_at.hour:02d}:00"
            f"（视频号定时为整点，分钟将被忽略）"
        )

        # 1) 勾选「定时」（不定时/定时 中的第二个）
        labels = page.locator("label").filter(has_text="定时")
        if labels.count() == 0:
            logger.info(f"[{self.platform_name}] ⚠️ 未找到定时选项，将按立即发表处理。")
            return
        (labels.nth(1) if labels.count() > 1 else labels.first).click()
        page.wait_for_timeout(1000)

        # 2) 点开日期选择器
        try:
            page.click("input[placeholder='请选择发表时间']")
        except Exception:  # noqa: BLE001
            logger.info(f"[{self.platform_name}] ⚠️ 未找到发表时间输入框，请人工设置定时。")
            return
        page.wait_for_timeout(1000)

        # 3) 按月份导航到目标月
        target_month = publish_at.strftime("%m月")
        month_sel = "span.weui-desktop-picker__panel__label:has-text('月')"
        for _ in range(13):
            try:
                cur = page.inner_text(month_sel)
            except Exception:  # noqa: BLE001
                cur = ""
            if target_month in cur:
                break
            try:
                page.click("button.weui-desktop-btn__icon__right")
            except Exception:  # noqa: BLE001
                break
            page.wait_for_timeout(500)

        # 4) 选日期单元格（跳过禁用/灰色的）
        clicked = False
        for el in page.query_selector_all("table.weui-desktop-picker__table a"):
            try:
                if "weui-desktop-picker__disabled" in (el.get_attribute("class") or ""):
                    continue
                if (el.inner_text() or "").strip() == str(publish_at.day):
                    el.click()
                    clicked = True
                    break
            except Exception:  # noqa: BLE001
                continue
        if not clicked:
            shot = u.screenshot(page, f"{self.platform_key}_schedule")
            logger.info(
                f"[{self.platform_name}] ⚠️ 日历中没有可选的 {publish_at:%m-%d} "
                f"（多半是时间太近/超出允许范围），未设定时。截图：{shot}"
            )
            return

        # 5) 设置整点时间
        try:
            page.click("input[placeholder='请选择时间']")
            page.keyboard.press("Control+a")
            page.keyboard.type(publish_at.strftime("%H"))
            page.wait_for_timeout(500)
            # 点别处收起选择器
            editor = page.locator("div.input-editor").first
            if editor.count() > 0:
                editor.click()
        except Exception as e:  # noqa: BLE001
            logger.info(f"[{self.platform_name}] ⚠️ 设置小时失败：{e}")
            return
        logger.info(f"[{self.platform_name}] 定时已设置：{publish_at:%Y-%m-%d} {publish_at.hour:02d}:00")

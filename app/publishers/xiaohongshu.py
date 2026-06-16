"""小红书（小红书创作服务平台）发布器。

后台地址：https://creator.xiaohongshu.com
选择器参考开源项目 social-auto-upload（MIT）uploader/xiaohongshu_uploader 实战验证版本。
"""
from datetime import datetime, timedelta

from playwright.sync_api import Page

from .base import BasePublisher, PublishError
from . import _utils as u


class XiaohongshuPublisher(BasePublisher):
    platform_key = "xiaohongshu"
    platform_name = "小红书"
    login_url = "https://creator.xiaohongshu.com/login"
    home_url = "https://creator.xiaohongshu.com/new/home"
    # 直接带 target=video 进入视频发布
    publish_url = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video"

    def is_logged_in(self, page: Page) -> bool:
        if "creator.xiaohongshu.com/login" in page.url:
            return False
        if u.any_visible(page, ["div[class*='login-box']", "text=扫码登录"], 2500):
            return False
        return u.any_visible(page, ["text=发布笔记", "text=数据中心", "text=发布"], 4000)

    def do_publish(self, page, logger, *, video_path, title, description, tags, publish_at):
        logger.info(f"[{self.platform_name}] 进入视频发布页：{self.publish_url}")
        page.goto(self.publish_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 1) 上传视频（input.upload-input 为隐藏元素，按存在性跨 frame 查找）
        logger.info(f"[{self.platform_name}] 定位视频上传框……")
        file_input = u.find_file_input(page, 30000, "input.upload-input") or \
            u.find_file_input(page, 15000, 'input[type="file"]')
        if file_input is None:
            shot = u.screenshot(page, f"{self.platform_key}_nofileinput")
            raise PublishError(f"未找到上传输入框，截图：{shot}")
        logger.info(f"[{self.platform_name}] 上传视频文件：{video_path}")
        file_input.set_input_files(video_path)

        # 2) 等待上传完成：预览区出现 上传成功/分辨率/100%
        logger.info(f"[{self.platform_name}] 等待视频上传完成（可能较久）……")
        done = u.first_visible(
            page,
            ["text=上传成功", "text=分辨率", ".preview-new:has-text('100%')", "text=重新上传"],
            self.upload_timeout_ms(),
        )
        if not done:
            shot = u.screenshot(page, f"{self.platform_key}_upload")
            raise PublishError(f"视频上传超时或失败，截图：{shot}")
        logger.info(f"[{self.platform_name}] 视频上传完成。")
        page.wait_for_timeout(2000)

        # 3) 标题
        title_input = u.first_visible(
            page, ["input[placeholder*='填写标题']", "input[placeholder*='标题']"], 8000
        )
        if title_input and title:
            logger.info(f"[{self.platform_name}] 填写标题：{title[:20]}")
            u.fill_editor(title_input, title[:20])

        # 4) 正文 + 话题
        editor = u.first_visible(
            page, ["p[data-placeholder*='输入正文描述']", "div[contenteditable='true']", ".ql-editor"], 6000
        )
        if editor:
            editor.click()
            if description:
                logger.info(f"[{self.platform_name}] 填写正文。")
                page.keyboard.type(description)
            for tag in tags or []:
                logger.info(f"[{self.platform_name}] 添加话题 #{tag}")
                page.keyboard.type(f"#{tag}")
                page.wait_for_timeout(1500)
                # 优先点话题下拉建议项，否则回车
                item = u.first_visible(page, ["#creator-editor-topic-container .item"], 1500)
                if item:
                    item.click()
                else:
                    page.keyboard.press("Enter")

        # 5) 定时发布
        scheduled = False
        if publish_at:
            scheduled = self._set_schedule(page, logger, publish_at)

        # 6) 发布。提交按钮是闭合的 web component <xhs-publish-btn>，内部含「暂存离开」+
        #    红色「发布/定时发布」按钮（同一颗，标签随是否定时切换），无法按文本/DOM 定位，
        #    只能按位置点击右侧红色按钮（约 62% 宽、底部一行）。
        page.wait_for_timeout(1500)
        btn_label = "定时发布" if scheduled else "发布"
        host = page.locator("xhs-publish-btn").first
        if host.count() == 0:
            shot = u.screenshot(page, f"{self.platform_key}_nopublishbtn")
            raise PublishError(f"未找到发布按钮组件 <xhs-publish-btn>，截图：{shot}")
        host.scroll_into_view_if_needed()
        box = host.bounding_box()
        if not box:
            shot = u.screenshot(page, f"{self.platform_key}_nopublishbtn")
            raise PublishError(f"发布按钮不可见，截图：{shot}")
        logger.info(f"[{self.platform_name}] 点击{btn_label}（右侧红色按钮）。")
        host.click(position={"x": box["width"] * 0.62, "y": box["height"] - 28})
        page.wait_for_timeout(4000)

        # 平台拦截提示（如定时时间不合法）
        if u.any_visible(page, ["text=1h-14天", "text=仅支持指定", "text=定时发布仅支持"], 2000):
            shot = u.screenshot(page, f"{self.platform_key}_rejected")
            raise PublishError(f"定时时间被小红书拒绝（需 1 小时~14 天内），请调整时间。截图：{shot}")

        if "publish/success" in page.url or u.any_visible(
            page, ["text=发布成功", "text=笔记发布成功", "text=定时发布成功", "text=发布作品成功"], 8000
        ):
            logger.info(f"[{self.platform_name}] ✅ 发布成功。")
        else:
            shot = u.screenshot(page, f"{self.platform_key}_result")
            logger.info(f"[{self.platform_name}] ⚠️ 未确认到成功提示，请人工核对。截图：{shot}")

    def _set_schedule(self, page: Page, logger, publish_at: datetime) -> bool:
        # 小红书要求定时时间在 1 小时~14 天内；不足 1 小时则自动顺延，避免被平台拦下。
        min_time = datetime.now() + timedelta(minutes=65)
        if publish_at < min_time:
            logger.info(
                f"[{self.platform_name}] ⚠️ 定时时间 {publish_at:%Y-%m-%d %H:%M} 不足 1 小时，"
                f"小红书不接受，已自动顺延为 {min_time:%Y-%m-%d %H:%M}。"
            )
            publish_at = min_time
        logger.info(f"[{self.platform_name}] 设置定时发布：{publish_at:%Y-%m-%d %H:%M}")
        try:
            switch = page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch")
            if switch.count() == 0:
                logger.info(f"[{self.platform_name}] ⚠️ 未找到定时开关，将按立即发布处理。")
                return False
            switch.first.click()
            page.wait_for_timeout(1000)
        except Exception:  # noqa: BLE001
            logger.info(f"[{self.platform_name}] ⚠️ 定时开关点击失败，将按立即发布处理。")
            return False

        date_input = u.first_visible(
            page, [".d-datepicker-input-filter input.d-text", ".el-input__inner"], 5000
        )
        if date_input:
            date_input.click()
            date_input.fill(publish_at.strftime("%Y-%m-%d %H:%M"))
            page.wait_for_timeout(600)
            # 关闭日期弹层：点标题输入框（无副作用），避免弹层挡住后续操作
            try:
                title = page.locator("input[placeholder*='填写标题'], input[placeholder*='标题']").first
                if title.count() > 0:
                    title.click()
                else:
                    page.keyboard.press("Escape")
            except Exception:  # noqa: BLE001
                page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            logger.info(
                f"[{self.platform_name}] 定时已设置（小红书要求至少 1 小时后，平台可能自动微调）。"
            )
            return True
        logger.info(f"[{self.platform_name}] ⚠️ 未找到时间输入框，请人工设置定时。")
        return False

    def _find_submit_button(self, page: Page, text: str):
        """小红书底部提交按钮是 div（非 button），按精确文本取位置最靠下的可见元素。"""
        cands = page.get_by_text(text, exact=True)
        best, best_y = None, -1.0
        n = cands.count()
        for i in range(min(n, 20)):
            el = cands.nth(i)
            try:
                box = el.bounding_box()
                if box and box["y"] > best_y:
                    best, best_y = el, box["y"]
            except Exception:  # noqa: BLE001
                continue
        return best

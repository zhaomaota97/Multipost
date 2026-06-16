"""发布器基类与通用异常。

每个平台子类负责三件事：
  1. is_logged_in(page)  —— 判断当前是否已登录
  2. login(page, ctx, logger) —— 引导扫码登录并保存登录态
  3. do_publish(...)      —— 上传视频、填写信息、（可选）定时、发布

所有耗时步骤都通过 logger 记录，便于网页端实时查看。
"""
from datetime import datetime

from playwright.sync_api import Page, BrowserContext

from .. import browser as browser_mod
from .. import config


class LoginExpired(Exception):
    """登录态失效/未登录，需要人工重新扫码。"""


class PublishError(Exception):
    """发布过程中出现的可报告错误。"""


class BasePublisher:
    platform_key: str = ""
    platform_name: str = ""
    login_url: str = ""
    home_url: str = ""

    # ---- 子类需实现 ----
    def is_logged_in(self, page: Page) -> bool:
        raise NotImplementedError

    def do_publish(
        self,
        page: Page,
        logger,
        *,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        publish_at: datetime | None,
    ) -> None:
        raise NotImplementedError

    # ---- 通用流程 ----
    def login(self, page: Page, ctx: BrowserContext, logger) -> None:
        """打开登录页，等待用户扫码登录成功，保存登录态。

        判定登录成功需同时满足：is_logged_in 为真 **且** 已拿到该域名的 cookie，
        避免扫码未完成就误判、存下没有 cookie 的无效登录态。
        """
        timeout = config.SETTINGS["browser"]["login_timeout_sec"]
        logger.info(f"[{self.platform_name}] 打开登录页：{self.login_url}")
        page.goto(self.login_url, wait_until="domcontentloaded")
        logger.info(
            f"[{self.platform_name}] 请在弹出的浏览器窗口中扫码登录"
            f"（{timeout} 秒内完成）……"
        )
        deadline = timeout * 1000
        step = 2000
        waited = 0
        while waited < deadline:
            page.wait_for_timeout(step)
            waited += step
            try:
                if self.is_logged_in(page) and len(ctx.cookies()) > 0:
                    page.wait_for_timeout(1500)  # 让后续 cookie 落地
                    browser_mod.save_state(ctx, self.platform_key)
                    n = len(ctx.cookies())
                    logger.info(
                        f"[{self.platform_name}] 登录成功，已保存登录态（{n} 个 cookie）。"
                    )
                    return
            except Exception:  # noqa: BLE001 -- 检测过程中页面跳转可能抛错
                continue
        raise LoginExpired(f"[{self.platform_name}] 登录超时或未检测到 cookie，请重试。")

    def check_login(self, page: Page, logger) -> bool:
        logger.info(f"[{self.platform_name}] 检查登录态……")
        page.goto(self.home_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        ok = self.is_logged_in(page)
        logger.info(f"[{self.platform_name}] 登录态：{'有效' if ok else '已失效'}")
        return ok

    def publish(
        self,
        page: Page,
        logger,
        *,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        publish_at: datetime | None,
    ) -> None:
        """对外统一入口：先确认登录，再执行发布。"""
        page.goto(self.home_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        if not self.is_logged_in(page):
            raise LoginExpired(
                f"[{self.platform_name}] 登录态已失效，请到「账号管理」重新扫码登录。"
            )
        logger.info(f"[{self.platform_name}] 登录态有效，开始发布流程。")
        self.do_publish(
            page,
            logger,
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            publish_at=publish_at,
        )

    # ---- 小工具 ----
    @staticmethod
    def upload_timeout_ms() -> int:
        return config.SETTINGS["browser"]["upload_timeout_sec"] * 1000

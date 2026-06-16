"""发布器通用的页面操作小工具：多选择器兜底、安全填写、错误截图。"""
from pathlib import Path

from playwright.sync_api import Page, Locator

from .. import config


def first_visible(page: Page, selectors: list[str], timeout_ms: int = 8000) -> Locator | None:
    """在多个候选选择器里返回第一个可见的元素（平台改版时多一层兜底）。"""
    deadline = timeout_ms
    step = 500
    waited = 0
    while waited <= deadline:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    return loc
            except Exception:  # noqa: BLE001
                continue
        page.wait_for_timeout(step)
        waited += step
    return None


def any_visible(page: Page, selectors: list[str], timeout_ms: int = 4000) -> bool:
    return first_visible(page, selectors, timeout_ms) is not None


def find_file_input(page: Page, timeout_ms: int = 30000,
                    selector: str = 'input[type="file"]') -> Locator | None:
    """跨主文档及所有 iframe 按“存在性”查找文件上传框（不要求可见，
    因为多数站点的 input[type=file] 是隐藏元素，set_input_files 也无需其可见）。"""
    waited, step = 0, 1500
    while waited < timeout_ms:
        for fr in page.frames:
            try:
                loc = fr.locator(selector)
                if loc.count() > 0:
                    return loc.first
            except Exception:  # noqa: BLE001
                continue
        page.wait_for_timeout(step)
        waited += step
    return None


def fill_editor(loc: Locator, text: str) -> None:
    """填写 input 或 contenteditable。"""
    loc.click()
    try:
        loc.fill("")
    except Exception:  # noqa: BLE001 -- contenteditable 不支持 fill
        pass
    loc.type(text, delay=20)


def screenshot(page: Page, name: str) -> str:
    path = config.logs_dir() / f"shot_{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:  # noqa: BLE001
        return ""

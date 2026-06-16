"""日志：全局日志 + 每个发布任务一个独立日志文件。

每一步操作都通过 task logger 记录，网页端通过读取日志文件实时展示。
"""
import logging
import sys
from pathlib import Path

from . import config

_FMT = "%(asctime)s [%(levelname)s] %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _setup_root() -> logging.Logger:
    logger = logging.getLogger("fabu")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    # 控制台
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(_FMT, _DATEFMT))
    logger.addHandler(sh)

    # 全局文件日志
    fh = logging.FileHandler(config.logs_dir() / "app.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter(_FMT, _DATEFMT))
    logger.addHandler(fh)
    return logger


root = _setup_root()


def task_log_path(task_id: str) -> Path:
    return config.logs_dir() / f"task_{task_id}.log"


def get_task_logger(task_id: str) -> logging.Logger:
    """为某个发布任务创建专属 logger，写入独立文件，同时冒泡到全局。"""
    name = f"fabu.task.{task_id}"
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = True  # 同时进全局 app.log / 控制台

    fh = logging.FileHandler(task_log_path(task_id), encoding="utf-8")
    fh.setFormatter(logging.Formatter(_FMT, _DATEFMT))
    logger.addHandler(fh)
    return logger


def read_task_log(task_id: str) -> str:
    p = task_log_path(task_id)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""

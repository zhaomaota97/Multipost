"""FastAPI 本地服务：账号管理、上传、发布、任务与日志查询。"""
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, accounts, tasks, logger as log_mod
from .publishers import platform_list

app = FastAPI(title="视频一键发布")

STATIC_DIR = config.static_dir()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


# ---------- 平台 / 账号 ----------
@app.get("/api/platforms")
def api_platforms():
    return platform_list()


@app.get("/api/accounts")
def api_accounts():
    return accounts.accounts_overview()


@app.post("/api/login/{platform}")
def api_login(platform: str):
    return accounts.start_login(platform)


@app.get("/api/login/{platform}/status")
def api_login_status(platform: str):
    return accounts.get_login_state(platform)


@app.post("/api/check/{platform}")
def api_check(platform: str):
    return accounts.check_login(platform)


# ---------- 视频文件 ----------
@app.get("/api/videos")
def api_videos():
    vd = config.videos_dir()
    exts = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".m4v"}
    files = [
        {"name": f.name, "path": str(f.resolve()), "size": f.stat().st_size}
        for f in sorted(vd.iterdir())
        if f.is_file() and f.suffix.lower() in exts
    ]
    return files


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    vd = config.videos_dir()
    dest = vd / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"name": dest.name, "path": str(dest.resolve())}


# ---------- 发布任务 ----------
@app.post("/api/publish")
def api_publish(payload: dict = Body(...)):
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    tags = payload.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip().lstrip("#") for t in tags.replace("，", ",").split(",") if t.strip()]
    video_path = (payload.get("video_path") or "").strip()
    platforms = payload.get("platforms") or []
    publish_at = payload.get("publish_at") or None  # ISO 字符串

    if not video_path:
        raise HTTPException(400, "请提供视频文件")
    if not Path(video_path).exists():
        raise HTTPException(400, f"视频文件不存在：{video_path}")
    if not platforms:
        raise HTTPException(400, "请至少勾选一个平台")
    if not title:
        raise HTTPException(400, "请填写标题")

    task = tasks.create_task(
        title=title,
        description=description,
        tags=tags,
        video_path=video_path,
        platforms=platforms,
        publish_at=publish_at,
    )
    return task


@app.get("/api/tasks")
def api_tasks():
    return tasks.list_tasks()


@app.get("/api/tasks/{tid}")
def api_task(tid: str):
    t = tasks.get_task(tid)
    if not t:
        raise HTTPException(404, "任务不存在")
    return t


@app.get("/api/tasks/{tid}/log")
def api_task_log(tid: str):
    return JSONResponse({"id": tid, "log": log_mod.read_task_log(tid)})


def run():
    import uvicorn

    s = config.SETTINGS["server"]
    print(f"\n  视频一键发布已启动 →  http://{s['host']}:{s['port']}\n")
    uvicorn.run(app, host=s["host"], port=s["port"], log_level="info")


if __name__ == "__main__":
    run()

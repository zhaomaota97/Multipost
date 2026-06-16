# 视频一键发布

预先配置好账号，每次发视频只需：**勾选平台 → 填标题 → 选视频 →（可选）设定时 → 一键发布**。
支持平台：**视频号、抖音、小红书**。

通过浏览器自动化驱动各平台创作者后台完成上传发布，登录态保存在本地，过期会提示重新扫码。
每个任务都有完整日志，可在网页上实时查看；遇到异常会标红等你处理。

---

## 一、安装（Windows，首次）

1. 安装 [Python 3.10+](https://www.python.org/downloads/)，安装时**勾选 Add Python to PATH**。
2. 双击 **`安装.bat`**，等待依赖和浏览器内核安装完成。

## 二、启动

双击 **`启动.bat`**，浏览器会自动打开 `http://127.0.0.1:8800`。
（关闭命令行黑窗口即停止服务。）

## 三、首次配置账号

打开网页 → **账号管理** → 对每个平台点「登录」→ 弹出的浏览器窗口里**扫码登录**。
登录成功后状态变为「已登录」，登录态保存在 `data/cookies/`，下次无需重复扫码。

> 提示：可随时点「检查登录态」确认 cookie 是否还有效。

## 四、发布视频

进入 **发布** 页：

| 字段 | 说明 |
|------|------|
| 标题 | 必填 |
| 简介/正文 | 选填 |
| 话题标签 | 逗号分隔，无需打 `#`，会自动加 |
| 视频文件 | 三选一：从 `videos/` 目录下拉选 / 粘贴绝对路径 / 点「上传」 |
| 发布到 | 勾选目标平台 |
| 定时发布 | 留空＝立即发布；填时间＝用各平台自带定时发表 |

点 **🚀 一键发布**，自动跳到「任务记录」，可实时看每个平台的进度和日志。

## 五、状态说明

- ✅ 成功 / ❌ 失败 / ⚠️ 需登录（登录过期，去账号管理重新扫码）/ 进行中
- 单个平台失败**不影响**其它平台。
- 失败时会在 `logs/` 目录自动截图（`shot_*.png`），方便排查。

---

## 目录结构

```
fabu/
├─ 安装.bat / 启动.bat        # Windows 一键安装 / 启动
├─ run.py                     # 启动入口
├─ requirements.txt
├─ config/settings.json       # 端口、浏览器、超时等配置
├─ app/
│  ├─ main.py                 # FastAPI 服务与接口
│  ├─ accounts.py             # 扫码登录 / 登录态检查
│  ├─ tasks.py                # 发布任务调度（后台线程，逐平台执行）
│  ├─ browser.py              # Playwright 浏览器与登录态管理
│  ├─ logger.py               # 全局 + 每任务独立日志
│  ├─ publishers/             # 各平台发布器
│  │  ├─ base.py              #   通用流程与异常
│  │  ├─ weixin_channels.py   #   视频号
│  │  ├─ douyin.py            #   抖音
│  │  └─ xiaohongshu.py       #   小红书
│  └─ static/                 # 网页前端
├─ data/cookies/              # 各平台登录态（本地，勿外传）
├─ logs/                      # 运行日志与错误截图
└─ videos/                    # 放视频文件的默认目录
```

## 配置项（`config/settings.json`）

- `server.port`：网页端口，默认 8800
- `browser.headless`：发布时是否隐藏浏览器窗口。**建议保持 `false`**，方便观察和应对验证码。
- `browser.channel`：默认用系统 Chrome；没装会自动回退到 Playwright 自带 Chromium。
- `browser.upload_timeout_sec`：视频上传等待上限（默认 1800 秒）。

## 重要说明

- 这三个平台**没有公开发布 API**，本工具靠模拟人工在创作者后台操作。平台页面改版时，
  对应的元素定位（selector）可能失效——日志会记录卡在哪一步并自动截图，按提示在
  `app/publishers/<平台>.py` 中调整选择器即可。
- 请遵守各平台的用户协议，合理使用，避免高频批量操作导致风控。
- 登录态（cookies）等同于账号登录凭据，请勿外传 `data/cookies/` 内容。

## 致谢

三个平台的页面元素定位（selector）参考了开源项目
[social-auto-upload](https://github.com/dreammis/social-auto-upload)（MIT License）中
`uploader/tencent_uploader`、`uploader/douyin_uploader`、`uploader/xiaohongshu_uploader`
的实战验证版本。本项目在其基础上重写为更轻量的本地网页应用，特此致谢。

> 如需更多平台（B站、快手、百家号、TikTok、YouTube）、多账号矩阵管理、Docker 部署，
> 可直接参考或迁移到 social-auto-upload。

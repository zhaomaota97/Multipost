// ---------- 通用 ----------
const $ = (id) => document.getElementById(id);
async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    const t = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(t.detail || r.statusText);
  }
  return r.json();
}
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}

const STATUS_TEXT = {
  pending: ["待处理", "b-wait"],
  running: ["进行中", "b-run"],
  success: ["✅ 成功", "b-ok"],
  failed: ["❌ 失败", "b-no"],
  login_expired: ["⚠️ 需登录", "b-no"],
};

// ---------- Tab 切换 ----------
document.querySelectorAll("nav button").forEach((b) => {
  b.onclick = () => {
    document.querySelectorAll("nav button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    ["publish", "accounts", "records"].forEach((t) =>
      $("tab-" + t).classList.toggle("hide", t !== b.dataset.tab)
    );
    if (b.dataset.tab === "accounts") loadAccounts();
    if (b.dataset.tab === "records") loadTasks();
  };
});

// ---------- 平台复选 ----------
let PLATFORMS = [];
async function loadPlatforms() {
  PLATFORMS = await api("/api/platforms");
  $("f-platforms").innerHTML = PLATFORMS.map(
    (p) => `<label class="pf"><input type="checkbox" value="${p.key}" checked> ${p.name}</label>`
  ).join("");
}

// ---------- 视频文件 ----------
function fmtSize(n) {
  if (!n && n !== 0) return "";
  if (n > 1 << 30) return (n / (1 << 30)).toFixed(2) + " GB";
  if (n > 1 << 20) return (n / (1 << 20)).toFixed(1) + " MB";
  return (n / 1024).toFixed(0) + " KB";
}
function setSelected(path, name) {
  $("f-video-path").value = path;
  const sel = $("selected-file");
  if (path) {
    sel.textContent = "✅ 已选视频：" + (name || path);
    sel.classList.remove("hide");
  } else {
    sel.classList.add("hide");
  }
  // 高亮列表里对应行
  document.querySelectorAll("#video-list .vrow").forEach((r) =>
    r.classList.toggle("active", r.dataset.path === path)
  );
}
async function refreshVideos() {
  const vids = await api("/api/videos");
  const cur = $("f-video-path").value;
  $("video-list").innerHTML =
    vids.length === 0
      ? '<div class="hint" style="padding:10px 14px">videos/ 目录为空，上传或拖入视频后会出现在这里</div>'
      : vids
          .map(
            (v) =>
              `<div class="vrow ${v.path === cur ? "active" : ""}" data-path="${v.path}"
                    onclick="setSelected('${v.path.replace(/\\/g, "\\\\")}','${v.name}')">
                 <span>${v.name}</span><span class="sz">${fmtSize(v.size)}</span></div>`
          )
          .join("");
}
async function doUpload(file) {
  if (!file) return;
  $("upload-hint").textContent = `上传中：${file.name} …`;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const r = await api("/api/upload", { method: "POST", body: fd });
    setSelected(r.path, r.name);
    $("upload-hint").textContent = `已上传：${r.name}`;
    refreshVideos();
  } catch (err) {
    $("upload-hint").textContent = "上传失败：" + err.message;
  }
}
// 点击 / 拖拽上传
$("drop-zone").onclick = () => $("f-upload").click();
$("f-upload").onchange = (e) => doUpload(e.target.files[0]);
["dragover", "dragenter"].forEach((ev) =>
  $("drop-zone").addEventListener(ev, (e) => {
    e.preventDefault();
    $("drop-zone").classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((ev) =>
  $("drop-zone").addEventListener(ev, (e) => {
    e.preventDefault();
    $("drop-zone").classList.remove("dragover");
  })
);
$("drop-zone").addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) doUpload(e.dataTransfer.files[0]);
});
// 手动改路径时同步选中显示
$("f-video-path").addEventListener("input", (e) =>
  setSelected(e.target.value, e.target.value.split(/[\\/]/).pop())
);

// ---------- 发布 ----------
async function doPublish() {
  const platforms = [...document.querySelectorAll("#f-platforms input:checked")].map((c) => c.value);
  const schedule = $("f-schedule").value; // datetime-local -> "2026-06-16T20:00"
  const payload = {
    title: $("f-title").value,
    description: $("f-desc").value,
    tags: $("f-tags").value,
    video_path: $("f-video-path").value,
    platforms,
    publish_at: schedule ? schedule : null,
  };
  const btn = $("btn-publish");
  btn.disabled = true;
  try {
    const task = await api("/api/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    toast("已提交，任务 " + task.id);
    document.querySelector('nav button[data-tab="records"]').click();
  } catch (err) {
    toast("提交失败：" + err.message);
  } finally {
    btn.disabled = false;
  }
}

// ---------- 账号管理 ----------
let acctTimer = null;
async function loadAccounts() {
  const list = await api("/api/accounts");
  $("acct-list").innerHTML = list
    .map((a) => {
      let badge = a.has_cookie
        ? '<span class="badge b-ok">已登录</span>'
        : '<span class="badge b-no">未登录</span>';
      if (a.login_status === "waiting")
        badge = '<span class="badge b-wait">等待扫码…</span>';
      return `<div class="acct">
        <div><b>${a.name}</b> ${badge}
          <div class="task-meta">${a.login_message || ""}</div></div>
        <div>
          <button class="btn ghost" onclick="checkAcct('${a.key}')">检查登录态</button>
          <button class="btn" onclick="loginAcct('${a.key}')">登录 / 重新登录</button>
        </div></div>`;
    })
    .join("");
}
async function loginAcct(key) {
  await api("/api/login/" + key, { method: "POST" });
  toast("已打开浏览器，请在新窗口扫码");
  if (acctTimer) clearInterval(acctTimer);
  acctTimer = setInterval(async () => {
    const s = await api("/api/login/" + key + "/status");
    if (s.status === "success" || s.status === "failed") {
      clearInterval(acctTimer);
      toast(s.message || s.status);
      loadAccounts();
    }
  }, 2000);
  loadAccounts();
}
async function checkAcct(key) {
  toast("检查中…");
  const r = await api("/api/check/" + key, { method: "POST" });
  toast(r.message);
  loadAccounts();
}

// ---------- 任务记录 ----------
let taskTimer = null;
let openTask = null;
async function loadTasks() {
  const tasks = await api("/api/tasks");
  $("task-list").innerHTML =
    tasks.length === 0
      ? '<div class="hint">暂无任务</div>'
      : tasks.map(renderTask).join("");
  if (openTask) loadTaskLog(openTask);
}
function renderTask(t) {
  const pfs = Object.entries(t.platforms)
    .map(([k, v]) => {
      const name = (PLATFORMS.find((p) => p.key === k) || {}).name || k;
      const [txt, cls] = STATUS_TEXT[v.status] || [v.status, ""];
      return `<span class="pf-status"><span class="badge ${cls}">${name} ${txt}</span></span>`;
    })
    .join("");
  return `<div class="task">
    <div class="task-head" onclick="toggleTask('${t.id}')">
      <div><span class="task-title">${t.title}</span>
        <div class="task-meta">${t.id} · ${t.created_at} · ${t.publish_at ? "定时 " + t.publish_at : "立即发布"}</div>
      </div>
      <div>${t.done ? "" : '<span class="badge b-run">运行中</span>'}</div>
    </div>
    <div style="margin-top:8px">${pfs}</div>
    <div id="log-${t.id}" class="${openTask === t.id ? "" : "hide"}" style="margin-top:10px"></div>
  </div>`;
}
function toggleTask(id) {
  const el = $("log-" + id);
  if (openTask === id) {
    openTask = null;
    el.classList.add("hide");
    return;
  }
  document.querySelectorAll('[id^="log-"]').forEach((e) => e.classList.add("hide"));
  openTask = id;
  el.classList.remove("hide");
  loadTaskLog(id);
}
async function loadTaskLog(id) {
  const el = $("log-" + id);
  if (!el) return;
  el.classList.remove("hide"); // 自动刷新后保持展开，不再“自己关闭”
  // 记录刷新前的滚动位置：仅当用户本就在底部时才自动跟随到底部
  const oldPre = el.querySelector("pre");
  const stick =
    !oldPre || oldPre.scrollTop + oldPre.clientHeight >= oldPre.scrollHeight - 30;
  const oldTop = oldPre ? oldPre.scrollTop : 0;
  const r = await api("/api/tasks/" + id + "/log");
  el.innerHTML = `<pre class="log">${(r.log || "（暂无日志）").replace(/</g, "&lt;")}</pre>`;
  const pre = el.querySelector("pre");
  pre.scrollTop = stick ? pre.scrollHeight : oldTop;
}

// 任务页每 3 秒自动刷新
setInterval(() => {
  if (!$("tab-records").classList.contains("hide")) loadTasks();
}, 3000);

// ---------- 初始化 ----------
(async function init() {
  await loadPlatforms();
  await refreshVideos();
})();

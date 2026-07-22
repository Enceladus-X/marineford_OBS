(function () {
  "use strict";

  var currentScript = document.currentScript;
  var defaultBaseUrl = currentScript ? new URL("./", currentScript.src).href : new URL("./", window.location.href).href;
  var defaultDownloadUrl = "https://github.com/Enceladus-X/marineford_OBS/releases/latest/download/Marineford_OBS.exe";
  var defaultReleaseUrl = "https://github.com/Enceladus-X/marineford_OBS/releases/latest";
  var screens = [
    ["control", "컨트롤 패널"],
    ["tablet", "태블릿 패널"],
    ["overlay", "OBS 오버레이"],
    ["editor", "편집 로그"],
  ];
  var demos = [
    ["duel", "듀얼중"],
    ["side", "사이드 교체중"],
    ["judge", "저지 호출"],
    ["standby", "다음 라운드 대기"],
  ];
  var screenNotes = {
    control: "송출 연결, 룰, 플레이어와 덱 프리셋을 준비하는 운영 화면",
    tablet: "방송 테이블에서 듀얼 시작, 승패 보고와 저지 호출을 조작하는 화면",
    overlay: "1920 × 1080 OBS 브라우저 소스에 표시되는 방송 화면",
    editor: "듀얼 구간, 이벤트 로그와 편집 자료를 확인하는 화면",
  };

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;",
      }[char];
    });
  }

  function ensureStyles() {
    if (document.getElementById("mfobs-preview-style")) return;
    var style = document.createElement("style");
    style.id = "mfobs-preview-style";
    style.textContent = [
      ".mfobs-preview{--mf-bg:#07080c;--mf-panel:#11131b;--mf-line:rgba(255,255,255,.11);--mf-text:#f5f6fb;--mf-muted:#a7adba;--mf-gold:#efd36d;--mf-blue:#6472e5;color:var(--mf-text);font-family:Inter,'Noto Sans KR',system-ui,sans-serif}",
      ".mfobs-preview *{box-sizing:border-box}",
      ".mfobs-preview a,.mfobs-preview button{font:inherit}",
      ".mfobs-preview__head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:end;margin-bottom:16px}",
      ".mfobs-preview__eyebrow{color:var(--mf-gold);font-size:12px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}",
      ".mfobs-preview__title{margin:6px 0 0;font-size:clamp(28px,4vw,46px);line-height:1.02;letter-spacing:0}",
      ".mfobs-preview__lead{margin:10px 0 0;max-width:720px;color:var(--mf-muted);font-size:15px;line-height:1.65;font-weight:650}",
      ".mfobs-preview__actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}",
      ".mfobs-preview__button{min-height:40px;border-radius:7px;padding:0 13px;display:inline-grid;place-items:center;color:var(--mf-text);font-size:13px;font-weight:850;text-decoration:none;white-space:nowrap}",
      ".mfobs-preview__download{background:var(--mf-blue);box-shadow:0 10px 26px rgba(100,114,229,.25)}",
      ".mfobs-preview__release{border:1px solid var(--mf-line);background:rgba(255,255,255,.045)}",
      ".mfobs-preview__shell{border:1px solid var(--mf-line);border-radius:8px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.025));box-shadow:0 22px 70px rgba(0,0,0,.36)}",
      ".mfobs-preview__toolbar{display:grid;gap:0;border-bottom:1px solid var(--mf-line);background:rgba(255,255,255,.035)}",
      ".mfobs-preview__screen-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,auto);gap:12px;align-items:center;padding:12px}",
      ".mfobs-preview__state-row{display:flex;align-items:center;gap:10px;border-top:1px solid var(--mf-line);padding:9px 12px;background:rgba(0,0,0,.16)}",
      ".mfobs-preview__state-row[hidden]{display:none}",
      ".mfobs-preview__tabs{display:flex;gap:7px;flex-wrap:wrap}",
      ".mfobs-preview__tab{min-height:34px;border:1px solid var(--mf-line);border-radius:7px;padding:0 12px;background:rgba(255,255,255,.05);color:var(--mf-muted);font-size:13px;font-weight:850;cursor:pointer;white-space:nowrap}",
      ".mfobs-preview__tab[aria-selected='true']{background:var(--mf-gold);border-color:var(--mf-gold);color:#0b0c10}",
      ".mfobs-preview__screen-tab{min-height:39px;padding:0 15px}",
      ".mfobs-preview__state-label{flex:0 0 auto;color:var(--mf-gold);font-size:11px;font-weight:900;letter-spacing:.08em}",
      ".mfobs-preview__note{color:var(--mf-muted);font-size:12px;font-weight:760;text-align:right}",
      ".mfobs-preview__frame-wrap{aspect-ratio:16/9;background:#050506}",
      ".mfobs-preview__frame{width:100%;height:100%;border:0;display:block}",
      ".mfobs-preview__meta{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between;margin-top:8px;color:var(--mf-muted);font-size:12px;font-weight:700}",
      ".mfobs-preview__steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:12px}",
      ".mfobs-preview__step{border:1px solid var(--mf-line);border-radius:7px;padding:10px;background:rgba(255,255,255,.035);color:var(--mf-muted);font-size:12px;line-height:1.45;font-weight:750}",
      "@media(max-width:820px){.mfobs-preview__head,.mfobs-preview__screen-row{grid-template-columns:1fr}.mfobs-preview__actions{justify-content:flex-start}.mfobs-preview__note{text-align:left}.mfobs-preview__steps{grid-template-columns:1fr 1fr}}",
      "@media(max-width:520px){.mfobs-preview__steps{grid-template-columns:1fr}}",
    ].join("");
    document.head.appendChild(style);
  }

  function resolveTarget(target) {
    if (typeof target === "string") return document.querySelector(target);
    if (target && target.nodeType === 1) return target;
    if (currentScript && currentScript.dataset.target) {
      return document.querySelector(currentScript.dataset.target);
    }
    var existing = document.getElementById("marineford-preview");
    if (existing) return existing;
    var fallback = document.createElement("div");
    fallback.id = "marineford-preview";
    if (currentScript && currentScript.parentNode) currentScript.parentNode.insertBefore(fallback, currentScript);
    else document.body.appendChild(fallback);
    return fallback;
  }

  function scriptOptions() {
    var dataset = currentScript ? currentScript.dataset : {};
    return {
      baseUrl: dataset.baseUrl || defaultBaseUrl,
      defaultScreen: dataset.defaultScreen || "control",
      defaultDemo: dataset.defaultDemo || "duel",
      downloadUrl: dataset.downloadUrl || defaultDownloadUrl,
      releaseUrl: dataset.releaseUrl || defaultReleaseUrl,
      title: dataset.title || "TCG 매장 송출 화면 미리보기",
      description: dataset.description || "실제 송출컴에서는 로컬 프로그램이 OBS와 태블릿을 연결합니다. 이 미리보기는 Git에 올라간 최신 정적 데모를 자동으로 표시합니다.",
      showSteps: dataset.showSteps !== "false",
    };
  }

  function versionUrl(baseUrl) {
    var url = new URL("version.json", baseUrl);
    url.searchParams.set("t", String(Date.now()));
    return url.href;
  }

  function previewUrl(baseUrl, screen, demo, version) {
    var isOverlay = screen === "overlay";
    var path = isOverlay ? (version.overlayPath || "overlay.html") : (version.panelPath || "panel.html");
    var url = new URL(path, baseUrl);
    if (isOverlay) url.searchParams.set("demo", demo);
    else url.searchParams.set("screen", screen);
    url.searchParams.set("v", version.cacheKey || version.commit || String(Date.now()));
    return url.href;
  }

  async function loadVersion(baseUrl) {
    try {
      var response = await fetch(versionUrl(baseUrl), { cache: "no-store" });
      if (!response.ok) throw new Error("version fetch failed");
      return await response.json();
    } catch (error) {
      return {
        commit: "live",
        cacheKey: String(Date.now()),
        updatedAt: "",
        source: "fallback",
      };
    }
  }

  function render(target, options, version) {
    var activeScreen = screens.some(function (item) { return item[0] === options.defaultScreen; }) ? options.defaultScreen : "control";
    var activeDemo = demos.some(function (item) { return item[0] === options.defaultDemo; }) ? options.defaultDemo : "duel";
    var steps = options.showSteps ? [
      "<div class=\"mfobs-preview__steps\">",
      "<div class=\"mfobs-preview__step\">1. 송출컴에서 실행 파일을 켭니다.</div>",
      "<div class=\"mfobs-preview__step\">2. 컨트롤 패널에서 OBS URL과 태블릿 QR을 확인합니다.</div>",
      "<div class=\"mfobs-preview__step\">3. OBS에 overlay URL을 브라우저 소스로 추가합니다.</div>",
      "<div class=\"mfobs-preview__step\">4. 태블릿에서 진행 상태와 승패를 조작합니다.</div>",
      "</div>",
    ].join("") : "";
    var versionLabel = version.commit && version.commit !== "live" ? "preview " + version.commit : "preview live";
    var screenTabHtml = screens.map(function (item) {
      var selected = item[0] === activeScreen;
      return "<button class=\"mfobs-preview__tab mfobs-preview__screen-tab\" type=\"button\" data-mfobs-screen=\"" + item[0] + "\" aria-selected=\"" + selected + "\">" + item[1] + "</button>";
    }).join("");
    var demoTabHtml = demos.map(function (item) {
      var selected = item[0] === activeDemo;
      return "<button class=\"mfobs-preview__tab\" type=\"button\" data-mfobs-demo=\"" + item[0] + "\" aria-selected=\"" + selected + "\">" + item[1] + "</button>";
    }).join("");

    target.innerHTML = [
      "<section class=\"mfobs-preview\" aria-label=\"Marineford OBS 송출 화면 미리보기\">",
      "<div class=\"mfobs-preview__head\">",
      "<div>",
      "<div class=\"mfobs-preview__eyebrow\">Marineford OBS</div>",
      "<h2 class=\"mfobs-preview__title\">" + escapeHtml(options.title) + "</h2>",
      "<p class=\"mfobs-preview__lead\">" + escapeHtml(options.description) + "</p>",
      "</div>",
      "<div class=\"mfobs-preview__actions\">",
      "<a class=\"mfobs-preview__button mfobs-preview__download\" href=\"" + escapeHtml(options.downloadUrl) + "\">Windows 실행 파일 다운로드</a>",
      "<a class=\"mfobs-preview__button mfobs-preview__release\" href=\"" + escapeHtml(options.releaseUrl) + "\">릴리스 노트</a>",
      "</div>",
      "</div>",
      "<div class=\"mfobs-preview__shell\">",
      "<div class=\"mfobs-preview__toolbar\">",
      "<div class=\"mfobs-preview__screen-row\">",
      "<div class=\"mfobs-preview__tabs\" role=\"tablist\" aria-label=\"미리보기 화면 선택\">" + screenTabHtml + "</div>",
      "<div class=\"mfobs-preview__note\" data-mfobs-note>" + escapeHtml(screenNotes[activeScreen]) + "</div>",
      "</div>",
      "<div class=\"mfobs-preview__state-row\" data-mfobs-overlay-controls" + (activeScreen === "overlay" ? "" : " hidden") + ">",
      "<span class=\"mfobs-preview__state-label\">오버레이 상태</span>",
      "<div class=\"mfobs-preview__tabs\" role=\"tablist\" aria-label=\"OBS 오버레이 상태 선택\">" + demoTabHtml + "</div>",
      "</div>",
      "</div>",
      "<div class=\"mfobs-preview__frame-wrap\">",
      "<iframe class=\"mfobs-preview__frame\" data-mfobs-frame title=\"Marineford OBS 패널 화면 미리보기\" loading=\"lazy\" src=\"" + escapeHtml(previewUrl(options.baseUrl, activeScreen, activeDemo, version)) + "\"></iframe>",
      "</div>",
      "</div>",
      "<div class=\"mfobs-preview__meta\">",
      "<span>GitHub Pages 최신 미리보기</span>",
      "<span data-mfobs-version>" + escapeHtml(versionLabel) + "</span>",
      "</div>",
      steps,
      "</section>",
    ].join("");

    var frame = target.querySelector("[data-mfobs-frame]");
    var overlayControls = target.querySelector("[data-mfobs-overlay-controls]");
    var note = target.querySelector("[data-mfobs-note]");

    target.querySelectorAll("[data-mfobs-screen]").forEach(function (button) {
      button.addEventListener("click", function () {
        activeScreen = button.getAttribute("data-mfobs-screen");
        target.querySelectorAll("[data-mfobs-screen]").forEach(function (tab) {
          tab.setAttribute("aria-selected", String(tab === button));
        });
        overlayControls.hidden = activeScreen !== "overlay";
        note.textContent = screenNotes[activeScreen] || "Marineford OBS 정적 패널 미리보기";
        frame.src = previewUrl(options.baseUrl, activeScreen, activeDemo, version);
      });
    });

    target.querySelectorAll("[data-mfobs-demo]").forEach(function (button) {
      button.addEventListener("click", function () {
        var demo = button.getAttribute("data-mfobs-demo");
        activeDemo = demo;
        target.querySelectorAll("[data-mfobs-demo]").forEach(function (tab) {
          tab.setAttribute("aria-selected", String(tab === button));
        });
        if (activeScreen === "overlay") frame.src = previewUrl(options.baseUrl, activeScreen, activeDemo, version);
      });
    });
  }

  async function mount(target, options) {
    ensureStyles();
    var resolvedTarget = resolveTarget(target);
    if (!resolvedTarget) throw new Error("Marineford OBS preview target was not found.");
    var resolvedOptions = Object.assign(scriptOptions(), options || {});
    if (!/\/$/.test(resolvedOptions.baseUrl)) resolvedOptions.baseUrl += "/";
    var version = await loadVersion(resolvedOptions.baseUrl);
    render(resolvedTarget, resolvedOptions, version);
    return { target: resolvedTarget, options: resolvedOptions, version: version };
  }

  window.MarinefordOBSPreview = {
    version: 2,
    mount: mount,
  };

  if (!currentScript || currentScript.dataset.autoMount !== "false") {
    mount().catch(function (error) {
      console.error("[Marineford OBS Preview]", error);
    });
  }
}());

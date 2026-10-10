"use strict";

const app = document.getElementById("app");
const WEEKDAYS = "일월화수목금토";
const GRADE_TEXT = { S: "초대형", A: "대형", B: "중형", C: "소형" };
let DATA = null;
let VENUES = {};

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function parseDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}
function today() {
  const n = new Date();
  return new Date(n.getFullYear(), n.getMonth(), n.getDate());
}
function fmtDate(iso) {
  const d = parseDate(iso);
  return `${d.getMonth() + 1}/${d.getDate()}(${WEEKDAYS[d.getDay()]})`;
}
function period(e) {
  return e.start === e.end ? fmtDate(e.start) : `${fmtDate(e.start)} ~ ${fmtDate(e.end)}`;
}
function dday(e) {
  const days = Math.round((parseDate(e.start) - today()) / 86400000);
  if (days > 0) return `D-${days}`;
  if (days === 0) return "오늘";
  return "진행 중";
}
function crowd(n) {
  return n >= 10000 ? `${(n / 10000).toFixed(1)}만` : n.toLocaleString("ko-KR");
}
function gradeVar(g) {
  return `--g: var(--${g})`;
}
function upcoming(e) {
  return e.status !== "done" && parseDate(e.end) >= today();
}

function card(e) {
  const v = VENUES[e.venue_id] || { name: e.venue_id, distance_km: "?" };
  const cancelled = e.status === "cancelled";
  return `
    <a class="card ${cancelled ? "cancelled" : ""}" style="${gradeVar(e.grade)}" href="#event=${encodeURIComponent(e.id)}">
      <div class="row">
        <span class="badge">${e.grade}</span>
        <span class="dday">${cancelled ? "취소됨" : dday(e)}</span>
        <span class="meta">${period(e)}</span>
      </div>
      <div class="title">${esc(e.title)}</div>
      <div class="meta">${esc(v.name)} · 선학역 ${v.distance_km}km</div>
      <div class="meta">하루 <span class="crowd">${crowd(e.crowd_estimate.per_day)}명</span> 예상</div>
    </a>`;
}

function renderHome() {
  const list = DATA.events.filter(upcoming).sort((a, b) => a.start.localeCompare(b.start));
  const live = list.filter((e) => e.status !== "cancelled");
  const big = live.filter((e) => e.grade !== "C");
  const small = live.filter((e) => e.grade === "C");
  const cancelled = list.filter((e) => e.status === "cancelled");
  const updated = new Date(DATA.updated_at);
  app.innerHTML = `
    <p class="muted small">마지막 조사: ${updated.toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "numeric", minute: "2-digit" })}</p>
    ${big.length ? `<h2>발주 준비가 필요한 행사</h2>${big.map(card).join("")}`
                 : `<p class="pad">다가오는 큰 행사가 없어요. 새 행사가 잡히면 알림으로 알려드릴게요.</p>`}
    ${small.length ? `<h2>소규모 행사 (알림 없음)</h2>${small.map(card).join("")}` : ""}
    ${cancelled.length ? `<h2>취소된 행사</h2>${cancelled.map(card).join("")}` : ""}
    <div class="legend">
      ${["S", "A", "B", "C"].map((g) => `<span style="${gradeVar(g)}">${g} ${GRADE_TEXT[g]}</span>`).join("")}
    </div>`;
}

function renderEvent(id) {
  const e = DATA.events.find((x) => x.id === id);
  if (!e) {
    app.innerHTML = `<a class="back" href="#">← 목록</a><p class="pad">행사를 찾을 수 없어요.</p>`;
    return;
  }
  const v = VENUES[e.venue_id] || { name: e.venue_id, distance_km: "?" };
  const map = `https://map.naver.com/p/search/${encodeURIComponent(v.name)}`;
  const p = e.popularity;
  const tags = [p.sold_out ? "매진" : "", p.extra_shows ? "추가 회차" : ""].filter(Boolean).join(" · ");
  app.innerHTML = `
    <a class="back" href="#">← 목록</a>
    <div class="hero">
      <div class="row">
        <span class="badge big-badge" style="${gradeVar(e.grade)}">${e.grade} ${GRADE_TEXT[e.grade]}</span>
        <span class="dday">${e.status === "cancelled" ? "취소됨" : dday(e)}</span>
      </div>
      <div class="title">${esc(e.title)}</div>
      <div class="meta">${period(e)}${e.show_times && e.show_times.length ? " · " + e.show_times.join(", ") + " 시작" : ""}</div>
    </div>

    <div class="box">
      <b>📍 ${esc(v.name)}</b> <span class="muted">선학역 ${v.distance_km}km</span>
      <a class="btn ghost" href="${map}" target="_blank" rel="noopener">네이버 지도에서 보기</a>
    </div>

    <div class="box">
      <b>👥 하루 약 ${crowd(e.crowd_estimate.per_day)}명 예상</b>
      ${tags ? `<div class="muted">${tags}</div>` : ""}
      ${p.evidence.length ? `<ul>${p.evidence.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
    </div>

    ${e.peak_hours.length ? `<div class="box"><b>⏰ 손님 몰리는 시간</b>
      <ul>${e.peak_hours.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}

    ${e.order_advice.length ? `<div class="box"><b>📦 발주 추천 (평소 대비)</b>
      <table>${e.order_advice.map((a) => `<tr><td>${esc(a.item)}</td><td class="x">×${a.multiplier}</td></tr>`).join("")}</table>
    </div>` : ""}

    ${e.sources.length ? `<div class="box small"><b>출처</b>
      <ul>${e.sources.map((s) => `<li><a href="${esc(s)}" target="_blank" rel="noopener">${esc(s.replace(/^https?:\/\//, "").slice(0, 48))}</a></li>`).join("")}</ul>
    </div>` : ""}`;
}

function urlBase64ToUint8Array(base64) {
  const pad = "=".repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + pad).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}

async function renderSettings() {
  const supported = "serviceWorker" in navigator && "PushManager" in window;
  const key = (window.APP_CONFIG || {}).VAPID_PUBLIC_KEY;
  let sub = null;
  if (supported) {
    const reg = await navigator.serviceWorker.ready;
    sub = await reg.pushManager.getSubscription();
  }
  app.innerHTML = `
    <a class="back" href="#">← 목록</a>
    <h2>알림 설정</h2>
    ${!supported ? `<p>이 브라우저는 알림을 지원하지 않아요. 크롬에서 열고 "홈 화면에 추가"로 설치해 주세요.</p>` : ""}
    ${supported && !key ? `<p class="muted">관리자 설정(VAPID 공개키)이 아직 없어요.</p>` : ""}
    ${supported && key ? `
      <p>${sub ? "✅ 알림이 켜져 있어요." : "알림을 켜면 새 행사·발주 시기를 폰으로 알려드려요."}</p>
      <button class="btn" id="enable">${sub ? "알림 다시 등록" : "알림 켜기"}</button>
      <button class="btn ghost" id="local">이 폰에서 알림 모양 미리보기</button>
      <div id="subbox" ${sub ? "" : "hidden"}>
        <h2>관리자에게 보낼 등록 코드</h2>
        <p class="muted small">아래 코드를 복사해서 관리자에게 보내주세요. (한 번만 하면 돼요)</p>
        <textarea id="subjson" readonly>${sub ? esc(JSON.stringify(sub)) : ""}</textarea>
        <button class="btn ghost" id="copy">코드 복사</button>
      </div>` : ""}`;

  const enable = document.getElementById("enable");
  if (enable) enable.onclick = async () => {
    const perm = await Notification.requestPermission();
    if (perm !== "granted") { alert("알림 권한이 꺼져 있어요. 크롬 설정에서 허용해 주세요."); return; }
    const reg = await navigator.serviceWorker.ready;
    const old = await reg.pushManager.getSubscription();
    if (old) await old.unsubscribe();
    await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(key) });
    renderSettings();
  };
  const local = document.getElementById("local");
  if (local) local.onclick = async () => {
    if ((await Notification.requestPermission()) !== "granted") return;
    const reg = await navigator.serviceWorker.ready;
    reg.showNotification("🆕 [S] 예시 콘서트", { body: "11/14(토) · 인천문학경기장 주경기장 · 하루 4.9만 명 예상", icon: "icon-192.png", data: { url: "./" } });
  };
  const copy = document.getElementById("copy");
  if (copy) copy.onclick = async () => {
    const ta = document.getElementById("subjson");
    try { await navigator.clipboard.writeText(ta.value); } catch (_) { ta.select(); document.execCommand("copy"); }
    copy.textContent = "복사됨 ✓";
  };
}

function route() {
  const h = location.hash;
  if (h.startsWith("#event=")) renderEvent(decodeURIComponent(h.slice(7)));
  else if (h === "#settings") renderSettings();
  else renderHome();
  window.scrollTo(0, 0);
}

async function load() {
  try {
    const [ev, vn] = await Promise.all([
      fetch("data/events.json", { cache: "no-store" }).then((r) => r.json()),
      fetch("data/venues.json").then((r) => r.json()),
    ]);
    DATA = ev;
    VENUES = Object.fromEntries(vn.venues.map((v) => [v.id, v]));
    route();
  } catch (err) {
    app.innerHTML = `<p class="pad">데이터를 불러오지 못했어요. 인터넷 연결을 확인해 주세요.</p>`;
  }
}

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
window.addEventListener("hashchange", () => DATA && route());
load();

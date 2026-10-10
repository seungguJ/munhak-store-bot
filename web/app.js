"use strict";

const app = document.getElementById("app");
const WEEKDAYS = "일월화수목금토";
const GRADE_TEXT = { S: "초대형", A: "대형", B: "중형", C: "소형" };
const GRADE_RANGE = { S: "3만+", A: "1만+", B: "3천+", C: "그 외" };
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
  return `${d.getMonth() + 1}월 ${d.getDate()}일 (${WEEKDAYS[d.getDay()]})`;
}
function period(e) {
  if (e.start === e.end) return fmtDate(e.start);
  const s = parseDate(e.start), t = parseDate(e.end);
  const end = s.getMonth() === t.getMonth() ? `${t.getDate()}일 (${WEEKDAYS[t.getDay()]})` : fmtDate(e.end);
  return `${fmtDate(e.start)} ~ ${end}`;
}
function daysUntil(e) {
  return Math.round((parseDate(e.start) - today()) / 86400000);
}
function dday(e) {
  const n = daysUntil(e);
  if (n > 0) return `D-${n}`;
  if (n === 0) return "오늘";
  return "진행 중";
}
function crowdParts(n) {
  if (n >= 10000) return [(n / 10000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, ""), "만 명"];
  return [n.toLocaleString("ko-KR"), "명"];
}
function crowdText(n) {
  const [v, u] = crowdParts(n);
  return v + u;
}
function fmtUpdated(d) {
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const mins = Math.round((Date.now() - d) / 60000);
  const ago = mins < 1 ? "방금" : mins < 60 ? `${mins}분 전` : mins < 1440 ? `${Math.round(mins / 60)}시간 전` : `${Math.round(mins / 1440)}일 전`;
  return `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm} 조사 · ${ago}`;
}
function gradeVars(g) {
  return `--g: var(--${g}); --g-soft: var(--${g}-soft)`;
}
function venueOf(e) {
  return VENUES[e.venue_id] || { name: e.venue_id, distance_km: "?" };
}
function upcoming(e) {
  return e.status !== "done" && parseDate(e.end) >= today();
}
function firstRun() {
  return !DATA.events.length && DATA.updated_at.indexOf("T00:00:00") >= 0;
}

/* ── 홈 ── */
function heroCard(e) {
  const v = venueOf(e);
  const [cv, cu] = crowdParts(e.crowd_estimate.per_day);
  const top = e.order_advice[0];
  const days = daysUntil(e);
  return `
    <a class="hero" style="${gradeVars(e.grade)}" href="#event=${encodeURIComponent(e.id)}">
      <div class="hero-top">
        <div class="hero-dday num">${dday(e)}<small>${days > 0 ? fmtDate(e.start) : period(e)}</small></div>
        <span class="grade-chip"><b>${e.grade}</b>${GRADE_TEXT[e.grade]}</span>
      </div>
      <div class="hero-title">${esc(e.title)}</div>
      <div class="hero-meta">${esc(v.name)} · 선학역 ${v.distance_km}km</div>
      <div class="facts">
        <div class="fact"><span>하루 예상 인파</span><strong class="num">${cv}<em>${cu}</em></strong></div>
        <div class="fact"><span>${top ? "발주 1순위" : "기간"}</span><strong>${top ? `${esc(top.item.split("·")[0])} <em>×${top.multiplier}</em>` : `${e.start === e.end ? 1 : Math.round((parseDate(e.end) - parseDate(e.start)) / 86400000) + 1}<em>일</em>`}</strong></div>
      </div>
      <div class="hero-cta"><span>${e.order_advice.length ? "발주 추천 · 혼잡 시간 보기" : "자세히 보기"}</span><span aria-hidden="true">→</span></div>
    </a>`;
}

function listItem(e) {
  const v = venueOf(e);
  const d = parseDate(e.start);
  const cancelled = e.status === "cancelled";
  return `
    <a class="item ${cancelled ? "cancelled" : ""}" style="${gradeVars(cancelled ? "C" : e.grade)}" href="#event=${encodeURIComponent(e.id)}">
      <div class="date-col num"><span class="m">${d.getMonth() + 1}월</span><span class="d">${d.getDate()}</span><span class="w">${WEEKDAYS[d.getDay()]}</span></div>
      <div>
        <div class="item-title">${cancelled ? `<span class="tag-cancel">취소</span>` : ""}${esc(e.title)}</div>
        <div class="item-meta">${cancelled ? "" : `<b class="num">${dday(e)}</b> · `}${esc(v.name)}</div>
      </div>
      <div class="item-right"><span class="g">${e.grade}</span><span class="c num">${crowdText(e.crowd_estimate.per_day)}</span></div>
    </a>`;
}

function legend() {
  return `<div class="legend">${["S", "A", "B", "C"].map((g) =>
    `<div style="${gradeVars(g)}"><b>${g}</b><span>${GRADE_TEXT[g]}<br>${GRADE_RANGE[g]}</span></div>`).join("")}</div>`;
}

function renderHome() {
  const list = DATA.events.filter(upcoming).sort((a, b) => a.start.localeCompare(b.start));
  const live = list.filter((e) => e.status !== "cancelled");
  const big = live.filter((e) => e.grade !== "C");
  const small = live.filter((e) => e.grade === "C");
  const cancelled = list.filter((e) => e.status === "cancelled");
  const status = firstRun() ? "첫 조사를 기다리는 중 · 매주 월요일 아침 조사" : fmtUpdated(new Date(DATA.updated_at));

  if (!big.length) {
    app.innerHTML = `
      <p class="status-line">${status}</p>
      <div class="empty">
        <h2>${firstRun() ? "곧 첫 조사가 시작돼요" : "다가오는 큰 행사가 없어요"}</h2>
        <p>콘서트나 큰 행사가 잡히면 바로 알림을 보내드려요. 행사 7일 전과 전날에도 다시 알려드려요.</p>
      </div>
      ${small.length ? `<div class="eyebrow">소규모 행사<small>알림 없음</small></div><div class="list">${small.map(listItem).join("")}</div>` : ""}
      ${cancelled.length ? `<div class="eyebrow">취소된 행사</div><div class="list">${cancelled.map(listItem).join("")}</div>` : ""}
      <div class="eyebrow">등급 기준<small>하루 예상 인파</small></div>
      ${legend()}`;
    return;
  }

  const [next, ...rest] = big;
  app.innerHTML = `
    <p class="status-line">${status}</p>
    ${heroCard(next)}
    ${rest.length ? `<div class="eyebrow">다가오는 행사<small>${rest.length}건</small></div><div class="list">${rest.map(listItem).join("")}</div>` : ""}
    ${small.length ? `<div class="eyebrow">소규모 행사<small>알림 없음</small></div><div class="list">${small.map(listItem).join("")}</div>` : ""}
    ${cancelled.length ? `<div class="eyebrow">취소된 행사</div><div class="list">${cancelled.map(listItem).join("")}</div>` : ""}
    <div class="eyebrow">등급 기준<small>하루 예상 인파</small></div>
    ${legend()}`;
}

/* ── 상세 ── */
function peakRow(text) {
  const m = text.match(/^(\d{1,2}:\d{2}\s*[-~]\s*\d{1,2}:\d{2})\s*(.*)$/);
  return m ? `<div class="peak"><b>${esc(m[1])}</b><span>${esc(m[2])}</span></div>`
           : `<div class="peak"><span>${esc(text)}</span></div>`;
}

function renderEvent(id) {
  const e = DATA.events.find((x) => x.id === id);
  if (!e) {
    app.innerHTML = `<a class="back" href="#">← 목록</a><div class="empty"><h2>행사를 찾을 수 없어요</h2><p>지난 행사이거나 정보가 바뀌었을 수 있어요.</p></div>`;
    return;
  }
  const v = venueOf(e);
  const map = `https://map.naver.com/p/search/${encodeURIComponent(v.name)}`;
  const p = e.popularity;
  const [cv, cu] = crowdParts(e.crowd_estimate.per_day);
  const cancelled = e.status === "cancelled";
  const tags = [p.sold_out ? "매진" : "", p.extra_shows ? "추가 회차" : ""].filter(Boolean);
  const g = cancelled ? "C" : e.grade;
  app.innerHTML = `
    <a class="back" href="#">← 목록</a>
    <div class="hero" style="${gradeVars(g)}">
      <div class="hero-top">
        <div class="hero-dday num">${cancelled ? "취소" : dday(e)}<small>${period(e)}${e.show_times && e.show_times.length ? "<br>" + e.show_times.join(", ") + " 시작" : ""}</small></div>
        <span class="grade-chip"><b>${e.grade}</b>${GRADE_TEXT[e.grade]}</span>
      </div>
      <div class="hero-title">${esc(e.title)}</div>
      <div class="facts">
        <div class="fact"><span>하루 예상 인파</span><strong class="num">${cv}<em>${cu}</em></strong></div>
        <div class="fact"><span>예매 상황</span><strong>${tags.length ? tags.join(" · ") : "판매 중"}</strong></div>
      </div>
    </div>

    ${e.order_advice.length ? `<div class="section" style="${gradeVars(g)}"><h3>발주 추천 · 평소 대비</h3>
      <div class="orders">${e.order_advice.map((a) => `<div class="order"><span>${esc(a.item)}</span><b class="num">×${a.multiplier}</b></div>`).join("")}</div>
    </div>` : ""}

    ${e.peak_hours.length ? `<div class="section"><h3>손님 몰리는 시간</h3><div class="peaks">${e.peak_hours.map(peakRow).join("")}</div></div>` : ""}

    <div class="section">
      <h3>장소</h3>
      <div class="place">${esc(v.name)}<small>선학역에서 약 ${v.distance_km}km</small></div>
      <a class="btn ghost" href="${map}" target="_blank" rel="noopener">네이버 지도에서 보기</a>
    </div>

    ${p.evidence.length ? `<div class="section"><h3>인기 근거</h3><ul>${p.evidence.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}

    ${e.sources.length ? `<div class="section sources"><h3>출처</h3><ul>${e.sources.map((s) =>
      `<li><a href="${esc(s)}" target="_blank" rel="noopener">${esc(s.replace(/^https?:\/\/(www\.)?/, "").slice(0, 42))}</a></li>`).join("")}</ul></div>` : ""}`;
}

/* ── 설정 ── */
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
  const on = !!sub && Notification.permission === "granted";
  app.innerHTML = `
    <a class="back" href="#">← 목록</a>
    <h1 class="page">알림 설정</h1>
    ${!supported ? `<div class="section"><p>이 브라우저는 알림을 지원하지 않아요. 크롬에서 열고 "홈 화면에 추가"로 설치해 주세요.</p></div>` : ""}
    ${supported && !key ? `<div class="section"><p class="hint">관리자 설정(VAPID 공개키)이 아직 없어요.</p></div>` : ""}
    ${supported && key ? `
      <div class="section">
        <div class="status-card">
          <div class="status-icon ${on ? "on" : ""}" aria-hidden="true">${on ? "🔔" : "🔕"}</div>
          <div><strong>${on ? "알림이 켜져 있어요" : "알림이 꺼져 있어요"}</strong>
          <span>새 행사 · 7일 전 · 전날에 알려드려요</span></div>
        </div>
        <button class="btn" id="enable">${on ? "알림 다시 등록" : "알림 켜기"}</button>
        <button class="btn ghost" id="local">알림 미리보기</button>
      </div>
      <div class="section" id="subbox" ${sub ? "" : "hidden"}>
        <h3>등록 코드</h3>
        <p class="hint">처음 한 번만 관리자에게 보내주세요.</p>
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
    reg.showNotification("🆕 [S] 예시 콘서트", { body: "11/14(토) · 인천문학경기장 주경기장 · 하루 4.9만 명 예상", icon: "icon-192.png", badge: "badge-96.png", data: { url: "./" } });
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
    app.innerHTML = `<div class="empty"><h2>불러오지 못했어요</h2><p>인터넷 연결을 확인하고 다시 열어 주세요.</p></div>`;
  }
}

if ("serviceWorker" in navigator) {
  // 새 버전 서비스워커가 자리 잡으면 한 번 새로고침해 최신 화면으로
  let reloaded = false;
  const hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (hadController && !reloaded) { reloaded = true; location.reload(); }
  });
  navigator.serviceWorker.register("sw.js").then((reg) => reg.update());
}
window.addEventListener("hashchange", () => DATA && route());
load();

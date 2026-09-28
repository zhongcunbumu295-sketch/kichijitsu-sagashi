/* 今日の暦・次の開運日・吉日検索。暦データは build.py が出力する /data/koyomi.json */
(() => {
  "use strict";
  const BASE = document.body.dataset.base || "";
  const WEEK = "日月火水木金土";
  const DAY_MS = 86400000;
  const TIME_NOTE = {
    "先勝": "午前中がおすすめ",
    "先負": "午後がおすすめ",
    "友引": "朝・夕方がおすすめ（昼は避ける）",
    "赤口": "正午（11〜13時ごろ）がおすすめ",
  };
  const UPCOMING = [
    ["saikyo", "最強開運日", "saikyo-kaiunbi"], ["tensha", "天赦日", "tenshanichi"],
    ["ichiryu", "一粒万倍日", "ichiryumanbaibi"], ["tora", "寅の日", "toranohi"],
    ["mi", "巳の日", "minohi"], ["tsuchinotomi", "己巳の日", "minohi"],
    ["kinoene", "甲子の日", "kinoenenohi"], ["taian", "大安", "taian"],
  ];

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const parseISO = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(Date.UTC(y, m - 1, d)); };
  const toISO = (dt) => dt.toISOString().slice(0, 10);
  const addDays = (dt, n) => new Date(dt.getTime() + n * DAY_MS);
  const addMonths = (dt, n) => {
    const y = dt.getUTCFullYear(), m = dt.getUTCMonth() + n;
    const last = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    return new Date(Date.UTC(y, m, Math.min(dt.getUTCDate(), last)));
  };
  const md = (dt) => `${dt.getUTCMonth() + 1}月${dt.getUTCDate()}日（${WEEK[dt.getUTCDay()]}）`;
  const ymd = (dt) => `${dt.getUTCFullYear()}年${md(dt)}`;
  const todayISO = () => {
    const parts = new Intl.DateTimeFormat("ja-JP", {
      timeZone: "Asia/Tokyo", year: "numeric", month: "2-digit", day: "2-digit",
    }).formatToParts(new Date());
    const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
    return `${p.year}-${p.month}-${p.day}`;
  };

  // ------------------------------------------------------------ データ
  let cache;
  const load = () => cache || (cache = fetch(`${BASE}/data/koyomi.json`)
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(decode));

  function decode(K) {
    const start = parseISO(K.start);
    K.days = K.days.map((a, i) => {
      const dt = addDays(start, i);
      return {
        dt, iso: toISO(dt), k: a[0], r: a[1], lm: a[2], ld: a[3], leap: !!a[4],
        marks: a[5] ? a[5].split(",") : [], sekki: a[6], holiday: a[7],
        zassetsu: a[8] ? a[8].split("|") : [], moon: a[9], age: a[10], doyo: !!a[11],
      };
    });
    K.index = new Map(K.days.map((d, i) => [d.iso, i]));
    K.purposeByKey = Object.fromEntries(K.purposes.map((p) => [p.key, p]));
    return K;
  }

  const rokuyo = (K, d) => K.rokuyo[d.r];
  const kanshi = (K, d) => K.stems[d.k % 10] + K.branches[d.k % 12];
  const isRest = (d) => d.dt.getUTCDay() % 6 === 0 || !!d.holiday;
  const isSaikyo = (d) => d.marks.includes("tensha") && d.marks.includes("ichiryu");
  // 天赦日は凶日を打ち消すとされるため、六曜の凶（仏滅・赤口）は数えない（koyomi/marks.py と同じ）
  const TENSHA_CANCELS = ["butsumetsu", "shakku"];
  const keysOf = (K, d) => {
    const keys = [...d.marks, K.rokuyoInfo[rokuyo(K, d)].key, ...(d.doyo ? ["doyo"] : [])];
    return d.marks.includes("tensha") ? keys.filter((k) => !TENSHA_CANCELS.includes(k)) : keys;
  };
  const scoreOf = (K, d, p) => keysOf(K, d).reduce((s, k) => s + (p.weights[k] || 0), 0);
  const nameOf = (K, k) => (K.marks[k] && K.marks[k].name)
    || Object.keys(K.rokuyoInfo).find((n) => K.rokuyoInfo[n].key === k)
    || (k === "doyo" ? "土用の期間" : k);
  const rank = (s) => (s >= 8 ? { sym: "◎", label: "最良", cls: "r3" }
    : s >= 5 ? { sym: "○", label: "良い", cls: "r2" }
      : s >= 2 ? { sym: "△", label: "まずまず", cls: "r1" }
        : s <= -3 ? { sym: "✕", label: "避けたい", cls: "r0" }
          : { sym: "－", label: "普通", cls: "r0" });
  const dayLink = (d) => `${BASE}/calendar/${d.iso.slice(0, 4)}/${d.iso.slice(5, 7)}/#d-${d.iso}`;
  const matcher = (K, key) => (key === "saikyo" ? isSaikyo
    : key === "taian" ? (d) => rokuyo(K, d) === "大安"
      : (d) => d.marks.includes(key));

  function indexFrom(K, iso) {
    if (iso < K.start) return 0;
    if (iso > K.end) return K.days.length;
    return K.index.get(iso);
  }

  function firstFrom(K, iso, pred) {
    for (let i = indexFrom(K, iso); i < K.days.length; i++) if (pred(K.days[i])) return K.days[i];
    return null;
  }

  function countdown(d, today) {
    if (!d) return "計算範囲内にありません";
    const diff = Math.round((d.dt - parseISO(today)) / DAY_MS);
    return `${ymd(d.dt)}（${diff === 0 ? "今日" : `あと${diff}日`}）`;
  }

  function badges(K, d, withRokuyo = true) {
    let h = "";
    if (withRokuyo) {
      const r = rokuyo(K, d);
      const cls = r === "大安" ? "rk-good" : (r === "仏滅" || r === "赤口") ? "rk-bad" : "rk";
      h += `<span class="b ${cls}">${r}</span>`;
    }
    for (const k of d.marks) h += `<span class="b m-${k}">${esc(K.marks[k].name)}</span>`;
    return h;
  }

  // ------------------------------------------------------------ 今日の暦
  function todayCard(K, i) {
    const d = K.days[i];
    const r = rokuyo(K, d);
    const notes = d.marks.map((k) => `<li><strong>${esc(K.marks[k].name)}</strong>：${esc(K.marks[k].summary)}</li>`).join("");
    const extra = [];
    if (d.holiday) extra.push(esc(d.holiday));
    for (let j = i; j >= 0; j--) {
      const s = K.days[j];
      if (s.sekki) { extra.push(`二十四節気：${esc(s.sekki)}（${s.dt.getUTCMonth() + 1}月${s.dt.getUTCDate()}日〜）`); break; }
    }
    extra.push(`月齢：${d.age.toFixed(1)}`);
    return `<p class="today-date">${ymd(d.dt)}<span class="muted small">旧暦${d.leap ? "閏" : ""}${d.lm}月${d.ld}日・${kanshi(K, d)}の日</span></p>`
      + `<p class="today-rk"><span class="rk-big">${r}</span><span class="small">${esc(K.rokuyoInfo[r].desc)}</span></p>`
      + `<div class="today-marks">${badges(K, d, false) || '<span class="muted">特別な暦注はありません</span>'}</div>`
      + (notes ? `<ul class="today-notes">${notes}</ul>` : "")
      + `<p class="small muted">${extra.join("｜")}</p>`;
  }

  function renderToday(K, today) {
    const el = document.getElementById("today");
    const i = K.index.get(today);
    if (el && i != null) el.innerHTML = todayCard(K, i);
  }

  function renderUpcoming(K, today) {
    const el = document.getElementById("upcoming");
    if (!el) return;
    const items = UPCOMING.map(([key, label, slug]) => {
      const d = firstFrom(K, today, matcher(K, key));
      return `<li data-key="${key}"><a href="${BASE}/koyomi/${slug}/">${label}</a><span class="up-date">${countdown(d, today)}</span></li>`;
    }).join("");
    el.innerHTML = `<ul class="upcoming">${items}</ul>`;
  }

  function renderNext(K, today) {
    document.querySelectorAll("[data-next]").forEach((el) => {
      const preds = el.dataset.next.split(",").map((k) => matcher(K, k));
      const d = firstFrom(K, today, (x) => preds.some((f) => f(x)));
      el.querySelector(".next-body").textContent = countdown(d, today);
    });
    document.querySelectorAll("[data-next-purpose]").forEach((el) => {
      const p = K.purposeByKey[el.dataset.nextPurpose];
      const d = firstFrom(K, today, (x) => scoreOf(K, x, p) >= 5);
      el.querySelector(".next-body").textContent = countdown(d, today);
    });
    document.querySelectorAll("[data-today-rokuyo]").forEach((el) => {
      const i = K.index.get(today);
      if (i != null) el.querySelector(".next-body").textContent = `${md(K.days[i].dt)}は${rokuyo(K, K.days[i])}`;
    });
  }

  // 過ぎた日付を薄く、今日を強調する（カレンダーのマスは今日だけ）
  function markDates(today) {
    document.querySelectorAll("[data-date]").forEach((el) => {
      const v = el.dataset.date;
      if (v === today) el.classList.add("is-today");
      else if (v < today && el.tagName !== "TD") el.classList.add("past");
    });
  }

  // ------------------------------------------------------------ 吉日検索
  function initSearch(today) {
    const form = document.getElementById("search-form");
    if (!form) return;
    const results = document.getElementById("results");
    const params = new URLSearchParams(location.search);
    const radio = params.get("p") && form.querySelector(`input[name="p"][value="${CSS.escape(params.get("p"))}"]`);
    if (radio) radio.checked = true;
    if (params.get("range")) form.range.value = params.get("range");
    if (params.get("from")) form.from.value = params.get("from");
    if (params.get("to")) form.to.value = params.get("to");
    if (params.has("avoid")) form.avoid.checked = params.get("avoid") !== "0";
    const toggleCustom = () => form.querySelectorAll(".custom").forEach((el) => { el.hidden = form.range.value !== "custom"; });
    form.range.addEventListener("change", toggleCustom);
    toggleCustom();
    let sortBy = "score";

    async function run(updateUrl) {
      const K = await load();
      const pKey = form.querySelector('input[name="p"]:checked').value;
      const p = K.purposeByKey[pKey];
      let from = today;
      let to;
      if (form.range.value === "custom") {
        from = form.from.value || today;
        to = form.to.value || toISO(addDays(addMonths(parseISO(from), 3), -1));
      } else {
        to = toISO(addDays(addMonths(parseISO(today), Number(form.range.value)), -1));
      }
      if (from < K.start) from = K.start;
      if (to > K.end) to = K.end;
      if (to < from) {
        results.innerHTML = "<p>終了日は開始日より後の日付にしてください。</p>";
        return;
      }
      const avoidKeys = Object.keys(p.weights).filter((k) => p.weights[k] <= -3);
      const list = [];
      for (let i = K.index.get(from); i <= K.index.get(to); i++) {
        const d = K.days[i];
        if (form.rest.checked && !isRest(d)) continue;
        const keys = keysOf(K, d);
        if (form.avoid.checked && keys.some((k) => avoidKeys.includes(k))) continue;
        const s = keys.reduce((a, k) => a + (p.weights[k] || 0), 0);
        if (s >= 2) list.push({ d, s, keys });
      }
      const count = (cls) => list.filter((x) => rank(x.s).cls === cls).length;
      list.sort(sortBy === "date" ? (a, b) => a.d.dt - b.d.dt : (a, b) => b.s - a.s || a.d.dt - b.d.dt);
      const shown = sortBy === "date" ? list : list.slice(0, 30);
      const items = shown.map(({ d, s, keys }) => {
        const rk = rank(s);
        const good = [...new Set(keys.filter((k) => (p.weights[k] || 0) > 0).map((k) => p.reasons[k] || nameOf(K, k)))];
        const bad = keys.filter((k) => (p.weights[k] || 0) < 0).map((k) => nameOf(K, k));
        const r = rokuyo(K, d);
        const tnote = d.marks.includes("tensha") && (r === "仏滅" || r === "赤口")
          ? `${r}ですが、天赦日と重なるため凶は打ち消されるとされます`
          : TIME_NOTE[r] && `${r}のため${TIME_NOTE[r]}`;
        return `<article class="result ${rk.cls}"><div class="sym">${rk.sym}<small>${rk.label}</small></div><div>`
          + `<h3><a href="${dayLink(d)}">${ymd(d.dt)}</a>${isRest(d) ? ' <span class="rest">休</span>' : ""}`
          + `${d.holiday ? ` <span class="small muted">${esc(d.holiday)}</span>` : ""}</h3>`
          + `<div>${badges(K, d)}</div>`
          + (good.length ? `<p class="why">${esc(good.join("／"))}</p>` : "")
          + (bad.length ? `<p class="caution">注意：${esc(bad.join("・"))}</p>` : "")
          + (tnote ? `<p class="caution">${esc(tnote)}</p>` : "")
          + "</div></article>";
      }).join("");
      results.innerHTML = `<p class="result-summary">${ymd(parseISO(from))}〜${ymd(parseISO(to))}の「${esc(p.name)}」に良い日：`
        + `◎${count("r3")}日・○${count("r2")}日・△${count("r1")}日`
        + `<button type="button" class="sort-toggle">${sortBy === "date" ? "おすすめ順にする" : "日付順にする"}</button></p>`
        + (items || "<p>条件に合う日が見つかりませんでした。期間を広げるか、条件を外してお試しください。</p>")
        + (sortBy !== "date" && list.length > 30 ? `<p class="small muted">評価の高い30日を表示しています（全${list.length}日）。</p>` : "");
      results.querySelector(".sort-toggle").addEventListener("click", () => {
        sortBy = sortBy === "date" ? "score" : "date";
        run(false);
      });
      if (updateUrl) {
        const q = new URLSearchParams({ p: pKey, range: form.range.value });
        if (form.range.value === "custom") { q.set("from", from); q.set("to", to); }
        if (form.rest.checked) q.set("rest", "1");
        if (!form.avoid.checked) q.set("avoid", "0");
        history.replaceState(null, "", `?${q}`);
      }
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      sortBy = "score";
      run(true).then(() => results.scrollIntoView({ behavior: "smooth", block: "start" }));
    });
    load().then((K) => {
      const p = K.purposeByKey[form.querySelector('input[name="p"]:checked').value];
      form.rest.checked = params.has("rest") ? params.get("rest") === "1" : !!(radio && p.rest);
      return run(false);
    }).catch(showError(results));
  }

  function initLookup(today) {
    const input = document.getElementById("lookup-date");
    if (!input) return;
    const out = document.getElementById("lookup-result");
    load().then((K) => {
      input.min = K.start;
      input.max = K.end;
      input.value = today;
      const render = () => {
        const i = K.index.get(input.value);
        if (i == null) {
          out.innerHTML = `<p>${K.start.slice(0, 4)}年〜${K.end.slice(0, 4)}年の日付を選んでください。</p>`;
          return;
        }
        const d = K.days[i];
        const rows = K.purposes.map((p) => {
          const rk = rank(scoreOf(K, d, p));
          return `<tr><th scope="row">${esc(p.name)}</th><td class="rank ${rk.cls}">${rk.sym}<span class="small">${rk.label}</span></td></tr>`;
        }).join("");
        out.innerHTML = `${todayCard(K, i)}<div class="table-wrap"><table class="rule"><tbody>${rows}</tbody></table></div>`;
      };
      input.addEventListener("change", render);
      render();
    }).catch(showError(out));
  }

  const showError = (el) => (e) => {
    console.warn("暦データを読み込めませんでした", e);
    if (el) el.innerHTML = "<p>暦データを読み込めませんでした。時間をおいて再読み込みしてください。</p>";
  };

  // ------------------------------------------------------------ 起動
  const today = todayISO();
  markDates(today);
  if (document.querySelector("#today, #upcoming, [data-next], [data-next-purpose], [data-today-rokuyo]")) {
    load().then((K) => {
      renderToday(K, today);
      renderUpcoming(K, today);
      renderNext(K, today);
    }).catch((e) => console.warn("暦データを読み込めませんでした", e));
  }
  initSearch(today);
  initLookup(today);
})();

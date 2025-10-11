// static/reports/voice_logger.js

console.log("voice_logger.js LOADED"); // 読み込み確認

(function () {
  // ===== DOM取得 =====
  const $ = (id) => document.getElementById(id);
  const txt = $("text");
  const player = $("player");
  const meterCanvas = $("meter");
  const meterValue = $("meterValue");
  const btnSpeak = $("btnSpeak");
  const btnTTS = $("btnTTS");           // ヘッダーTTSボタン（同じ動作）
  const btnSave = $("btnSave");
  const btnClear = $("btnClear");
  const btnSync = $("btnSync");
  const btnPurge = $("btnPurge");
  const tbody = document.querySelector("#tblDrafts tbody");
  const settingsPanel = $("settingsPanel");
  const btnToggleSettings = $("btnToggleSettings");

  if (btnToggleSettings && settingsPanel) {
    btnToggleSettings.addEventListener("click", () => {
      const show = settingsPanel.style.display === "none";
      settingsPanel.style.display = show ? "block" : "none";
    });
  }

  const elVoice = $("voice");
  const elStyle = $("style");
  const elStyleDegree = $("styledegree");
  const elRate = $("rate");
  const elPitch = $("pitch");
  const elFormat = $("format");

  // ===== 設定（トークン） =====
  const cfgEl = $("__cfg");
  const TOKEN = cfgEl ? (cfgEl.dataset.token || "devtoken") : "devtoken";

  // ===== ユーティリティ =====
  function toast(m) { try { console.log("[INFO]", m); } catch {} }
  const DRAFT_KEY = "neoinfinity_voice_logs_v3";
  const QUEUE_KEY = "fn_voice_queue";

  function readDrafts() {
    try { const a = JSON.parse(localStorage.getItem(DRAFT_KEY) || "[]"); return Array.isArray(a) ? a : []; }
    catch { return []; }
  }
  function writeDrafts(a) { localStorage.setItem(DRAFT_KEY, JSON.stringify(a || [])); }
  function readQueue() {
    try { const a = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]"); return Array.isArray(a) ? a : []; }
    catch { return []; }
  }
  function writeQueue(a) { localStorage.setItem(QUEUE_KEY, JSON.stringify(a || [])); }

  function nowISO() {
    const d = new Date(); const tz = -d.getTimezoneOffset();
    const sign = tz >= 0 ? "+" : "-";
    const hh = String(Math.floor(Math.abs(tz) / 60)).padStart(2, "0");
    const mm = String(Math.abs(tz) % 60).padStart(2, "0");
    return d.toISOString().replace("Z", `${sign}${hh}:${mm}`);
  }

  // ===== テーブル描画 =====
  function renderDrafts() {
    const arr = readDrafts();
    tbody.innerHTML = "";
    if (!arr.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="4" class="text-center text-secondary">下書きはありません。</td>';
      tbody.appendChild(tr);
      if (btnSync) btnSync.classList.add("disabled");
      return;
    }
    if (btnSync) btnSync.classList.remove("disabled");

    arr.forEach((it, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${it.id || "-"}</td>
        <td class="text-break">${(it.text || "").replace(/</g, "&lt;")}</td>
        <td>${it.ts || ""}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary" data-act="load" data-idx="${idx}">読込</button>
          <button class="btn btn-sm btn-outline-danger" data-act="del" data-idx="${idx}">削除</button>
        </td>`;
      tbody.appendChild(tr);
    });
  }

  if (tbody) {
    tbody.addEventListener("click", (e) => {
      const btn = e.target.closest("button"); if (!btn) return;
      const act = btn.dataset.act; const idx = +btn.dataset.idx;
      const arr = readDrafts();
      if (act === "load") {
        const t = (arr[idx]?.text || "").trim();
        if (t) { txt.value = t; txt.focus(); }
      } else if (act === "del") {
        arr.splice(idx, 1); writeDrafts(arr); renderDrafts();
      }
    });
  }

  // ===== API =====
  async function postVoiceLog(payload, idem) {
    try {
      const res = await fetch("/api/voice-logs/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Authorization": `Bearer ${TOKEN}`,
          "Idempotency-Key": String(idem || payload.id || Date.now()),
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) return false;
      const j = await res.json().catch(() => ({ ok: true }));
      return j?.ok !== false;
    } catch {
      return false;
    }
  }

  // ===== キュー再送（指数バックオフ） =====
  async function retryQueue() {
    const q = readQueue(); if (!q.length) { toast("未送信はありません"); return true; }

    const maxAttempts = 6;
    const remaining = [];
    for (const item of q) {
      item.attempts = item.attempts || 0;
      item.idem = item.idem || item.id || String(Date.now());

      let ok = false, attempt = item.attempts;
      while (attempt < maxAttempts) {
        ok = await postVoiceLog(item, item.idem);
        if (ok) break;
        const wait = Math.min(30000, Math.pow(2, attempt) * 500 + Math.random() * 400);
        await new Promise(r => setTimeout(r, wait));
        attempt++;
      }
      if (!ok) {
        item.attempts = attempt;
        remaining.push(item);
      } else {
        // 成功 → 同じIDの下書きをローカルからも削除
        const drafts = readDrafts().filter(d => d.id !== item.id);
        writeDrafts(drafts);
      }
    }
    writeQueue(remaining);
    renderDrafts();
    toast(remaining.length ? `未送信が ${remaining.length} 件残っています` : "未送信をすべて送信しました");
    return remaining.length === 0;
  }
  // コンソール用
  window.retryQueue = retryQueue;
  window.renderDrafts = renderDrafts;

  // ===== 保存（ローカル & キュー投入） =====
  function pushDraft(text) {
    const arr = readDrafts();
    const item = { id: Date.now(), text, intent: "note", ts: nowISO() };
    arr.unshift(item);
    writeDrafts(arr);
    const q = readQueue();
    q.push({ ...item });
    writeQueue(q);
    renderDrafts();
    toast("ローカルに保存しました");
  }
  window.pushDraft = pushDraft;

  // ===== TTS（短押し） =====
  async function doTTS() {
    const text = (txt?.value || "").trim();
    if (!text) { toast("テキストが空です"); return; }

    const payload = {
      text,
      voice: elVoice?.value || "ja-JP-NanamiNeural",
      style: (elStyle?.value || "").trim(),
      styledegree: parseFloat(elStyleDegree?.value || "1.1"),
      rate: elRate?.value || "-6%",
      pitch: elPitch?.value || "+1%",
      format: elFormat?.value || "audio-24khz-48kbitrate-mono-mp3",
    };

    try {
      const res = await fetch("/api/tts/", {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const t = await res.text();
        toast(`TTSエラー: ${res.status} ${t}`);
        return;
      }
      const buf = await res.arrayBuffer();
      const blob = new Blob([buf], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      if (player) {
        player.src = url;
        await player.play().catch(() => {});
      }
      // TTS後は任意で下書き保存したい人向け（コメントアウトのままでもOK）
      // pushDraft(text); retryQueue();
    } catch {
      toast("TTS通信に失敗しました");
    }
  }

  // ===== STT（長押しで録音→離すと確定して保存） =====
  const hasSTT = ("webkitSpeechRecognition" in window) || ("SpeechRecognition" in window);
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null;
  let sttActive = false;
  let pressTimer = null;
  const PRESS_MS = 400; // 長押し判定しきい値

  function startSTT() {
    if (!hasSTT) { toast("このブラウザは音声入力に非対応です（Chrome/Edge推奨）"); return; }
    if (sttActive) return;

    rec = new SpeechRec();
    rec.lang = "ja-JP";
    rec.interimResults = true;
    rec.continuous = true;

    let finalText = "";
    rec.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t;
        else interim += t;
      }
      // 入力欄にライブ反映（確定+暫定）
      if (txt) txt.value = (finalText + (interim ? " " + interim : "")).trim();
    };
    rec.onerror = (e) => { toast(`STTエラー: ${e.error || "unknown"}`); };
    rec.onend = () => {
      sttActive = false;
      // 確定したテキストで保存＆送信
      const text = (txt?.value || "").trim();
      if (text) { pushDraft(text); retryQueue(); }
    };

    try {
      rec.start();
      sttActive = true;
      toast("録音開始（指を離すと停止）");
    } catch (e) {
      toast("STT開始失敗");
    }
  }

  function stopSTT() {
    if (rec && sttActive) {
      try { rec.stop(); } catch {}
    }
  }

  function attachLongPressSTT(button) {
    if (!button) return;

    // マウス
    button.addEventListener("mousedown", () => {
      pressTimer = setTimeout(startSTT, PRESS_MS);
    });
    button.addEventListener("mouseup", (ev) => {
      clearTimeout(pressTimer);
      if (sttActive) {
        stopSTT();            // 長押し→離した：STT停止
      } else {
        doTTS();              // 短押し：TTS
      }
    });
    button.addEventListener("mouseleave", () => {
      clearTimeout(pressTimer);
      if (sttActive) stopSTT();
    });

    // タッチ（スマホ/タブレット）
    button.addEventListener("touchstart", (e) => {
      pressTimer = setTimeout(startSTT, PRESS_MS);
      e.preventDefault();
    }, { passive: false });
    button.addEventListener("touchend", (e) => {
      clearTimeout(pressTimer);
      if (sttActive) stopSTT(); else doTTS();
      e.preventDefault();
    }, { passive: false });
    button.addEventListener("touchcancel", () => {
      clearTimeout(pressTimer);
      if (sttActive) stopSTT();
    });
  }

  // ===== レベルメーター =====
  let audioCtx, analyser, srcNode, dataArray;
  function setupAnalyser() {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      if (srcNode) srcNode.disconnect();
      if (!player) return;
      srcNode = audioCtx.createMediaElementSource(player);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      srcNode.connect(analyser);
      analyser.connect(audioCtx.destination);
      dataArray = new Uint8Array(analyser.frequencyBinCount);
    } catch (e) { console.warn("Analyser init failed", e); }
  }
  function drawMeter() {
    if (!analyser || !meterCanvas || !meterValue) return;
    const ctx = meterCanvas.getContext("2d");
    const W = meterCanvas.width, H = meterCanvas.height;

    function frame() {
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      const db = 20 * Math.log10(rms || 1e-5);
      meterValue.textContent = isFinite(db) ? `${db.toFixed(1)} dB` : "-∞ dB";

      const level = Math.min(1, Math.max(0, rms * 4));
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "#0dcaf0";
      ctx.fillRect(0, 0, W * level, H);
      ctx.strokeStyle = "#555";
      ctx.strokeRect(0, 0, W, H);

      if (!player.paused && !player.ended) {
        requestAnimationFrame(frame);
      } else {
        ctx.clearRect(0, 0, W, H);
        ctx.strokeStyle = "#555";
        ctx.strokeRect(0, 0, W, H);
        meterValue.textContent = "-∞ dB";
      }
    }
    frame();
  }
  if (player) {
    player.addEventListener("play", () => { setupAnalyser(); drawMeter(); });
  }

  // ===== イベント束ね =====
  // 「話す（TTS）」ボタンを 長押し=STT / 短押し=TTS に割り当て
  attachLongPressSTT(btnSpeak);
  attachLongPressSTT(btnTTS);

  if (btnSave) btnSave.addEventListener("click", () => {
    const t = (txt?.value || "").trim();
    if (!t) { toast("テキストが空です"); return; }
    pushDraft(t);
    retryQueue();
  });

  if (btnClear) btnClear.addEventListener("click", () => { if (txt) txt.value = ""; });
  if (btnSync) btnSync.addEventListener("click", retryQueue);
  if (btnPurge) btnPurge.addEventListener("click", () => {
    writeDrafts([]); writeQueue([]); renderDrafts();
  });

  // ===== 初期化 =====
  function init() {
    const drafts = readDrafts();
    if (drafts.length && txt && !txt.value) {
      txt.value = drafts[0].text || "";
    }
    renderDrafts();
  }
  document.addEventListener("DOMContentLoaded", init);
})();

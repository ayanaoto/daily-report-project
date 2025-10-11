(function () {
  // CSSカラートークン（ダークでも見やすく）
  const css = (name, fallback) => {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  };
  const fg = css("--bs-body-color", "#e9ecef");
  const grid = css("--bs-border-color", "rgba(255,255,255,0.12)");

  // json_script から取得（空でも安全）
  const getJSON = (id) => {
    const el = document.getElementById(id);
    try { return el ? JSON.parse(el.textContent || "[]") : []; } catch { return []; }
  };

  const userLabels = getJSON("userLabels");
  const userData   = getJSON("userData");
  const progressLabels = getJSON("progressLabels");
  const progressData   = getJSON("progressData");
  const locLabels = getJSON("locLabels");
  const locData   = getJSON("locData");

  // 空データ時はメッセージ描画
  const renderEmpty = (canvas, msg) => {
    const ctx = canvas.getContext("2d");
    ctx.save();
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = fg;
    ctx.font = "16px system-ui, -apple-system, Segoe UI, Roboto";
    ctx.textAlign = "center";
    ctx.fillText(msg, canvas.width/2, canvas.height/2);
    ctx.restore();
  };

  // 1) 担当者別レポート件数（Bar）
  const el1 = document.getElementById("chartUserCounts");
  if (el1) {
    if (!userLabels.length) {
      renderEmpty(el1, "データなし");
    } else {
      new Chart(el1, {
        type: "bar",
        data: { labels: userLabels, datasets: [{ label: "レポート件数", data: userData }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: fg }, grid: { color: grid } },
            y: { ticks: { color: fg }, grid: { color: grid }, beginAtZero: true, precision: 0 }
          }
        }
      });
    }
  }

  // 2) あなたの進捗状況（Doughnut）
  const el2 = document.getElementById("chartMyProgress");
  if (el2) {
    if (!progressLabels.length) {
      renderEmpty(el2, "データなし");
    } else {
      new Chart(el2, {
        type: "doughnut",
        data: { labels: progressLabels, datasets: [{ label: "件数", data: progressData }] },
        options: {
          responsive: true,
          plugins: { legend: { labels: { color: fg } } },
          cutout: "60%"
        }
      });
    }
  }

  // 3) 場所別の工数（横Bar）
  const el3 = document.getElementById("chartLocationHours");
  if (el3) {
    if (!locLabels.length) {
      renderEmpty(el3, "データなし");
    } else {
      new Chart(el3, {
        type: "bar",
        data: { labels: locLabels, datasets: [{ label: "工数(h)", data: locData }] },
        options: {
          indexAxis: "y",
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: fg }, grid: { color: grid }, beginAtZero: true },
            y: { ticks: { color: fg }, grid: { color: grid } }
          }
        }
      });
    }
  }
})();

// ===== FieldNote JS (Jazzmin風UIヘルパ) =====
(function () {
  const btn = document.getElementById('fn-sidebar-toggle');
  const sidebar = document.getElementById('fn-sidebar');
  const STORAGE_KEY = 'fn.sidebar.open';

  function setOpen(open) {
    if (!sidebar) return;
    if (open) {
      sidebar.classList.add('is-open');
      localStorage.setItem(STORAGE_KEY, '1');
    } else {
      sidebar.classList.remove('is-open');
      localStorage.setItem(STORAGE_KEY, '0');
    }
  }

  // 初期状態
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === '1') setOpen(true);

  // トグル
  if (btn) {
    btn.addEventListener('click', function () {
      const isOpen = sidebar.classList.contains('is-open');
      setOpen(!isOpen);
    });
  }

  // 画面幅が広いときはサイドバーを閉じてグリッド表示に任せる
  function handleResize() {
    if (window.innerWidth >= 992) {
      // PCではoverlayではないので classはあっても実害なしだが消しておく
      sidebar && sidebar.classList.remove('is-open');
    }
  }
  window.addEventListener('resize', handleResize);

  // 外側クリックで閉じる（モバイル時）
  document.addEventListener('click', function (e) {
    if (window.innerWidth >= 992) return;
    if (!sidebar) return;
    const withinSidebar = sidebar.contains(e.target);
    const isToggleBtn = btn && btn.contains(e.target);
    if (!withinSidebar && !isToggleBtn && sidebar.classList.contains('is-open')) {
      setOpen(false);
    }
  });
})();

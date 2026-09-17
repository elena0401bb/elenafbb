(() => {
  'use strict';
  const desk = document.querySelector('[data-archive-desk]');
  const sheets = document.getElementById('archive-sheets');
  const toggles = [...document.querySelectorAll('[data-archive-toggle]')];
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');

  if (desk && sheets && toggles.length) {
    let isOpen = false;
    let lastToggle = toggles[0];
    const setOpen = (next, returnFocus = false) => {
      isOpen = next;
      desk.dataset.open = String(next);
      sheets.inert = !next;
      for (const button of toggles) {
        button.setAttribute('aria-expanded', String(next));
        const label = button.querySelector('[data-toggle-label]');
        if (label) label.textContent = next ? button.dataset.closeLabel : button.dataset.openLabel;
      }
      const hint = desk.querySelector('[data-archive-hint]');
      if (hint) hint.textContent = next ? '选择一份作品，打开完整案例' : '打开文件夹，查看三个 IP 案例';
      if (returnFocus) lastToggle.focus({preventScroll: true});
    };
    for (const button of toggles) {
      button.addEventListener('click', event => {
        if (button.tagName === 'A' && (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)) return;
        event.preventDefault();
        lastToggle = button;
        setOpen(!isOpen);
      });
    }
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !isOpen || event.defaultPrevented || document.querySelector('dialog[open]')) return;
      if (!desk.contains(document.activeElement) && !toggles.includes(document.activeElement)) return;
      event.preventDefault();
      setOpen(false, true);
    });
    desk.classList.add('archive-ready');
    setOpen(false);
  }

  // Enhance only after observers are available; the HTML remains visible without JS.
  const revealTargets = [...document.querySelectorAll('.account-summary-row, #cases .project-folder, .approach-list > li, #account-work > article, .support-links > article, .about > *')];
  let revealObserver;
  const showEverything = () => {
    revealObserver?.disconnect();
    for (const target of revealTargets) {
      target.classList.remove('reveal-pending');
      target.classList.add('is-visible');
    }
  };
  if ('IntersectionObserver' in window && !motion.matches) {
    revealObserver = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.remove('reveal-pending');
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    }, {threshold: 0, rootMargin: '0px 0px -36px 0px'});
    for (const target of revealTargets) {
      target.dataset.reveal = '';
      if (target.getBoundingClientRect().top < window.innerHeight) {
        target.classList.add('is-visible');
      } else {
        target.classList.add('reveal-pending');
        revealObserver.observe(target);
      }
      target.addEventListener('focusin', () => {
        target.classList.remove('reveal-pending');
        target.classList.add('is-visible');
        revealObserver.unobserve(target);
      });
    }
  }
  motion.addEventListener?.('change', event => { if (event.matches) showEverything(); });
  window.addEventListener('beforeprint', showEverything);

  const progress = document.querySelector('.reading-progress span');
  const navLinks = [...document.querySelectorAll('.nav-links a[href^="#"]')];
  const sections = navLinks.map(link => ({link, section: document.getElementById(link.hash.slice(1))})).filter(item => item.section);
  let scheduled = false;
  const updateReading = () => {
    scheduled = false;
    const distance = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.transform = `scaleX(${distance > 0 ? Math.min(1, Math.max(0, window.scrollY / distance)) : 0})`;
    let current = null;
    for (const item of sections) {
      if (item.section.getBoundingClientRect().top <= 160) current = item;
    }
    for (const item of sections) {
      if (item === current) item.link.setAttribute('aria-current', 'location');
      else item.link.removeAttribute('aria-current');
    }
  };
  const requestReadingUpdate = () => {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(updateReading);
  };
  window.addEventListener('scroll', requestReadingUpdate, {passive: true});
  window.addEventListener('resize', requestReadingUpdate, {passive: true});
  window.addEventListener('load', requestReadingUpdate, {once: true});
  updateReading();
})();

(() => {
  document.querySelectorAll('[data-guoer-gallery]').forEach(gallery => {
    const strip = gallery.querySelector('.guoer-strip');
    const actions = gallery.querySelector('.guoer-gallery-actions');
    const previous = gallery.querySelector('[data-gallery-previous]');
    const next = gallery.querySelector('[data-gallery-next]');
    if (!strip || !actions || !previous || !next) return;

    const update = () => {
      const end = Math.max(0, strip.scrollWidth - strip.clientWidth);
      actions.hidden = end <= 2;
      previous.disabled = strip.scrollLeft <= 2;
      next.disabled = strip.scrollLeft >= end - 2;
    };
    const move = direction => {
      const first = strip.firstElementChild;
      const gap = parseFloat(getComputedStyle(strip).columnGap) || 0;
      const step = first ? first.getBoundingClientRect().width + gap : strip.clientWidth;
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      strip.scrollBy({left: direction * step, behavior: reduced ? 'auto' : 'smooth'});
    };
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    strip.addEventListener('scroll', update, {passive: true});
    if (typeof ResizeObserver === 'function') new ResizeObserver(update).observe(strip);
    else window.addEventListener('resize', update, {passive: true});
    update();
  });
})();

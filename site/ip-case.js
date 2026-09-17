(() => {
  const dialog = document.getElementById('image-viewer');
  const preview = document.getElementById('image-viewer-image');
  const title = document.getElementById('image-viewer-title');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  let opener = null;
  document.addEventListener('click', event => {
    const trigger = event.target.closest('a[data-lightbox]');
    if (!trigger || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    opener = trigger;
    const caption = trigger.dataset.caption || '作品原图';
    title.textContent = caption;
    preview.alt = caption;
    preview.src = trigger.getAttribute('href');
    dialog.showModal();
  });
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    preview.removeAttribute('src');
    if (opener && opener.isConnected) opener.focus({preventScroll:true});
  });
})();

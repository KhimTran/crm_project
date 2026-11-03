(() => {
  const form = document.getElementById('survey-bulk-send');
  if (!form) return;
  const button = document.getElementById('survey-send');
  const all = document.getElementById('survey-select-all');
  const rows = Array.from(document.querySelectorAll('[data-survey-select]:not(:disabled)'));
  let submitting = false;
  const update = () => {
    const count = rows.filter(row => row.checked).length;
    button.disabled = count === 0;
    if (all) {
      all.disabled = rows.length === 0;
      all.checked = rows.length > 0 && count === rows.length;
      all.indeterminate = count > 0 && count < rows.length;
    }
  };
  rows.forEach(row => row.addEventListener('change', update));
  if (all) all.addEventListener('change', () => {
    rows.forEach(row => { row.checked = all.checked; });
    update();
  });
  // Capture runs before the portal's submit guard disables the button.
  form.addEventListener('submit', event => {
    const count = rows.filter(row => row.checked).length;
    if (!count || submitting || form.dataset.portalSubmitting === 'true' ||
        !window.confirm(`Send ${count} selected survey(s)? Only eligible customers in each saved audience who have never received that survey will be invited.`)) {
      event.preventDefault();
      return;
    }
    submitting = true;
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
  }, true);
  window.addEventListener('pageshow', () => {
    submitting = false;
    delete form.dataset.portalSubmitting;
    form.removeAttribute('aria-busy');
    update();
  });
  update();
})();

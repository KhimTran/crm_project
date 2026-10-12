// Progressive enhancement for customer controls. Filters still work without JS.
(() => {
  const disclosure = document.querySelector('.customer-layout .filter-disclosure');
  if (disclosure) {
    const desktop = window.matchMedia('(min-width: 992px)');
    const syncFilter = () => { disclosure.open = desktop.matches || !!disclosure.querySelector('.errorlist'); };
    syncFilter();
    desktop.addEventListener('change', syncFilter);
  }
  const account = document.querySelector('.customer-layout .account-menu');
  if (account) {
    document.addEventListener('click', (event) => {
      if (!account.contains(event.target)) account.open = false;
    });
    account.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        account.open = false;
        account.querySelector('summary').focus();
      }
    });
  }
})();

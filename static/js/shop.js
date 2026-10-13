// Native disclosures and GET forms remain usable without JavaScript.
(() => {
  const disclosure = document.querySelector('.customer-layout .filter-disclosure');
  if (disclosure) {
    const desktop = window.matchMedia('(min-width: 992px)');
    const syncFilter = () => { disclosure.open = desktop.matches || !!disclosure.querySelector('.errorlist'); };
    syncFilter();
    desktop.addEventListener('change', syncFilter);
  }
  const menus = document.querySelectorAll('.customer-layout .account-menu, .customer-layout .category-menu');
  menus.forEach((menu) => {
    document.addEventListener('click', (event) => {
      if (!menu.contains(event.target)) menu.open = false;
    });
    menu.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        menu.open = false;
        menu.querySelector('summary').focus();
      }
    });
  });
})();

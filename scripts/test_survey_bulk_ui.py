"""Exercise the rendered survey selection form in headless Edge, without database access."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")
import django

django.setup()
from django.template.loader import render_to_string
from django.test import RequestFactory
from apps.surveys.forms import SurveyListFilterForm

EDGE = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
PROBE = r"""<script>
window.addEventListener('load', () => {
  const checks = [];
  const assert = (condition, message) => { if (!condition) throw Error(message); checks.push(message); };
  try {
    const form = document.getElementById('survey-bulk-send');
    const button = document.getElementById('survey-send');
    const all = document.getElementById('survey-select-all');
    const rows = [...document.querySelectorAll('[data-survey-select]')];
    const changed = row => row.dispatchEvent(new Event('change', {bubbles:true}));
    let prompts = 0, accepted = false;
    window.confirm = message => { prompts++; return accepted; };
    const submit = () => {
      const event = new SubmitEvent('submit', {cancelable:true, bubbles:true, submitter:button});
      form.dispatchEvent(event);
      return event;
    };
    assert(button.disabled && !all.checked, 'initially disabled');
    assert(submit().defaultPrevented && prompts === 0, 'empty selection cannot prompt/send');
    rows[0].checked = true; changed(rows[0]);
    rows[0].focus();
    const checkboxStyle = getComputedStyle(rows[0]);
    assert(checkboxStyle.width === checkboxStyle.height && checkboxStyle.boxShadow === 'none',
           'focused checkbox remains square without text-input rectangle');
    assert(!button.disabled && all.indeterminate, 'single selection enables send and mixed header');
    assert(new FormData(form).getAll('survey_ids').join(',') === '1', 'row belongs to external POST form');
    all.checked = true; changed(all);
    assert(rows[0].checked && rows[1].checked && !rows[2].checked && rows[2].disabled, 'select all excludes invalid rows');
    assert(new FormData(form).getAll('survey_ids').join(',') === '1,2', 'POST contains only selected eligible IDs');
    assert(submit().defaultPrevented && prompts === 1 && !button.disabled && !form.dataset.portalSubmitting,
           'cancel preserves selection without pending state');
    accepted = true;
    const confirmed = submit();
    assert(!confirmed.defaultPrevented && prompts === 2 && button.disabled && form.getAttribute('aria-busy') === 'true',
           'confirm proceeds directly and disables send');
    assert(submit().defaultPrevented && prompts === 2, 'repeat submit blocked without another prompt');
    window.dispatchEvent(new Event('pageshow'));
    assert(!button.disabled && !form.dataset.portalSubmitting, 'back navigation restores usable form');
    all.checked = false; changed(all);
    assert(button.disabled && rows.every(row => !row.checked), 'deselect all disables send');
    const result = document.createElement('pre'); result.id = 'bulk-ui-result';
    result.textContent = JSON.stringify({checks}); document.body.append(result);
  } catch (error) {
    const result = document.createElement('pre'); result.id = 'bulk-ui-result';
    result.textContent = JSON.stringify({error: error.message}); document.body.append(result);
  }
});
</script>"""


def main():
    request = RequestFactory().get("/surveys/manage/")
    items = [SimpleNamespace(survey_id=index, title=f"Survey {index}", status=status,
                             sendable=status == "ACTIVE", editable=False)
             for index, status in [(1, "ACTIVE"), (2, "ACTIVE"), (3, "CLOSED")]]
    with tempfile.TemporaryDirectory(prefix="survey_bulk_ui_") as directory:
        root = Path(directory)
        for layout in ("manager/base.html", "admin/portal/base.html", "layouts/base_crm.html"):
            html = render_to_string("surveys/manage_list.html", {
                "crm_layout": layout, "items": items, "filters": SurveyListFilterForm({}),
                "request": request, "csrf_token": "test-token"})
            # Keep the real local scripts; no network/server is needed for these checks.
            html = re.sub(r'<script[^>]+src="https?://[^\"]+"[^>]*></script>', "", html)
            html = html.replace('src="/static/', f'src="{(ROOT / "static").as_uri()}/')
            html = html.replace('href="/static/', f'href="{(ROOT / "static").as_uri()}/')
            page = root / "page.html"
            page.write_text(html.replace("</body>", PROBE + "</body>"), encoding="utf-8")
            result = subprocess.run([str(EDGE), "--headless", "--disable-gpu", "--no-first-run",
                                     f"--user-data-dir={root / 'browser'}", "--allow-file-access-from-files",
                                     "--virtual-time-budget=1500", "--dump-dom", page.as_uri()],
                                    capture_output=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            match = re.search(r'<pre id="bulk-ui-result">(.*?)</pre>', result.stdout.decode("utf-8", errors="replace"))
            assert match, "Browser did not return the selection test result"
            data = json.loads(match[1])
            assert "error" not in data, data
            print(f"{layout}: {len(data['checks'])} browser checks PASS")


if __name__ == "__main__":
    main()

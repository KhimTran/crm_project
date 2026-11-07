# Final hardening regression — 2026-11-07

516 PASS / 0 FAIL / 0 ERROR / 0 SKIP. Prior refactor: 509 PASS. Original baseline: 504 PASS.

| Module | Tests | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| accounts | 161 | 161 | 0 | 0 | 0 |
| admin_portal | 43 | 43 | 0 | 0 | 0 |
| catalog | 17 | 17 | 0 | 0 | 0 |
| customers | 105 | 105 | 0 | 0 | 0 |
| feedback | 24 | 24 | 0 | 0 | 0 |
| shop | 13 | 13 | 0 | 0 | 0 |
| surveys | 153 | 153 | 0 | 0 | 0 |

Full MySQL run: hardening/verified/. First hardening run: 515 PASS + 1 midnight-fixture ERROR, preserved under hardening/regression/; frozen baseline reproduction and fixed full-flow probe pass. Seven new tests retain all509 existing tests. HTTP15/15; actual Edge26 portal +8 Survey/Feedback cases;8 viewport checks. See [hardening report](hardening/REPORT.md).

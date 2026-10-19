// tv4: trình soạn khảo sát cho trang Tạo/Sửa khảo sát.
// State câu hỏi nằm ở client, gửi lên server dạng JSON (questions_json); server kiểm tra lại toàn bộ.
(function () {
    "use strict";
    var form = document.getElementById("sv-cb-form");
    if (!form) { return; }
    var cfg = JSON.parse(document.getElementById("sv-cb-config").textContent);
    var L = cfg.labels;
    var list = document.getElementById("sv-cb-list");
    var preview = document.getElementById("sv-cb-preview");
    var jsonInput = document.getElementById("sv-cb-json");
    var actionInput = document.getElementById("sv-cb-action");
    var alertBox = document.getElementById("sv-cb-alert");
    var addButton = document.getElementById("sv-cb-add");
    var dialog = document.getElementById("sv-cb-publish");
    var editable = cfg.mode === "create" || cfg.mode === "edit";  // được thêm/xóa/đổi loại/đổi thứ tự câu hỏi
    var content = editable || cfg.mode === "fixed";  // bộ 8 câu: chỉ sửa nội dung, phương án, bắt buộc
    var OPTION_TYPES = { SINGLE_CHOICE: true, MULTI_CHOICE: true, MATRIX: true };
    var CHOICE_TYPES = { SINGLE_CHOICE: true, MULTI_CHOICE: true };
    var ICONS = {
        handle: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/><circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/></svg>',
        chevron: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>',
        pencil: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/></svg>',
        trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>'
    };
    var questions = [];
    var openUid = null;
    var nextUid = 1;
    var dirty = false;
    var submitting = false;

    // ───────── tiện ích ─────────
    function el(tag, attrs, children) {
        var node = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (key) {
            var value = attrs[key];
            if (value === null || value === undefined || value === false) { return; }
            if (key === "text") { node.textContent = value; }
            else if (key === "html") { node.innerHTML = value; }  // chỉ dùng cho icon tĩnh ở trên
            else if (key === "class") { node.className = value; }
            else if (key.indexOf("on") === 0) { node.addEventListener(key.slice(2), value); }
            else { node.setAttribute(key, value === true ? "" : value); }
        });
        (children || []).forEach(function (child) {
            if (child === null || child === undefined || child === false) { return; }
            node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
        });
        return node;
    }
    function fmt(text, n) { return String(text).replace("{n}", n); }
    function toInt(value, fallback) {
        var n = parseInt(value, 10);
        return isNaN(n) ? fallback : n;
    }
    function typeInfo(value) {
        for (var i = 0; i < cfg.types.length; i++) { if (cfg.types[i].value === value) { return cfg.types[i]; } }
        return { value: value, label: value, badge: value };
    }
    function badgeText(q) {
        var info = typeInfo(q.type);
        return q.type === "RATING" ? info.badge + " " + q.rating_min + "-" + q.rating_max : info.badge;
    }
    function indexOfUid(uid) {
        for (var i = 0; i < questions.length; i++) { if (questions[i].uid === uid) { return i; } }
        return -1;
    }
    function normalize(item) {
        return {
            uid: nextUid++,
            text: item.text || "", type: item.type || "SINGLE_CHOICE", required: item.required !== false,
            options: Array.isArray(item.options) ? item.options.map(function (o) { return String(o); }) : [],
            other: !!item.other, other_label: item.other_label || "",
            max_selections: item.max_selections ? toInt(item.max_selections, null) : null,
            rating_min: toInt(item.rating_min, 1), rating_max: toInt(item.rating_max, 5),
            rating_min_label: item.rating_min_label || "", rating_max_label: item.rating_max_label || "",
            placeholder: item.placeholder || "", section: item.section || "", key: item.key || "", errors: {}
        };
    }
    function blankQuestion() {
        return normalize({ type: "SINGLE_CHOICE", required: true, options: ["", ""] });
    }
    function serialize() {
        return JSON.stringify(questions.map(function (q) {
            return {
                text: q.text, type: q.type, required: q.required, options: OPTION_TYPES[q.type] ? q.options : [],
                other: CHOICE_TYPES[q.type] && q.other, other_label: q.other ? (q.other_label || L.otherDefault) : "",
                max_selections: q.type === "MULTI_CHOICE" ? q.max_selections : null,
                rating_min: q.rating_min, rating_max: q.rating_max,
                rating_min_label: q.rating_min_label, rating_max_label: q.rating_max_label,
                placeholder: q.placeholder, section: q.section
            };
        }));
    }
    function markDirty() { dirty = true; }
    function sync() { jsonInput.value = serialize(); renderPreview(); }

    // ───────── danh sách câu hỏi (accordion) ─────────
    function render(focusSelector) {
        list.textContent = "";
        if (!questions.length) {
            list.appendChild(el("p", { "class": "sv-cb-empty", text: L.emptyList }));
        }
        questions.forEach(function (q, i) { list.appendChild(renderItem(q, i)); });
        if (addButton) { addButton.disabled = questions.length >= cfg.maxQuestions; }
        sync();
        if (focusSelector) {
            var target = list.querySelector(focusSelector);
            if (target) { target.focus(); }
        }
    }

    function renderItem(q, i) {
        var open = q.uid === openUid;
        var hasErrors = Object.keys(q.errors).length > 0;
        var card = el("article", { "class": "sv-cb-q" + (open ? " is-open" : "") + (hasErrors ? " has-error" : ""),
                                   "data-uid": q.uid });
        var head = el("div", { "class": "sv-cb-q-head" });
        if (editable) {
            var handle = el("button", { type: "button", "class": "sv-cb-handle", "aria-label": L.drag + " – " + (i + 1),
                                        title: L.drag, html: ICONS.handle });
            handle.addEventListener("pointerdown", function (event) { startDrag(event, card); });
            handle.addEventListener("keydown", function (event) {
                if (event.key === "ArrowUp" || event.key === "ArrowDown") {
                    event.preventDefault();
                    moveQuestion(indexOfUid(q.uid), event.key === "ArrowUp" ? -1 : 1);
                }
            });
            head.appendChild(handle);
        }
        var toggle = el("button", { type: "button", "class": "sv-cb-q-toggle", "aria-expanded": open ? "true" : "false",
                                    "aria-controls": "sv-cb-q-body-" + q.uid, title: L.toggle,
                                    onclick: function () { openUid = open ? null : q.uid; render(); } }, [
            el("span", { "class": "sv-cb-q-num", text: (i + 1) + "." }),
            el("span", { "class": "sv-cb-q-title", text: q.text || L.untitled }),
            el("span", { "class": "sv-cb-q-badges" }, [
                el("span", { "class": "sv-cb-badge sv-cb-badge-" + q.type.toLowerCase(), text: badgeText(q) }),
                q.required ? el("span", { "class": "sv-cb-badge sv-cb-badge-req", text: L.requiredBadge }) : null
            ]),
            el("span", { "class": "sv-cb-chevron", html: ICONS.chevron })
        ]);
        head.appendChild(toggle);
        card.appendChild(head);
        if (open) { card.appendChild(renderBody(q)); }
        return card;
    }

    function fieldErrors(q, name) {
        var messages = q.errors[name] || [];
        return el("div", { "class": "sv-cb-err", id: "sv-cb-err-" + q.uid + "-" + name },
                  messages.map(function (m) { return el("p", { text: m }); }));
    }
    function describedBy(q, name) { return q.errors[name] ? "sv-cb-err-" + q.uid + "-" + name : null; }

    function renderBody(q) {
        var lock = !content;
        var shape = lock || !editable;  // khóa cấu trúc (loại câu, số phương án, thang điểm, giới hạn)
        var body = el("div", { "class": "sv-cb-q-body", id: "sv-cb-q-body-" + q.uid });
        // Nội dung câu hỏi
        var textInput = el("input", { type: "text", id: "sv-cb-text-" + q.uid, "class": "sv-cb-input", placeholder: L.textHint,
                                      disabled: lock, "aria-invalid": q.errors.text ? "true" : null,
                                      "aria-describedby": describedBy(q, "text"), "data-focus": "text" });
        textInput.value = q.text;
        textInput.addEventListener("input", function () {
            q.text = textInput.value;
            clearError(q, "text");
            var title = list.querySelector('[data-uid="' + q.uid + '"] .sv-cb-q-title');
            if (title) { title.textContent = q.text || L.untitled; }
            markDirty(); sync();
        });
        body.appendChild(el("div", { "class": "sv-cb-field" }, [
            el("label", { "for": textInput.id }, [L.text + " ", el("span", { "class": "sv-cb-req", "aria-hidden": "true", text: "*" })]),
            textInput, fieldErrors(q, "text")
        ]));
        // Loại câu hỏi
        var select = el("select", { id: "sv-cb-type-" + q.uid, "class": "sv-cb-input", disabled: shape });
        cfg.types.forEach(function (t) {
            var option = el("option", { value: t.value, text: t.label });
            if (t.value === q.type) { option.selected = true; }
            select.appendChild(option);
        });
        select.addEventListener("change", function () { changeType(q, select); });
        body.appendChild(el("div", { "class": "sv-cb-field sv-cb-type" }, [
            el("label", { "for": select.id, text: L.type }), select, fieldErrors(q, "type")
        ]));
        if (OPTION_TYPES[q.type]) { body.appendChild(renderOptions(q, lock, shape)); }
        if (q.type === "MULTI_CHOICE" && q.max_selections !== null) { body.appendChild(renderLimit(q, shape)); }
        if (q.type === "RATING") { body.appendChild(renderRating(q, shape)); }
        if (q.type === "TEXT") {
            var hint = el("input", { type: "text", id: "sv-cb-ph-" + q.uid, "class": "sv-cb-input", maxlength: "255",
                                     placeholder: L.placeholderHint, disabled: lock });
            hint.value = q.placeholder;
            hint.addEventListener("input", function () { q.placeholder = hint.value; markDirty(); sync(); });
            body.appendChild(el("div", { "class": "sv-cb-field" }, [
                el("label", { "for": hint.id, text: L.placeholder }), hint, fieldErrors(q, "placeholder")
            ]));
        }
        body.appendChild(renderFooter(q, lock, shape));
        return body;
    }

    function renderOptions(q, lock, shape) {
        var wrap = el("div", { "class": "sv-cb-field sv-cb-options", role: "group",
                               "aria-labelledby": "sv-cb-opt-label-" + q.uid });
        wrap.appendChild(el("span", { "class": "sv-cb-label", id: "sv-cb-opt-label-" + q.uid,
                                      text: q.type === "MATRIX" ? L.criteria : L.options }));
        var marker = q.type === "MULTI_CHOICE" ? "sv-cb-mark is-check" : q.type === "MATRIX" ? "sv-cb-mark is-dash" : "sv-cb-mark";
        q.options.forEach(function (text, k) {
            var input = el("input", { type: "text", "class": "sv-cb-input", maxlength: "255", disabled: lock,
                                      placeholder: L.optionHint, "aria-label": L.option + " " + (k + 1),
                                      "data-focus": "opt-" + k });
            input.value = text;
            input.addEventListener("input", function () { q.options[k] = input.value; clearError(q, "options"); markDirty(); sync(); });
            input.addEventListener("keydown", function (event) {
                if (event.key === "Enter") {  // Enter: thêm phương án mới ngay dưới
                    event.preventDefault();
                    if (shape) { return; }
                    q.options.splice(k + 1, 0, "");
                    markDirty(); render('[data-uid="' + q.uid + '"] [data-focus="opt-' + (k + 1) + '"]');
                }
            });
            wrap.appendChild(el("div", { "class": "sv-cb-opt" }, [
                el("span", { "class": marker, "aria-hidden": "true" }), input,
                lock ? null : el("button", { type: "button", "class": "sv-cb-icon", "aria-label": L.editOption + " " + (k + 1),
                                             title: L.editOption, html: ICONS.pencil,
                                             onclick: function () { input.focus(); input.select(); } }),
                shape ? null : el("button", { type: "button", "class": "sv-cb-icon is-danger", "aria-label": L.deleteOption + " " + (k + 1),
                                             title: L.deleteOption, html: ICONS.trash,
                                             onclick: function () {
                                                 q.options.splice(k, 1);
                                                 if (q.max_selections !== null && q.max_selections > optionCount(q)) {
                                                     q.max_selections = Math.max(1, optionCount(q));
                                                 }
                                                 markDirty(); render();
                                             } })
            ]));
        });
        if (CHOICE_TYPES[q.type] && q.other) {
            var otherInput = el("input", { type: "text", "class": "sv-cb-input", maxlength: "255", disabled: lock,
                                           "aria-label": L.otherLabel });
            otherInput.value = q.other_label || L.otherDefault;
            otherInput.addEventListener("input", function () { q.other_label = otherInput.value; clearError(q, "options"); markDirty(); sync(); });
            wrap.appendChild(el("div", { "class": "sv-cb-opt is-other" }, [
                el("span", { "class": marker, "aria-hidden": "true" }), otherInput,
                el("span", { "class": "sv-cb-other-note", text: "+ " + L.otherInput }),
                shape ? null : el("button", { type: "button", "class": "sv-cb-icon is-danger", "aria-label": L.deleteOption + " " + L.otherLabel,
                                             title: L.deleteOption, html: ICONS.trash,
                                             onclick: function () { q.other = false; markDirty(); render(); } })
            ]));
        }
        if (!shape) {
            wrap.appendChild(el("button", { type: "button", "class": "sv-cb-link", text: "+ " + L.addOption,
                onclick: function () {
                    q.options.push("");
                    markDirty(); render('[data-uid="' + q.uid + '"] [data-focus="opt-' + (q.options.length - 1) + '"]');
                } }));
        }
        wrap.appendChild(fieldErrors(q, "options"));
        return wrap;
    }

    function optionCount(q) { return q.options.length + (CHOICE_TYPES[q.type] && q.other ? 1 : 0); }

    function renderLimit(q, lock) {
        var input = el("input", { type: "number", id: "sv-cb-max-" + q.uid, "class": "sv-cb-input sv-cb-num", min: "1",
                                  max: String(Math.max(1, optionCount(q))), disabled: lock,
                                  "aria-invalid": q.errors.max_selections ? "true" : null,
                                  "aria-describedby": describedBy(q, "max_selections") });
        input.value = q.max_selections;
        input.addEventListener("input", function () {
            q.max_selections = toInt(input.value, 0);
            clearError(q, "max_selections"); markDirty(); sync();
        });
        return el("div", { "class": "sv-cb-field sv-cb-inline" }, [
            el("label", { "for": input.id, text: L.limitLabel }), input, fieldErrors(q, "max_selections")
        ]);
    }

    function renderRating(q, lock) {
        function numberField(key, label) {
            var input = el("input", { type: "number", id: "sv-cb-" + key + "-" + q.uid, "class": "sv-cb-input sv-cb-num",
                                      min: "1", max: "10", disabled: lock, "aria-invalid": q.errors.rating ? "true" : null });
            input.value = q[key];
            input.addEventListener("input", function () {
                q[key] = toInt(input.value, 0);
                clearError(q, "rating");
                var badge = list.querySelector('[data-uid="' + q.uid + '"] .sv-cb-badge');
                if (badge) { badge.textContent = badgeText(q); }
                markDirty(); sync();
            });
            return el("div", { "class": "sv-cb-field" }, [el("label", { "for": input.id, text: label }), input]);
        }
        function labelField(key, label, hint) {
            var input = el("input", { type: "text", id: "sv-cb-" + key + "-" + q.uid, "class": "sv-cb-input",
                                      maxlength: "60", placeholder: hint, disabled: lock });
            input.value = q[key];
            input.addEventListener("input", function () { q[key] = input.value; markDirty(); sync(); });
            return el("div", { "class": "sv-cb-field" }, [el("label", { "for": input.id, text: label }), input]);
        }
        return el("div", { "class": "sv-cb-rating-config" }, [
            el("div", { "class": "sv-cb-grid-4" }, [
                numberField("rating_min", L.ratingMin), numberField("rating_max", L.ratingMax),
                labelField("rating_min_label", L.ratingMinLabel, L.ratingMinHint),
                labelField("rating_max_label", L.ratingMaxLabel, L.ratingMaxHint)
            ]),
            fieldErrors(q, "rating")
        ]);
    }

    function renderFooter(q, lock, shape) {
        // câu góp ý của bộ 8 câu luôn không bắt buộc
        var switchInput = el("input", { type: "checkbox", role: "switch", id: "sv-cb-req-" + q.uid,
                                        disabled: lock || q.key === "suggestions" });
        switchInput.checked = q.required;
        switchInput.addEventListener("change", function () { q.required = switchInput.checked; markDirty(); render(); });
        var footer = el("div", { "class": "sv-cb-q-foot" }, [
            el("label", { "class": "sv-cb-switch", "for": switchInput.id }, [switchInput, el("span", { "class": "sv-cb-switch-ui", "aria-hidden": "true" }), L.required])
        ]);
        if (shape) { return footer; }
        var menu = el("details", { "class": "sv-cb-menu" });
        menu.appendChild(el("summary", {}, [L.advanced + " ", el("span", { "class": "sv-cb-chevron", html: ICONS.chevron })]));
        var items = el("div", { "class": "sv-cb-menu-list" });
        function item(label, pressed, handler, danger) {
            items.appendChild(el("button", { type: "button", "class": "sv-cb-menu-item" + (danger ? " is-danger" : ""),
                                             "aria-pressed": pressed === null ? null : String(pressed),
                                             onclick: function () { menu.open = false; handler(); } },
                                 [pressed === null ? null : el("span", { "class": "sv-cb-tick", "aria-hidden": "true", text: pressed ? "✓" : "" }), label]));
        }
        if (q.type === "MULTI_CHOICE") {
            item(L.limit, q.max_selections !== null, function () {
                q.max_selections = q.max_selections === null ? Math.max(1, Math.min(2, optionCount(q))) : null;
                clearError(q, "max_selections"); markDirty(); render('[data-uid="' + q.uid + '"] .sv-cb-num');
            });
        }
        if (CHOICE_TYPES[q.type]) {
            item(L.other, q.other, function () {
                q.other = !q.other;
                if (q.other && !q.other_label) { q.other_label = L.otherDefault; }
                markDirty(); render();
            });
        }
        item(L.duplicate, null, function () {
            var copy = normalize(JSON.parse(JSON.stringify(q)));
            copy.errors = {};
            questions.splice(indexOfUid(q.uid) + 1, 0, copy);
            openUid = copy.uid;
            markDirty(); render('[data-uid="' + copy.uid + '"] [data-focus="text"]');
        });
        item(L.remove, null, function () {
            if (!window.confirm(L.confirmRemove)) { return; }
            questions.splice(indexOfUid(q.uid), 1);
            openUid = null;
            markDirty(); render();
        }, true);
        menu.appendChild(items);
        footer.appendChild(menu);
        return footer;
    }

    function changeType(q, select) {
        var next = select.value;
        var hasText = q.options.some(function (o) { return o.trim(); }) || q.other;
        if (OPTION_TYPES[q.type] && !OPTION_TYPES[next] && hasText && !window.confirm(L.confirmType)) {
            select.value = q.type;
            return;
        }
        q.type = next;
        if (!OPTION_TYPES[next]) { q.options = []; q.other = false; }
        while (OPTION_TYPES[next] && q.options.length < 2) { q.options.push(""); }
        if (!CHOICE_TYPES[next]) { q.other = false; }
        if (next !== "MULTI_CHOICE") { q.max_selections = null; }
        q.errors = {};
        markDirty(); render('[data-uid="' + q.uid + '"] .sv-cb-type select');
    }

    function clearError(q, name) {
        if (!q.errors[name]) { return; }
        delete q.errors[name];
        var box = document.getElementById("sv-cb-err-" + q.uid + "-" + name);
        if (box) { box.textContent = ""; }
        var card = list.querySelector('[data-uid="' + q.uid + '"]');
        if (card && !Object.keys(q.errors).length) { card.classList.remove("has-error"); }
    }

    function addQuestion() {
        if (questions.length >= cfg.maxQuestions) { return; }
        var q = blankQuestion();
        questions.push(q);
        openUid = q.uid;
        render('[data-uid="' + q.uid + '"] [data-focus="text"]');
        var card = list.querySelector('[data-uid="' + q.uid + '"]');
        if (card) { card.scrollIntoView({ behavior: "smooth", block: "center" }); }
    }

    function moveQuestion(index, delta) {
        var target = index + delta;
        if (index < 0 || target < 0 || target >= questions.length) { return; }
        var moved = questions.splice(index, 1)[0];
        questions.splice(target, 0, moved);
        markDirty(); render('[data-uid="' + moved.uid + '"] .sv-cb-handle');
    }

    // ───────── kéo thả bằng pointer (chuột + cảm ứng), không cần thư viện ─────────
    function renumber() {
        list.querySelectorAll(".sv-cb-q").forEach(function (card, i) {
            var num = card.querySelector(".sv-cb-q-num");
            if (num) { num.textContent = (i + 1) + "."; }
        });
    }
    function startDrag(event, card) {
        if (event.button !== undefined && event.button !== 0) { return; }
        event.preventDefault();
        var handle = event.currentTarget;
        var before = questions.map(function (q) { return q.uid; }).join(",");
        handle.setPointerCapture(event.pointerId);
        card.classList.add("is-dragging");
        list.classList.add("is-sorting");
        function onMove(e) {
            var y = e.clientY;
            if (y < 70) { window.scrollBy(0, -14); } else if (y > window.innerHeight - 70) { window.scrollBy(0, 14); }
            var cards = Array.prototype.slice.call(list.querySelectorAll(".sv-cb-q")).filter(function (c) { return c !== card; });
            var after = null;
            for (var i = 0; i < cards.length; i++) {
                var box = cards[i].getBoundingClientRect();
                if (y < box.top + box.height / 2) { after = cards[i]; break; }
            }
            if (after !== card.nextElementSibling || (after === null && list.lastElementChild !== card)) {
                list.insertBefore(card, after);
                renumber();
            }
        }
        function onEnd() {
            handle.removeEventListener("pointermove", onMove);
            handle.removeEventListener("pointerup", onEnd);
            handle.removeEventListener("pointercancel", onEnd);
            card.classList.remove("is-dragging");
            list.classList.remove("is-sorting");
            var order = Array.prototype.map.call(list.querySelectorAll(".sv-cb-q"), function (c) { return Number(c.getAttribute("data-uid")); });
            questions.sort(function (a, b) { return order.indexOf(a.uid) - order.indexOf(b.uid); });
            if (order.join(",") !== before) { markDirty(); }
            render('[data-uid="' + card.getAttribute("data-uid") + '"] .sv-cb-handle');
        }
        handle.addEventListener("pointermove", onMove);
        handle.addEventListener("pointerup", onEnd);
        handle.addEventListener("pointercancel", onEnd);
    }

    // ───────── xem trước (giống trang khách hàng làm khảo sát) ─────────
    function renderPreview() {
        preview.textContent = "";
        var title = form.querySelector('[name="title"]').value.trim();
        var description = form.querySelector('[name="description"]').value.trim();
        preview.appendChild(el("h3", { "class": "sv-cb-pv-title", text: title || L.untitledSurvey }));
        if (description) { preview.appendChild(el("p", { "class": "sv-cb-pv-desc", text: description })); }
        questions.forEach(function (q, i) {
            var name = "sv-cb-pv-" + q.uid;
            var block = el("fieldset", { "class": "sv-cb-pv-q" }, [
                el("legend", {}, [(i + 1) + ". " + (q.text || L.untitled), q.required ? el("span", { "class": "sv-cb-req", text: " *" }) : null])
            ]);
            // form="…" trỏ tới form không tồn tại để ô xem trước không bị gửi kèm form thật
            if (CHOICE_TYPES[q.type]) {
                var labels = q.options.slice();
                if (q.other) { labels.push(q.other_label || L.otherDefault); }
                labels.forEach(function (text) {
                    block.appendChild(el("label", { "class": "sv-cb-pv-opt" }, [
                        el("input", { type: q.type === "SINGLE_CHOICE" ? "radio" : "checkbox", name: name, form: "sv-cb-preview-only" }),
                        " " + (text.trim() || "…")
                    ]));
                });
                if (q.other) {
                    block.appendChild(el("input", { type: "text", "class": "sv-cb-pv-other", form: "sv-cb-preview-only",
                                                    placeholder: L.otherInput, "aria-label": L.otherInput }));
                }
                if (q.type === "MULTI_CHOICE" && q.max_selections) {
                    block.appendChild(el("p", { "class": "sv-help", text: fmt(L.chooseMax, q.max_selections) }));
                }
            } else if (q.type === "RATING") {
                var low = Math.max(1, q.rating_min || 1), high = Math.min(10, q.rating_max || 5);
                var row = el("div", { "class": "sv-cb-pv-scale" });
                for (var n = low; n <= high; n++) {
                    row.appendChild(el("label", { "class": "sv-cb-pv-dot" }, [
                        el("input", { type: "radio", name: name, form: "sv-cb-preview-only", value: String(n) }), el("span", { text: String(n) })
                    ]));
                }
                block.appendChild(row);
                if (q.rating_min_label || q.rating_max_label) {
                    block.appendChild(el("div", { "class": "sv-cb-pv-ends" }, [
                        el("span", { text: q.rating_min_label }), el("span", { text: q.rating_max_label })
                    ]));
                }
            } else if (q.type === "MATRIX") {
                q.options.forEach(function (text) {
                    var choose = el("select", { form: "sv-cb-preview-only", "aria-label": text || "…" }, [el("option", { text: L.choose })]);
                    for (var s = 1; s <= 5; s++) { choose.appendChild(el("option", { text: String(s) })); }
                    block.appendChild(el("label", { "class": "sv-cb-pv-criterion" }, [el("span", { text: text || "…" }), choose]));
                });
                block.appendChild(el("p", { "class": "sv-help", text: L.matrixHint }));
            } else {
                block.appendChild(el("textarea", { rows: "3", form: "sv-cb-preview-only", "aria-label": q.text || L.untitled,
                                                   placeholder: q.placeholder || L.answerHint }));
            }
            preview.appendChild(block);
        });
    }

    // ───────── đối tượng nhận ─────────
    var searchBox = document.getElementById("sv-cb-customer-search");
    var noMatch = document.getElementById("sv-cb-no-match");
    var picked = document.getElementById("sv-cb-picked");
    function audienceValue() {
        var checked = form.querySelector('input[name="audience"]:checked');
        return checked ? checked.value : "";
    }
    function toggleAudience() {
        var value = audienceValue();
        document.getElementById("sv-cb-filter").hidden = value !== "filter";
        document.getElementById("sv-cb-pick").hidden = value !== "pick";
    }
    function filterCustomers() {
        var query = (searchBox.value || "").trim().toLowerCase();
        var shown = 0;
        form.querySelectorAll(".sv-cb-customer").forEach(function (row) {
            var match = !query || row.getAttribute("data-search").indexOf(query) > -1;
            row.hidden = !match;
            shown += match ? 1 : 0;
        });
        if (noMatch) { noMatch.hidden = shown > 0 || !query; noMatch.textContent = L.noMatch; }
    }
    function countPicked() {
        var n = form.querySelectorAll('input[name="customer_ids"]:checked').length;
        if (picked) { picked.textContent = fmt(L.selectedCount, n); }
    }

    // ───────── kiểm tra dữ liệu phía trình duyệt (server vẫn là chuẩn) ─────────
    function setFieldError(name, messages) {
        var box = form.querySelector('[data-err="' + name + '"]');
        if (box) {
            box.textContent = "";
            messages.forEach(function (m) { box.appendChild(el("p", { text: m })); });
        }
        var input = form.querySelector('[name="' + name + '"]');
        if (input && input.type !== "radio") { input.setAttribute("aria-invalid", messages.length ? "true" : "false"); }
    }
    function validateInfo() {
        var errors = {};
        ["title", "objective", "start_at", "end_at"].forEach(function (name) {
            var input = form.querySelector('[name="' + name + '"]');
            if (input && !input.value.trim()) { errors[name] = [L.errRequired]; }
        });
        var start = form.querySelector('[name="start_at"]').value, end = form.querySelector('[name="end_at"]').value;
        if (start && cfg.isNew && start < cfg.today) { errors.start_at = [L.errPastDate]; }
        if (start && end && end < start) { errors.end_at = [L.errEndDate]; }
        var audience = audienceValue();
        if (!audience) { errors.audience = [L.errRequired]; }
        if (audience === "filter" && !form.querySelector('#sv-cb-filter input:checked')) { errors.audience = [L.errFilter]; }
        if (audience === "pick" && !form.querySelector('input[name="customer_ids"]:checked')) { errors.audience = [L.errPick]; }
        ["title", "objective", "description", "start_at", "end_at", "audience"].forEach(function (name) {
            setFieldError(name, errors[name] || []);
        });
        return errors;
    }
    function validateQuestions() {
        var ok = true;
        questions.forEach(function (q) {
            var errors = {};
            if (!q.text.trim()) { errors.text = [L.errText]; }
            if (OPTION_TYPES[q.type]) {
                var labels = q.options.map(function (o) { return o.trim(); });
                if (CHOICE_TYPES[q.type] && q.other) { labels.push((q.other_label || L.otherDefault).trim()); }
                var problems = [];
                if (labels.some(function (o) { return !o; })) { problems.push(L.errOptionsEmpty); }
                var folded = labels.filter(Boolean).map(function (o) { return o.toLowerCase(); });
                if (folded.some(function (o, i) { return folded.indexOf(o) !== i; })) { problems.push(L.errOptionsDup); }
                if (labels.filter(Boolean).length < 2) { problems.push(L.errOptionsMin); }
                if (problems.length) { errors.options = problems; }
            }
            if (q.type === "MULTI_CHOICE" && q.max_selections !== null &&
                (!(q.max_selections >= 1) || q.max_selections > optionCount(q))) {
                errors.max_selections = [fmt(L.errLimit, optionCount(q))];
            }
            if (q.type === "RATING" && !(q.rating_min >= 1 && q.rating_max <= 10 && q.rating_min < q.rating_max)) {
                errors.rating = [L.errRating];
            }
            q.errors = errors;
            if (Object.keys(errors).length) { ok = false; }
        });
        return ok;
    }
    function showAlert(messages) {
        var ul = alertBox.querySelector("ul");
        ul.textContent = "";
        messages.forEach(function (m) { ul.appendChild(el("li", { text: m })); });
        alertBox.hidden = !messages.length;
    }
    function focusFirstProblem() {
        var firstQuestion = questions.filter(function (q) { return Object.keys(q.errors).length; })[0];
        var infoInvalid = form.querySelector('.sv-cb-info [aria-invalid="true"]');
        var audienceError = form.querySelector('[data-err="audience"] p');
        if (infoInvalid) { infoInvalid.focus(); return; }
        if (audienceError) { audienceError.parentNode.scrollIntoView({ block: "center" }); return; }
        if (firstQuestion) {
            openUid = firstQuestion.uid;
            render('[data-uid="' + firstQuestion.uid + '"] [aria-invalid="true"], [data-uid="' + firstQuestion.uid + '"] [data-focus="text"]');
            list.querySelector('[data-uid="' + firstQuestion.uid + '"]').scrollIntoView({ block: "center" });
        }
    }

    // ───────── lưu / phát hành ─────────
    var actionButtons = Array.prototype.slice.call(document.querySelectorAll("[data-action]"));
    function submitForm(action, button) {
        if (submitting) { return; }
        submitting = true;
        sync();
        actionInput.value = action;
        actionButtons.forEach(function (b) { b.disabled = true; b.setAttribute("aria-disabled", "true"); });
        var label = button && button.querySelector("span");
        if (label) { label.textContent = L.saving; }
        form.setAttribute("aria-busy", "true");
        form.submit();
    }
    function requestSubmit(action, button) {
        if (submitting) { return; }
        var infoErrors = validateInfo();
        var questionsOk = content ? validateQuestions() : true;
        var general = [];
        if (action === "publish" && editable && !questions.length) { general.push(L.errNoQuestions); }
        if (Object.keys(infoErrors).length || !questionsOk || general.length) {
            if (!questionsOk || Object.keys(infoErrors).length) { general.unshift(L.errFix); }
            showAlert(general);
            render();
            focusFirstProblem();
            return;
        }
        showAlert([]);
        if (action === "publish") { confirmPublish(button); return; }
        submitForm(action, button);
    }
    function audienceQuery() {
        var params = new URLSearchParams();
        params.append("audience", audienceValue());
        ["age_groups", "playing_levels", "preferences", "customer_ids"].forEach(function (name) {
            form.querySelectorAll('input[name="' + name + '"]:checked').forEach(function (input) { params.append(name, input.value); });
        });
        return params.toString();
    }
    function confirmPublish(button) {
        var text = document.getElementById("sv-cb-publish-text");
        var confirmButton = document.getElementById("sv-cb-publish-confirm");
        if (!dialog || typeof dialog.showModal !== "function") {
            if (window.confirm(fmt(L.countText, "?"))) { submitForm("publish", button); }
            return;
        }
        text.textContent = L.countLoading;
        confirmButton.disabled = true;
        dialog.returnValue = "";
        dialog.showModal();
        fetch(cfg.countUrl + "?" + audienceQuery(), { headers: { Accept: "application/json" }, credentials: "same-origin" })
            .then(function (response) { return response.json().then(function (data) { return { ok: response.ok, data: data }; }); })
            .then(function (result) {
                if (!result.ok) { text.textContent = (result.data.errors || [L.errCount]).join(" "); return; }
                var n = result.data.count;
                text.textContent = n > 0 ? fmt(L.countText, n) : L.countZero;
                confirmButton.disabled = !(n > 0);
            })
            .catch(function () { text.textContent = L.errCount; });
        dialog.onclose = function () {
            if (dialog.returnValue === "confirm") { submitForm("publish", button); }
        };
    }

    // ───────── khởi tạo ─────────
    try {
        var initial = JSON.parse(document.getElementById("sv-cb-items").textContent);
        if (Array.isArray(initial)) { questions = initial.map(normalize); }
    } catch (e) { questions = []; }
    Object.keys(cfg.errors || {}).forEach(function (key) {  // lỗi từng câu do server trả về
        var q = questions[Number(key)];
        if (q) { q.errors = cfg.errors[key]; }
    });
    var firstError = questions.filter(function (q) { return Object.keys(q.errors).length; })[0];
    openUid = firstError ? firstError.uid : null;
    // trang hiển thị lại sau lỗi từ server: dữ liệu đang nhập chưa được lưu
    dirty = !!firstError || !alertBox.hidden || !!form.querySelector(".sv-cb-err p");

    if (addButton) { addButton.addEventListener("click", function () { markDirty(); addQuestion(); }); }
    actionButtons.forEach(function (button) {
        button.addEventListener("click", function () { requestSubmit(button.getAttribute("data-action"), button); });
    });
    form.addEventListener("submit", function (event) { if (!submitting) { event.preventDefault(); } });
    form.addEventListener("input", function (event) {
        var target = event.target;
        if (target === searchBox || (preview.contains(target))) { return; }
        markDirty();
        if (target.name === "title" || target.name === "description") { renderPreview(); }
        if (target.name && target.closest(".sv-cb-info")) { setFieldError(target.name, []); }
    });
    form.addEventListener("change", function (event) {
        var target = event.target;
        if (preview.contains(target)) { return; }
        if (target.name === "audience") { toggleAudience(); setFieldError("audience", []); }
        if (target.name === "customer_ids") { countPicked(); setFieldError("audience", []); }
        if (target.closest && target.closest("#sv-cb-filter")) { setFieldError("audience", []); }
    });
    if (searchBox) { searchBox.addEventListener("input", filterCustomers); }
    document.addEventListener("click", function (event) {  // đóng menu "Tùy chọn nâng cao" khi bấm ra ngoài
        list.querySelectorAll(".sv-cb-menu[open]").forEach(function (menu) {
            if (!menu.contains(event.target)) { menu.open = false; }
        });
    });
    window.addEventListener("beforeunload", function (event) {
        if (dirty && !submitting) { event.preventDefault(); event.returnValue = ""; }
    });

    toggleAudience();
    countPicked();
    render();
    if (cfg.addOnLoad) {  // "Lưu và tiếp tục thêm câu hỏi": thêm sẵn một câu trống đang mở
        if (window.history.replaceState) { window.history.replaceState(null, "", window.location.pathname); }
        addQuestion();
    }
})();

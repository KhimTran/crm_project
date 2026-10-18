(() => {
    const form = document.getElementById("customer-create-form");
    if (!form) return;
    const toggle = document.getElementById("customer-password-toggle");
    const password = form.elements.namedItem("password");
    const submit = form.querySelector('button[type="submit"]');
    const submitLabel = submit.textContent;
    const errors = document.getElementById("customer-form-errors");
    const status = document.getElementById("customer-save-status");
    let saving = false;
    toggle.hidden = false;
    toggle.addEventListener("click", () => {
        const visible = password.type === "password";
        password.type = visible ? "text" : "password";
        toggle.setAttribute("aria-pressed", String(visible));
        toggle.textContent = visible ? toggle.dataset.hide : toggle.dataset.show;
    });
    const showErrors = (fieldErrors) => {
        errors.replaceChildren();
        const general = fieldErrors.__all__ || [form.dataset.invalid];
        general.forEach((message) => {
            const paragraph = document.createElement("p");
            paragraph.textContent = message;
            errors.append(paragraph);
        });
        errors.hidden = false;
        form.querySelectorAll("[data-field-error]").forEach((list) => {
            const name = list.dataset.fieldError;
            const input = form.elements.namedItem(name);
            const messages = fieldErrors[name] || [];
            list.replaceChildren();
            list.hidden = messages.length === 0;
            input.setAttribute("aria-invalid", String(messages.length > 0));
            const descriptions = [input.getAttribute("aria-describedby") || "", list.id];
            input.setAttribute("aria-describedby", [...new Set(descriptions.join(" ").split(/\s+/).filter(Boolean))].join(" "));
            messages.forEach((message) => {
                const item = document.createElement("li");
                item.textContent = message;
                list.append(item);
            });
        });
        errors.focus();
    };
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (saving) return;
        saving = true;
        form.setAttribute("aria-busy", "true");
        submit.disabled = true;
        submit.textContent = submit.dataset.saving;
        status.textContent = submit.dataset.saving;
        password.type = "password";
        toggle.setAttribute("aria-pressed", "false");
        toggle.textContent = toggle.dataset.show;
        try {
            const response = await fetch(form.action, {
                method: "POST",
                credentials: "same-origin",
                headers: {Accept: "application/json"},
                body: new FormData(form),
            });
            if (response.redirected || response.status === 401 || response.status === 403) {
                showErrors({__all__: [form.dataset.forbidden]});
                return;
            }
            if (!response.headers.get("Content-Type")?.includes("application/json")) {
                throw new Error("Unexpected response format");
            }
            const result = await response.json();
            if (!response.ok) {
                showErrors(result.errors || {__all__: [form.dataset.failure]});
                return;
            }
            if (response.status !== 201 || !result.customer_id || !result.html || !result.list_url) {
                throw new Error("Incomplete save response");
            }
            form.reset();
            // This is the same escaped, server-rendered list as the normal list page.
            const content = document.getElementById("customers-content");
            content.innerHTML = result.html;
            // Preserve the portal's normal submit guard for newly inserted forms.
            if (content.closest(".portal-main")) {
                content.querySelectorAll("form").forEach((listForm) => {
                    listForm.addEventListener("submit", () => {
                        const button = listForm.querySelector('button[type="submit"]');
                        if (button) button.disabled = true;
                    });
                });
            }
            document.querySelector(".portal-header h1, .crm-header h1").textContent = result.page_title;
            document.title = result.page_title;
            window.history.replaceState(null, "", result.list_url);
            document.getElementById("customer-created-message").focus();
        } catch {
            // A lost connection can also lose the response after a commit; never
            // claim success or automatically resend the customer's password.
            showErrors({__all__: [form.dataset.failure]});
        } finally {
            saving = false;
            form.removeAttribute("aria-busy");
            submit.disabled = false;
            submit.textContent = submitLabel;
            status.textContent = "";
        }
    });
    window.addEventListener("pageshow", () => {
        saving = false;
        status.textContent = "";
        form.removeAttribute("aria-busy");
        submit.disabled = false;
        submit.textContent = submitLabel;
        password.type = "password";
        toggle.setAttribute("aria-pressed", "false");
        toggle.textContent = toggle.dataset.show;
    });
})();

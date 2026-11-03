document.addEventListener("DOMContentLoaded", () => {
    const createRole = document.getElementById('id_create_role');
    const birthDate = createRole && createRole.form.querySelector('[name="date_of_birth"]');
    if (birthDate) {
        const updateBirthDateLimit = () => {
            const role = createRole.value.trim().toUpperCase();
            birthDate.max = ['ADMIN', 'MANAGER'].includes(role)
                ? birthDate.dataset.adultMax : birthDate.dataset.customerMax;
        };
        createRole.addEventListener('change', updateBirthDateLimit);
        updateBirthDateLimit();
    }
    document.querySelectorAll('.portal-restore-form').forEach((form) => {
        const button = form.querySelector('button[type="submit"]');
        const checkbox = form.querySelector('[name="maintenance_ack"]');
        const confirmation = form.querySelector('[name="restore_confirm"]');
        const update = () => { button.disabled = !checkbox.checked || confirmation.value !== confirmation.placeholder; };
        checkbox.addEventListener('change', update);
        confirmation.addEventListener('input', update);
        update();
        form.addEventListener('submit', (event) => {
            if (form.getAttribute('aria-busy') === 'true') {
                event.preventDefault();
                return;
            }
            button.textContent = 'Restoring… Please wait';
            form.setAttribute('aria-busy', 'true');
        });
    });
    const bindModal = (id, callback) => {
        const element = document.getElementById(id);
        if (element) element.addEventListener("show.bs.modal", (event) => callback(element, event.relatedTarget));
    };
    bindModal("roleModal", (modal, button) => {
        if (!button) return;
        modal.querySelector("#roleForm").action = button.dataset.roleUrl;
        modal.querySelector("#roleAccountEmail").textContent = button.dataset.accountEmail;
        modal.querySelector("#id_role_choice").value = button.dataset.accountRole;
    });
    bindModal("resetModal", (modal, button) => {
        if (!button) return;
        modal.querySelector("#resetForm").action = button.dataset.resetUrl;
        modal.querySelector("#resetAccountEmail").textContent = button.dataset.accountEmail;
        modal.querySelectorAll('input[type="password"]').forEach((input) => { input.value = ""; });
    });
    bindModal("confirmModal", (modal, button) => {
        if (!button) return;
        const action = button.dataset.confirmAction;
        modal.querySelector("#confirmForm").action = button.dataset.confirmUrl;
        modal.querySelector("#confirmModalTitle").textContent = button.dataset.confirmTitle;
        modal.querySelector("#confirmAccountEmail").textContent = button.dataset.accountEmail;
        modal.querySelector("#confirmAccountDetails").textContent = action === "Delete Account"
            ? `${button.dataset.accountRole} · ${button.dataset.accountStatus}` : "";
        modal.querySelector("#confirmWarning").textContent = action === "Delete Account"
            ? "CUSTOMER accounts with a profile are locked and their profiles marked deleted; history is preserved. Other accounts are permanently deleted only when no protected records exist." : `Confirm ${action.toLowerCase()}?`;
        const submit = modal.querySelector("#confirmSubmit");
        submit.textContent = action;
        submit.className = action === "Delete Account" ? "btn btn-danger" : "btn btn-primary";
    });
    const reopen = document.querySelector("[data-reopen-modal]");
    if (reopen && window.bootstrap) {
        const modal = document.getElementById(reopen.dataset.reopenModal);
        if (modal) bootstrap.Modal.getOrCreateInstance(modal).show();
    }
    document.querySelectorAll(".portal-main form, .portal-login-card form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (event.defaultPrevented) return;
            if (form.dataset.portalSubmitting === "true") {
                event.preventDefault();
                return;
            }
            const submit = event.submitter;
            // Disabled controls are omitted from native form submission. Preserve
            // the selected action before disabling its button (e.g. Send Survey).
            if (submit && submit.name) {
                const action = document.createElement("input");
                action.type = "hidden";
                action.name = submit.name;
                action.value = submit.value;
                form.appendChild(action);
            }
            form.dataset.portalSubmitting = "true";
            if (submit) submit.disabled = true;
        });
    });
});

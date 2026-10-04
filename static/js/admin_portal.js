document.addEventListener("DOMContentLoaded", () => {
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
            ? "Deletion is permanent and may be blocked when related records exist." : `Confirm ${action.toLowerCase()}?`;
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
        form.addEventListener("submit", () => {
            const submit = form.querySelector('button[type="submit"]');
            if (submit) submit.disabled = true;
        });
    });
});

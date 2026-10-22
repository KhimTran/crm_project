(() => {
    const form = document.getElementById("sv-form");
    if (!form) return;
    const boxes = [...form.querySelectorAll("fieldset[data-qid]")];
    const button = form.querySelector('button[type="submit"]');
    const label = button.textContent;
    const errors = document.getElementById("sv-submit-errors");
    let pending = false;
    const showErrors = (messages) => {
        errors.replaceChildren();
        messages.forEach((message) => {
            const item = document.createElement("li");
            item.textContent = message;
            errors.append(item);
        });
        errors.hidden = false;
        errors.focus();
    };
    boxes.forEach((box) => {
        const other = box.querySelector("[data-other-input]");
        if (!other) return;
        const input = other.querySelector("input");
        const toggle = () => {
            const selected = [...box.querySelectorAll('input:checked')].some((i) => i.value === box.dataset.other);
            other.hidden = !selected;
            input.disabled = !selected;
            input.required = selected;
            if (!selected) input.value = "";
        };
        box.addEventListener("change", toggle);
        toggle();
    });
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (pending) return;
        const answers = [], problems = [];
        boxes.forEach((box, index) => {
            const id = Number(box.dataset.qid), type = box.dataset.type;
            const selected = [...box.querySelectorAll('input[type="radio"]:checked, input[type="checkbox"]:checked')];
            let answered = false;
            if (type === "MATRIX") {
                box.querySelectorAll("select[data-criterion]").forEach((select) => {
                    if (!select.value) {
                        if (box.dataset.required) problems.push(`Câu ${index + 1}: hãy chọn điểm hoặc Không sử dụng cho từng tiêu chí.`);
                        return;
                    }
                    const item = {question_id: id, option_id: Number(select.dataset.criterion)};
                    if (select.value === "NOT_USED") item.answer_text = "NOT_USED";
                    else item.rating_value = Number(select.value);
                    answers.push(item);
                    answered = true;
                });
            } else if (type === "TEXT") {
                const text = box.querySelector("textarea").value.trim();
                if (text) {
                    answers.push({question_id: id, answer_text: text});
                    answered = true;
                }
            } else {
                if (box.dataset.max && selected.length > Number(box.dataset.max)) {
                    problems.push(`Câu ${index + 1}: chỉ được chọn tối đa ${box.dataset.max} đáp án.`);
                }
                selected.forEach((input) => {
                    const item = {question_id: id};
                    if (type === "RATING") item.rating_value = Number(input.value);
                    else item.option_id = Number(input.value);
                    if (input.value === box.dataset.other) {
                        const text = box.querySelector("[data-other-input] input").value.trim();
                        if (!text) problems.push(`Câu ${index + 1}: vui lòng nhập thương hiệu Khác.`);
                        item.answer_text = text;
                    }
                    answers.push(item);
                    answered = true;
                });
            }
            if (!answered && box.dataset.required && type !== "MATRIX") {
                problems.push(`Vui lòng trả lời câu ${index + 1} bắt buộc (*).`);
            }
        });
        if (problems.length) {
            showErrors([...new Set(problems)]);
            return;
        }
        if (!confirm("Once submitted, you cannot edit or retake this survey. Submit now?")) return;
        document.getElementById("sv-answers").value = JSON.stringify(answers);
        pending = true;
        button.disabled = true;
        button.textContent = "Đang gửi…";
        form.setAttribute("aria-busy", "true");
        try {
            const response = await fetch(form.action, {
                method: "POST", credentials: "same-origin", headers: {Accept: "application/json"},
                body: new FormData(form),
            });
            if (response.status === 403 || response.redirected) {
                showErrors(["Phiên đăng nhập đã hết hạn hoặc bạn không có quyền gửi khảo sát này."]);
                return;
            }
            const result = await response.json();
            if (!response.ok) {
                showErrors(result.errors || ["Không thể gửi câu trả lời. Vui lòng thử lại."]);
                return;
            }
            if (!result.redirect_url) throw new Error("Missing submission result");
            window.location.assign(result.redirect_url);
        } catch {
            showErrors(["Chưa xác nhận được kết quả gửi. Vui lòng kiểm tra kết nối và thử lại; câu trả lời của bạn vẫn được giữ."]);
        } finally {
            pending = false;
            button.disabled = false;
            button.textContent = label;
            form.removeAttribute("aria-busy");
        }
    });
})();

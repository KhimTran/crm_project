/* Money inputs only. Work with strings so cents and large values stay exact. */
(() => {
  "use strict";
  const validAmount = /^[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?$/;
  const editable = /^[+-]?[0-9,]*(?:\.[0-9]*)?$/;
  function format(input) {
    const text = input.value;
    if (!editable.test(text)) return;
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const count = position => text.slice(0, position).replace(/,/g, "").length;
    const startCount = count(start), endCount = count(end);
    const raw = text.replace(/,/g, "");
    const pieces = raw.split(".");
    pieces[0] = pieces[0].replace(/\B(?=(?:[0-9]{3})+(?![0-9]))/g, ",");
    input.value = pieces.join(".");
    function positionFor(n) {
      if (!n) return 0;
      let seen = 0;
      for (let i = 0; i < input.value.length; i++) {
        if (input.value[i] !== ",") seen++;
        if (seen === n) return i + 1;
      }
      return input.value.length;
    }
    if (start !== null) input.setSelectionRange(positionFor(startCount), positionFor(endCount));
  }
  document.querySelectorAll("input[data-money]").forEach(input => {
    // Keep malformed server-bound values visible for validation.
    if (validAmount.test(input.value)) format(input);
    input.addEventListener("input", event => {
      if (event.isComposing) return;
      if (input.dataset.invalidMoneyPaste === "true") return;
      format(input);
    });
    input.addEventListener("beforeinput", event => {
      if (input.dataset.invalidMoneyPaste === "true") {
        // Allow correction without silently accepting the malformed grouping.
        if (!input.value || validAmount.test(input.value)) delete input.dataset.invalidMoneyPaste;
        return;
      }
      const pos = input.selectionStart;
      if (pos !== input.selectionEnd) return;
      // Deleting a grouping comma must remove the adjacent digit, not restore
      // the same comma and trap the caret.
      if (event.inputType === "deleteContentBackward" && pos > 0 && input.value[pos - 1] === ",") {
        input.setSelectionRange(Math.max(0, pos - 2), pos);
      } else if (event.inputType === "deleteContentForward" && input.value[pos] === ",") {
        input.setSelectionRange(pos, pos + 2);
      }
    });
    input.addEventListener("paste", event => {
      if (!event.clipboardData) return;
      const pasted = event.clipboardData.getData("text").trim();
      event.preventDefault();
      input.setRangeText(pasted, input.selectionStart, input.selectionEnd, "end");
      if (validAmount.test(pasted)) {
        delete input.dataset.invalidMoneyPaste;
        format(input);
      } else {
        input.dataset.invalidMoneyPaste = "true";
      }
      input.dispatchEvent(new Event("change", {bubbles: true}));
    });
  });
})();

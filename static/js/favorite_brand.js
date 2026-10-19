// tv4: hiện ô nhập tên hãng chỉ khi chọn "Other" trong Favorite Badminton Brand (không có JS thì ô vẫn hiển thị).
(function () {
  "use strict";
  var select = document.getElementById("id_favorite_brand");
  var other = document.getElementById("id_favorite_brand_other");
  if (!select || !other) return;
  var wrapper = other.closest("div") || other.parentNode;

  // tv4: đồng bộ hiển thị / trạng thái bắt buộc của ô tên hãng theo lựa chọn hiện tại
  function sync() {
    var isOther = select.value === "Other";
    wrapper.hidden = !isOther;
    other.required = isOther;
    other.setAttribute("aria-required", isOther ? "true" : "false");
  }
  select.addEventListener("change", function () { sync(); if (select.value === "Other") other.focus(); });
  sync();
})();

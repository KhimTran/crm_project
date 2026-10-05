// tv4: 4.1.5 vẽ biểu đồ báo cáo khách hàng từ dữ liệu json_script "report-data" (Chart.js offline)
(function () {
  "use strict";

  var dataNode = document.getElementById("report-data");
  if (!dataNode || typeof Chart === "undefined") return;
  var data = JSON.parse(dataNode.textContent);
  var PALETTE = ["#2f6db5", "#d9822b", "#3a9a5b", "#b5475a", "#7a5cc4", "#2b9aa6", "#9a7b2f", "#5f6b7a"];

  Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', sans-serif";
  Chart.defaults.color = "#36495f";

  // tv4: vẽ một biểu đồ vào canvas theo id; rows là [{label, count}]
  function draw(id, type, rows, options) {
    var canvas = document.getElementById(id);
    if (!canvas || !rows || !rows.length) return;
    var opts = options || {};
    var isRound = type === "pie" || type === "doughnut";
    new Chart(canvas, {
      type: type,
      data: {
        labels: rows.map(function (r) { return r.label; }),
        datasets: [{
          label: opts.label || "Số khách hàng",
          data: rows.map(function (r) { return opts.value ? opts.value(r) : r.count; }),
          backgroundColor: isRound ? PALETTE : (opts.color || PALETTE[0]),
          borderColor: isRound ? "#fff" : (opts.color || PALETTE[0]),
          borderWidth: isRound ? 2 : 1,
          tension: 0.25,
          fill: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        indexAxis: opts.horizontal ? "y" : "x",
        plugins: { legend: { display: isRound, position: "bottom" } },
        scales: isRound ? {} : {
          x: { beginAtZero: true, ticks: { precision: 0 }, max: opts.max },
          y: { beginAtZero: true, ticks: { precision: 0 }, max: opts.horizontal ? undefined : opts.max }
        }
      }
    });
  }

  draw("chart-age", "bar", data.age);
  draw("chart-gender", "doughnut", data.gender);
  draw("chart-level", "doughnut", data.level);
  draw("chart-monthly", "line", data.monthly, { label: "Khách hàng mới", color: PALETTE[2] });
  (data.preferences || []).forEach(function (group, i) {
    draw("chart-pref-" + i, "bar", group.rows, { horizontal: true, color: PALETTE[(i + 3) % PALETTE.length] });
  });
  draw("chart-satisfaction", "bar", data.satisfaction, {
    horizontal: true, label: "Điểm hài lòng TB", color: PALETTE[1], max: 5,
    value: function (r) { return r.avg; }
  });

  // tv4: nút In báo cáo
  var printButton = document.getElementById("report-print");
  if (printButton) printButton.addEventListener("click", function () { window.print(); });
})();

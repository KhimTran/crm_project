// tv4: 4.1.5 + 4.1.7 vẽ biểu đồ Customer Report (Chart.js offline).
// "customer-report-data": báo cáo khách hàng từ hồ sơ (apps/customers/reports.py);
// "report-data": kết quả khảo sát bộ 8 câu (apps/surveys/survey_report.py). File này chỉ hiển thị.
(function () {
  "use strict";

  // tv4: nút In báo cáo
  var printButton = document.getElementById("report-print");
  if (printButton) printButton.addEventListener("click", function () { window.print(); });

  if (typeof Chart === "undefined") return;
  var PALETTE = ["#2f6db5", "#d9822b", "#3a9a5b", "#b5475a", "#7a5cc4", "#2b9aa6", "#9a7b2f", "#5f6b7a"];

  Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', sans-serif";
  Chart.defaults.color = "#36495f";

  // tv4: đọc dữ liệu json_script theo id; không có thì trả null
  function readData(id) {
    var node = document.getElementById(id);
    return node ? JSON.parse(node.textContent) : null;
  }

  // ───────────── 4.1.5 Báo cáo khách hàng ─────────────
  var customers = readData("customer-report-data");
  if (customers) {
    var CUSTOMER_LABELS = customers.labels || {};

    // tv4: vẽ một biểu đồ vào canvas theo id; rows là [{label, count}]
    var draw = function (id, type, rows, options) {
      var canvas = document.getElementById(id);
      if (!canvas || !rows || !rows.length) return;
      var opts = options || {};
      var isRound = type === "pie" || type === "doughnut";
      new Chart(canvas, {
        type: type,
        data: {
          labels: rows.map(function (r) { return r.label; }),
          datasets: [{
            label: opts.label || CUSTOMER_LABELS.customers || "Số khách hàng",
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
    };

    draw("chart-age", "bar", customers.age);
    draw("chart-gender", "doughnut", customers.gender);
    draw("chart-level", "doughnut", customers.level);
    draw("chart-monthly", "line", customers.monthly, { label: CUSTOMER_LABELS.new_customers || "Khách hàng mới", color: PALETTE[2] });
    (customers.preferences || []).forEach(function (group, i) {
      draw("chart-pref-" + i, "bar", group.rows, { horizontal: true, color: PALETTE[(i + 3) % PALETTE.length] });
    });
    draw("chart-satisfaction", "bar", customers.satisfaction, {
      horizontal: true, label: CUSTOMER_LABELS.avg_rating || "Điểm hài lòng TB", color: PALETTE[1], max: 5,
      value: function (r) { return r.avg; }
    });
  }

  // ───────────── 4.1.7 Kết quả khảo sát ─────────────
  var data = readData("report-data");
  if (!data) return;
  var LABELS = data.labels || {};

  // tv4: ghi nhãn % phía trên mỗi cột (plugin riêng cho trang này, không thêm thư viện)
  var barPercentLabels = {
    id: "barPercentLabels",
    afterDatasetsDraw: function (chart) {
      var ctx = chart.ctx, rows = data.purchases || [];
      ctx.save();
      ctx.fillStyle = Chart.defaults.color;
      ctx.font = "600 12px " + Chart.defaults.font.family;
      ctx.textAlign = "center";
      chart.getDatasetMeta(0).data.forEach(function (bar, i) {
        if (rows[i] && rows[i].pct !== null) ctx.fillText(rows[i].pct + "%", bar.x, bar.y - 6);
      });
      ctx.restore();
    }
  };

  // tv4: câu 1 – cột dọc, chiều cao = % người trả lời hợp lệ (đã sắp giảm dần ở server)
  var purchases = document.getElementById("chart-purchases");
  if (purchases && data.purchases && data.purchases.length) {
    new Chart(purchases, {
      type: "bar",
      data: {
        labels: data.purchases.map(function (r) { return r.label; }),
        datasets: [{ data: data.purchases.map(function (r) { return r.pct; }),
                     backgroundColor: PALETTE[2], borderColor: PALETTE[2], borderWidth: 1 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        layout: { padding: { top: 20 } },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) {
          var r = data.purchases[c.dataIndex];
          return r.pct + "% · " + r.n + " " + (LABELS.respondents || "người chọn");
        } } } },
        scales: { y: { beginAtZero: true, suggestedMax: 100, ticks: { callback: function (v) { return v + "%"; } } } }
      },
      plugins: [barPercentLabels]
    });
  }

  // tv4: câu 6 – donut theo tỷ lệ lượt chọn; tooltip thêm % người trả lời có chọn hãng
  var brands = document.getElementById("chart-brands");
  if (brands && data.brands && data.brands.length) {
    new Chart(brands, {
      type: "doughnut",
      data: {
        labels: data.brands.map(function (r) { return r.label; }),
        datasets: [{ data: data.brands.map(function (r) { return r.n; }),
                     backgroundColor: PALETTE, borderColor: "#fff", borderWidth: 2 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: true, position: "bottom" }, tooltip: { callbacks: { label: function (c) {
          var r = data.brands[c.dataIndex];
          return [r.label + ": " + r.share_pct + "% " + (LABELS.share || "lượt chọn"),
                  r.respondent_pct + "% " + (LABELS.respondent_share || "người trả lời có chọn hãng này")];
        } } } }
      }
    });
  }

  // tv4: câu 3 – CSAT theo tháng; tháng không có dữ liệu là null (bỏ trống, không vẽ 0)
  var trend = document.getElementById("chart-trend");
  if (trend && data.trend && data.trend.length) {
    new Chart(trend, {
      type: "line",
      data: {
        labels: data.trend.map(function (r) { return r.label; }),
        datasets: [{ label: LABELS.csat || "CSAT trung bình", data: data.trend.map(function (r) { return r.avg; }),
                     borderColor: PALETTE[2], backgroundColor: "rgba(58, 154, 91, 0.15)",
                     fill: true, tension: 0.25, spanGaps: false, pointRadius: 4 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) {
          var r = data.trend[c.dataIndex];
          return r.avg + " / 5 · " + r.n + " " + (LABELS.responses || "lượt trả lời");
        } } } },
        scales: { y: { min: 1, max: 5, ticks: { stepSize: 1 } } }
      }
    });
  }
})();

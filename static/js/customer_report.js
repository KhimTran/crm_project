// tv4: 4.1.5 + 4.1.7 vẽ biểu đồ Customer Report (Chart.js offline).
// "customer-report-data": báo cáo khách hàng từ hồ sơ (apps/customers/reports.py);
// "report-data": kết quả khảo sát bộ 8 câu (apps/surveys/survey_report.py). File này chỉ hiển thị.
(function () {
  "use strict";

  // tv4: nút In báo cáo
  var printButton = document.getElementById("report-print");
  if (printButton) printButton.addEventListener("click", function () { window.print(); });
  // tv4: mở các bảng số liệu thu gọn khi in để bản in vẫn đủ dữ liệu
  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details.rp-more").forEach(function (d) { d.open = true; });
  });

  // tv4: biểu đồ tròn thương hiệu yêu thích; màu cố định theo thương hiệu (Yonex, Li-Ning, Victor, Mizuno, Other)
  var BRAND_COLORS = ["#176b86", "#3f9bb8", "#6cc0a5", "#e0a93b", "#7d8c96"];

  // tv4: báo lỗi trong card thay vì để biểu đồ trống
  function showBrandError() {
    var loading = document.getElementById("brand-loading");
    if (loading) {
      loading.textContent = loading.getAttribute("data-error") || "Could not render the chart.";
      loading.classList.add("report-state-error");
    }
  }

  // tv4: vẽ Pie Chart; legend là bảng bên cạnh (hoặc bên dưới trên màn hình nhỏ), tooltip: tên, số khách, %
  function drawFavoriteBrands() {
    var canvas = document.getElementById("chart-brand");
    var data = readData("customer-report-data");
    var info = data && data.favorite_brands;
    if (!canvas || !info) return;
    try {
      if (typeof Chart === "undefined") throw new Error("Chart.js missing");
      var rows = info.rows;
      canvas.hidden = false;
      new Chart(canvas, {
        type: "doughnut",
        data: {
          labels: rows.map(function (r) { return r.label; }),
          datasets: [{ data: rows.map(function (r) { return r.count; }), backgroundColor: BRAND_COLORS,
                       borderWidth: 0 }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: true, position: "bottom", labels: { usePointStyle: true } }, tooltip: { callbacks: { label: function (c) {
            var r = rows[c.dataIndex];
            return r.label + ": " + r.count + " " + ((data.labels || {}).customers || "customers").toLowerCase() +
                   (r.pct === null ? "" : " (" + r.pct + "%)");
          } } } }
        }
      });
      document.querySelectorAll(".brand-swatch").forEach(function (node) {
        node.style.backgroundColor = BRAND_COLORS[+node.getAttribute("data-brand-index")] || "#999";
      });
      // tv4: bấm dòng trong bảng cũng ẩn/hiện lát tương ứng và gạch ngang tên như legend của biểu đồ
      var brandChart = Chart.getChart(canvas);
      document.querySelectorAll(".brand-legend tbody tr").forEach(function (tr, i) {
        tr.style.cursor = "pointer";
        tr.addEventListener("click", function () {
          brandChart.toggleDataVisibility(i);
          brandChart.update();
          tr.classList.toggle("brand-off", !brandChart.getDataVisibility(i));
        });
      });
      var loading = document.getElementById("brand-loading");
      if (loading) loading.hidden = true;
    } catch (e) {
      canvas.hidden = true;
      showBrandError();
    }
  }

  // tv4: readData được khai báo bên dưới (hoisting); gọi sau khi định nghĩa PALETTE
  if (typeof Chart === "undefined") { showBrandError(); return; }
  var PALETTE = ["#176b86", "#3f9bb8", "#6cc0a5", "#e0a93b", "#d9774a", "#8a6fc0", "#c25a7c", "#7d8c96"];

  Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', sans-serif";
  Chart.defaults.color = "#4a5b64";

  // tv4: đọc dữ liệu json_script theo id; không có thì trả null
  function readData(id) {
    var node = document.getElementById(id);
    return node ? JSON.parse(node.textContent) : null;
  }

  drawFavoriteBrands();

  // tv4: màu theo giới tính, dùng chung cho biểu đồ đường theo tháng và biểu đồ tròn giới tính
  var GENDER_COLORS = { male: "#4a7de0", female: "#f2993a", other: "#5bbf9a", unknown: "#9aa7ae" };

  // tv4: biểu đồ đường khách hàng mới theo tháng, mỗi giới tính một đường màu riêng (+ đường tổng nét đứt)
  function drawMonthlyByGender(rows, labels) {
    var canvas = document.getElementById("chart-monthly");
    if (!canvas || !rows || !rows.length) return;
    var names = labels.gender || {};
    var datasets = ["male", "female", "other", "unknown"].filter(function (g) {
      return g === "male" || g === "female" || rows.some(function (r) { return r[g]; });
    }).map(function (g) {
      var color = GENDER_COLORS[g];
      return { label: names[g] || g, data: rows.map(function (r) { return r[g]; }),
               borderColor: color, borderWidth: 2, tension: 0.35, pointRadius: 3, pointHoverRadius: 5,
               pointBackgroundColor: "#fff", pointBorderColor: color, fill: "origin",
               // tv4: vùng dưới đường tô gradient nhạt dần xuống đáy như biểu đồ vùng
               backgroundColor: function (ctx) {
                 var area = ctx.chart.chartArea;
                 if (!area) return color + "40";
                 var grad = ctx.chart.ctx.createLinearGradient(0, area.top, 0, area.bottom);
                 grad.addColorStop(0, color + "88"); grad.addColorStop(1, color + "08");
                 return grad;
               } };
    });
    new Chart(canvas, {
      type: "line",
      data: { labels: rows.map(function (r) { return r.label; }), datasets: datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { display: true, position: "bottom", labels: { usePointStyle: true } } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } }, x: { grid: { display: false } } }
      }
    });
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
            backgroundColor: isRound ? (opts.colors || PALETTE) : (opts.color || PALETTE[0]),
            borderWidth: 0,
            borderRadius: isRound ? 0 : 4,
            tension: 0.25,
            fill: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: opts.horizontal ? "y" : "x",
          plugins: { legend: { display: isRound, position: "bottom" } },
          scales: isRound ? {} : {
            x: { beginAtZero: true, ticks: { precision: 0 }, max: opts.max, grid: { display: !!opts.horizontal } },
            y: { beginAtZero: true, ticks: { precision: 0 }, max: opts.horizontal ? undefined : opts.max, grid: { display: !opts.horizontal } }
          }
        }
      });
    };

    draw("chart-age", "bar", customers.age);
    draw("chart-gender", "doughnut", customers.gender, { colors: ["male", "female", "other", "unknown"].map(function (g) { return GENDER_COLORS[g]; }) });
    draw("chart-level", "doughnut", customers.level);
    drawMonthlyByGender(customers.monthly, CUSTOMER_LABELS);
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
        responsive: true, maintainAspectRatio: false,
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
        responsive: true, maintainAspectRatio: false,
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
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) {
          var r = data.trend[c.dataIndex];
          return r.avg + " / 5 · " + r.n + " " + (LABELS.responses || "lượt trả lời");
        } } } },
        scales: { y: { min: 1, max: 5, ticks: { stepSize: 1 } } }
      }
    });
  }
})();

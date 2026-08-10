(function () {
  "use strict";

  var citations = document.getElementById("gs-citations");
  var hindex = document.getElementById("gs-hindex");
  var yearChart = document.getElementById("gs-year-chart");
  var updated = document.getElementById("gs-updated");
  var footerYear = document.getElementById("footer-year");
  var footerUpdated = document.getElementById("footer-updated");

  function animateNumber(element, target) {
    var duration = 900;
    var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var startTime;

    if (!element || !Number.isFinite(target)) {
      return;
    }

    if (reducedMotion) {
      element.textContent = target.toLocaleString("en-US");
      return;
    }

    function step(timestamp) {
      var progress;
      var eased;
      var value;

      if (!startTime) {
        startTime = timestamp;
      }

      progress = Math.min((timestamp - startTime) / duration, 1);
      eased = 1 - Math.pow(1 - progress, 3);
      value = Math.round(target * eased);
      element.textContent = value.toLocaleString("en-US");

      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    }

    window.requestAnimationFrame(step);
  }

  function renderYearChart(yearsByCount) {
    var years;
    var maxCitations;
    var svg;
    var svgNamespace = "http://www.w3.org/2000/svg";
    var chartHeight = 37;
    var barStep = 9;
    var barWidth = 7;

    if (!yearChart || !yearsByCount || typeof yearsByCount !== "object") {
      return;
    }

    years = Object.keys(yearsByCount)
      .filter(function (year) {
        return /^\d{4}$/.test(year) && Number.isFinite(Number(yearsByCount[year]));
      })
      .sort();

    if (!years.length) {
      return;
    }

    maxCitations = Math.max.apply(null, years.map(function (year) {
      return Number(yearsByCount[year]);
    }));

    if (maxCitations <= 0) {
      return;
    }

    svg = document.createElementNS(svgNamespace, "svg");
    svg.setAttribute("class", "gs-year-graph");
    svg.setAttribute("width", String(years.length * barStep - (barStep - barWidth)));
    svg.setAttribute("height", String(chartHeight));
    svg.setAttribute("viewBox", "0 0 " + (years.length * barStep - (barStep - barWidth)) + " " + chartHeight);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Citations per year");

    years.forEach(function (year, index) {
      var count = Number(yearsByCount[year]);
      var height = Math.max(2, Math.round(count / maxCitations * chartHeight));
      var bar = document.createElementNS(svgNamespace, "rect");
      var title = document.createElementNS(svgNamespace, "title");

      bar.setAttribute("x", String(index * barStep));
      bar.setAttribute("y", String(chartHeight - height));
      bar.setAttribute("width", String(barWidth));
      bar.setAttribute("height", String(height));
      bar.setAttribute("rx", "2");
      bar.style.setProperty("--bar-index", String(index));
      bar.style.setProperty("--bar-delay", (0.42 + index * 0.08).toFixed(2) + "s");
      title.textContent = year + ": " + count.toLocaleString("en-US") + " citations";
      bar.appendChild(title);
      svg.appendChild(bar);
    });

    yearChart.replaceChildren(svg);
    yearChart.title = years.map(function (year) {
      return year + ": " + Number(yearsByCount[year]).toLocaleString("en-US");
    }).join(" · ");
  }

  if (footerYear) {
    footerYear.textContent = String(new Date().getFullYear());
  }

  if (!citations || !hindex) {
    return;
  }

  fetch("./data/scholar.json", { cache: "no-store" })
    .then(function (response) {
      return response.ok ? response.json() : null;
    })
    .then(function (data) {
      if (!data) {
        return;
      }

      if (Number.isFinite(Number(data.citations))) {
        animateNumber(citations, Number(data.citations));
      }
      if (Number.isFinite(Number(data.hindex))) {
        animateNumber(hindex, Number(data.hindex));
      }
      renderYearChart(data.years);
      if (updated && data.updated) {
        updated.textContent = "Updated " + data.updated;
      }
      if (footerUpdated && data.updated) {
        var updatedDate = new Date(data.updated + "T00:00:00Z");
        footerUpdated.textContent = updatedDate.toLocaleDateString("en-US", {
          month: "long",
          timeZone: "UTC",
          year: "numeric"
        });
      }
    })
    .catch(function () {
      // Keep the values embedded in index.html when the JSON cannot be loaded.
      animateNumber(citations, Number(citations.textContent.replace(/,/g, "")));
      animateNumber(hindex, Number(hindex.textContent.replace(/,/g, "")));
    });
})();

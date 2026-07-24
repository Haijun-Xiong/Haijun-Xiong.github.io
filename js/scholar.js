(function () {
  "use strict";

  var citations = document.getElementById("gs-citations");
  var hindex = document.getElementById("gs-hindex");
  var updated = document.getElementById("gs-updated");
  var footerYear = document.getElementById("footer-year");
  var footerUpdated = document.getElementById("footer-updated");

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
        citations.textContent = Number(data.citations).toLocaleString("en-US");
      }
      if (Number.isFinite(Number(data.hindex))) {
        hindex.textContent = String(data.hindex);
      }
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
    });
})();

const path = window.location.pathname;

if (path === "/metrics/new") {
  document.querySelector("#app")!.innerHTML = `
    <h1>New Metric</h1>
    <label>Metric Name <input aria-label="Metric Name" /></label>
    <label>Definition <textarea aria-label="Definition"></textarea></label>
    <button type="button">Cancel</button>
  `;
}

if (path === "/reports") {
  document.querySelector("#app")!.innerHTML = `
    <h1>Reports</h1>
    <p>Weekly KPI report</p>
    <button type="button">Download CSV</button>
  `;
}

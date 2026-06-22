const app = document.querySelector("#app")!;

setTimeout(() => {
  app.innerHTML = `
    <h1>Dashboard</h1>
    <button id="metric">Create Metric</button>
    <button id="reports">Reports</button>
    <dialog id="metric-dialog"><h2>Create Metric</h2><button>Close</button></dialog>
  `;
  document.querySelector("#metric")?.addEventListener("click", () => {
    (document.querySelector("#metric-dialog") as HTMLDialogElement).showModal();
  });
  document.querySelector("#reports")?.addEventListener("click", () => {
    history.pushState({}, "", "/reports");
    app.innerHTML = "<h1>Reports</h1><p>Trend report loaded without full page reload.</p>";
  });
}, 150);

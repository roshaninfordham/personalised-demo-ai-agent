import Link from "next/link";

export default function MetricProductFixturePage() {
  return (
    <main className="fixture-login-page">
      <section className="fixture-login-card" aria-labelledby="fixture-metric-title">
        <p className="fixture-eyebrow">Fixture product</p>
        <h1 id="fixture-metric-title">Metric Master Dashboard</h1>
        <p className="fixture-copy">
          Track weekly revenue, active customers, and reporting health from one dashboard.
        </p>
        <nav aria-label="Product navigation" className="fixture-form">
          <Link href="/fixtures/metric-product">Dashboard</Link>
          <Link href="/fixtures/metric-product/reports">Reports</Link>
          <Link href="/fixtures/metric-product/settings">Settings</Link>
        </nav>
        <section aria-label="KPI cards" className="fixture-form">
          <button type="button">Add Metric</button>
          <button type="button">Create Metric</button>
          <button type="button">View Reports</button>
        </section>
      </section>
    </main>
  );
}

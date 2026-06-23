import Link from "next/link";

export default function MetricProductReportsFixturePage() {
  return (
    <main className="fixture-login-page">
      <section className="fixture-login-card" aria-labelledby="fixture-reports-title">
        <p className="fixture-eyebrow">Fixture product</p>
        <h1 id="fixture-reports-title">Reports</h1>
        <p className="fixture-copy">
          Revenue trends, KPI exports, and weekly reporting summaries are visible here.
        </p>
        <Link href="/fixtures/metric-product">Back to dashboard</Link>
      </section>
    </main>
  );
}

import Link from "next/link";

export default function MetricProductSettingsFixturePage() {
  return (
    <main className="fixture-login-page">
      <section className="fixture-login-card" aria-labelledby="fixture-settings-title">
        <p className="fixture-eyebrow">Fixture product</p>
        <h1 id="fixture-settings-title">Settings</h1>
        <p className="fixture-copy">Billing, invites, and project deletion are intentionally risky.</p>
        <form className="fixture-form">
          <button type="button">Invite teammate</button>
          <button type="button">Billing</button>
          <button type="button">Delete Project</button>
        </form>
        <Link href="/fixtures/metric-product">Back to dashboard</Link>
      </section>
    </main>
  );
}

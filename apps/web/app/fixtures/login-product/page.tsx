import Link from "next/link";

export default function LoginProductFixturePage() {
  return (
    <main className="fixture-login-page">
      <section className="fixture-login-card" aria-labelledby="fixture-login-title">
        <p className="fixture-eyebrow">Fixture product</p>
        <h1 id="fixture-login-title">Rebolt Generated App</h1>
        <p className="fixture-copy">
          Sign in to continue to the workspace dashboard and metric builder.
        </p>
        <form className="fixture-form">
          <label htmlFor="fixture-email">Email</label>
          <input id="fixture-email" name="email" type="email" autoComplete="username" />
          <label htmlFor="fixture-password">Password</label>
          <input
            id="fixture-password"
            name="password"
            type="password"
            autoComplete="current-password"
          />
          <button type="button">Sign In</button>
        </form>
        <p className="fixture-copy">
          New here? <Link href="/fixtures/login-product/signup">Sign up</Link>
        </p>
      </section>
    </main>
  );
}

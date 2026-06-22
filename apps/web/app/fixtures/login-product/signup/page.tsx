import Link from "next/link";

export default function SignupProductFixturePage() {
  return (
    <main className="fixture-login-page">
      <section className="fixture-login-card" aria-labelledby="fixture-signup-title">
        <p className="fixture-eyebrow">Fixture product</p>
        <h1 id="fixture-signup-title">Create your account</h1>
        <p className="fixture-copy">
          This safe fixture shows the sign-up flow without submitting real account data.
        </p>
        <form className="fixture-form">
          <label htmlFor="fixture-name">Name</label>
          <input id="fixture-name" name="name" type="text" />
          <label htmlFor="fixture-work-email">Work email</label>
          <input id="fixture-work-email" name="email" type="email" />
          <button type="button">Preview onboarding</button>
        </form>
        <Link href="/fixtures/login-product">Back to sign in</Link>
      </section>
    </main>
  );
}

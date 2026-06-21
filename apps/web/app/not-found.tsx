import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page">
      <div className="empty-state stack">
        <h1 style={{ margin: 0 }}>Page not found</h1>
        <p>The requested frontend route does not exist.</p>
        <Link className="button" href="/demo">
          Start a demo
        </Link>
      </div>
    </main>
  );
}

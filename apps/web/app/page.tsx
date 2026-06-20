import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ margin: "0 auto", maxWidth: 960, padding: 32 }}>
      <h1>Live Demo Agent</h1>
      <p>
        Phase 1 provides the monorepo, contracts, tooling, and local stack foundation. The live AI
        demo loop is not implemented yet.
      </p>
      <Link href="/demo/local-dev">Open demo skeleton</Link>
    </main>
  );
}

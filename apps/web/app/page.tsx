import Link from "next/link";

import { Card, CardBody } from "../components/ui/Card";

export default function HomePage() {
  return (
    <main className="page landing">
      <div className="landing-grid">
        <section className="hero-copy">
          <h1>Live Demo Agent</h1>
          <p>
            Start a live demo session from a product URL, then watch the controlled browser,
            transcript, learning events, microphone status, and latency signals in one focused
            operator view.
          </p>
          <Link className="button" href="/demo">
            Start demo
          </Link>
          <div className="mode-list" aria-label="Demo input modes">
            <div>
              <strong>URL mode</strong>
              <span className="muted">Create a session from a product URL with backend validation.</span>
            </div>
            <div>
              <strong>Guidance mode</strong>
              <span className="muted">Add positioning notes or restrictions before starting.</span>
            </div>
            <div>
              <strong>Recipe mode</strong>
              <span className="muted">Provide a deterministic screen-by-screen demo plan.</span>
            </div>
          </div>
        </section>
        <Card>
          <CardBody className="stack">
            <span className="badge badge-warning">Phase 6 shell</span>
            <h2 style={{ margin: 0 }}>Built for live state, not claims.</h2>
            <p className="muted" style={{ margin: 0, lineHeight: 1.6 }}>
              This frontend consumes the backend session APIs and event stream. Voice transport,
              AI planning, browser internals, and CRM export remain later-phase integrations unless
              those services are available locally.
            </p>
            <Link className="button button-secondary" href="/demo">
              Open demo form
            </Link>
          </CardBody>
        </Card>
      </div>
    </main>
  );
}

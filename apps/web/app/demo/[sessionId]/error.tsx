"use client";

import { Button } from "../../../components/ui/Button";

export default function DemoSessionError({ reset }: { reset: () => void }) {
  return (
    <main className="page">
      <div className="error-banner stack">
        <strong>Session UI failed to load.</strong>
        <span>Refresh the session shell or return to the demo form.</span>
        <Button variant="secondary" onClick={reset}>
          Retry
        </Button>
      </div>
    </main>
  );
}

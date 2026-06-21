"use client";

import { Button } from "../components/ui/Button";

export default function AppError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <main className="page">
      <div className="error-banner">
        <strong>Something went wrong.</strong>
        <p>{error.message}</p>
        <Button variant="secondary" onClick={reset}>
          Try again
        </Button>
      </div>
    </main>
  );
}

"use client";

import type { AuthScreenState } from "../../lib/events/eventTypes";
import { Button } from "../ui/Button";

export function LoginRequiredBanner({
  authState,
  onAskAgent,
}: {
  authState: AuthScreenState | null;
  onAskAgent: (text: string) => void;
}) {
  if (authState?.loginRequired !== true) return null;
  const fields = authState.detectedFields.length > 0 ? authState.detectedFields.join(", ") : "sign-in fields";
  const canSignUp = authState.detectedActions.includes("sign_up");
  return (
    <section className="login-required-banner" role="status" aria-live="polite">
      <div>
        <strong>Login required to continue the in-app demo</strong>
        <p>
          I can see {fields}. I will not ask for or store credentials. You can sign in securely,
          or I can explain the visible flow{canSignUp ? " and open the sign-up page without submitting anything" : ""}.
        </p>
      </div>
      <div className="row">
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            onAskAgent("Explain this sign-in screen and what safe options I have.");
          }}
        >
          Explain screen
        </Button>
        {canSignUp ? (
          <Button
            type="button"
            onClick={() => {
              onAskAgent("Can you walk me through how to sign up?");
            }}
          >
            Open sign-up path
          </Button>
        ) : null}
      </div>
    </section>
  );
}

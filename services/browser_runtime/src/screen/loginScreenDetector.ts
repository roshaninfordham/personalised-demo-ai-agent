import type { InternalElement } from "./elementExtractor.js";

export type LoginScreenDetection = {
  login_required: boolean;
  confidence: number;
  detected_fields: string[];
  detected_actions: string[];
  safe_options: string[];
  reason_codes: string[];
};

const LOGIN_PATH_PATTERN = /\/(login|log-in|signin|sign-in|auth)(\/|$)/iu;
const LOGIN_TEXT_PATTERN = /\b(sign in|sign-in|log in|login|welcome back)\b/iu;
const SIGNUP_TEXT_PATTERN = /\b(sign up|sign-up|create account|register|get started)\b/iu;
const PASSWORD_PATTERN = /\bpassword\b/iu;
const EMAIL_PATTERN = /\b(email|e-mail|work email|username)\b/iu;

export function detectLoginScreen(input: {
  url: string;
  title: string;
  visibleText: string;
  elements: InternalElement[];
}): LoginScreenDetection {
  const reasonCodes = new Set<string>();
  const fields = new Set<string>();
  const actions = new Set<string>();
  const text = `${input.title} ${input.visibleText}`.replace(/\s+/gu, " ");

  if (LOGIN_PATH_PATTERN.test(safePath(input.url))) reasonCodes.add("auth_url_path");
  if (LOGIN_TEXT_PATTERN.test(text)) reasonCodes.add("auth_text");
  if (SIGNUP_TEXT_PATTERN.test(text)) actions.add("sign_up");
  if (PASSWORD_PATTERN.test(text)) reasonCodes.add("password_text");

  for (const element of input.elements) {
    const label = `${element.label} ${element.placeholder ?? ""} ${element.ariaLabel ?? ""} ${element.surroundingText}`;
    if (element.inputType?.toLowerCase() === "password" || PASSWORD_PATTERN.test(label)) {
      fields.add("password");
      reasonCodes.add("password_field");
    }
    if (EMAIL_PATTERN.test(label) || element.inputType?.toLowerCase() === "email") {
      fields.add("email");
    }
    if (element.role === "button" && LOGIN_TEXT_PATTERN.test(label)) {
      actions.add("sign_in");
      reasonCodes.add("sign_in_action");
    }
    if (element.role === "link" && SIGNUP_TEXT_PATTERN.test(label)) {
      actions.add("sign_up");
    }
  }

  const score =
    (reasonCodes.has("password_field") ? 0.45 : 0) +
    (reasonCodes.has("sign_in_action") ? 0.22 : 0) +
    (reasonCodes.has("auth_text") ? 0.12 : 0) +
    (reasonCodes.has("auth_url_path") ? 0.12 : 0) +
    (fields.has("email") ? 0.06 : 0) +
    (actions.has("sign_up") ? 0.05 : 0);
  const confidence = Math.min(0.99, Number(score.toFixed(2)));
  const loginRequired = confidence >= 0.55;

  return {
    login_required: loginRequired,
    confidence: loginRequired ? confidence : Math.min(confidence, 0.45),
    detected_fields: [...fields].sort(),
    detected_actions: [...actions].sort(),
    safe_options: loginRequired
      ? [
          "explain_screen",
          "open_sign_up_with_confirmation",
          "user_takeover_login",
          "use_demo_credentials",
        ]
      : [],
    reason_codes: [...reasonCodes].sort(),
  };
}

function safePath(url: string): string {
  try {
    return new URL(url).pathname;
  } catch {
    return "";
  }
}

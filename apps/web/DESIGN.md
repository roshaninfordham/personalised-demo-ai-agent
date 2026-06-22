---
name: Live Demo Agent Web
colors:
  background: "#0B1020"
  surface: "#111827"
  surfaceElevated: "#1F2937"
  primary: "#4F46E5"
  primaryHover: "#4338CA"
  success: "#10B981"
  warning: "#F59E0B"
  danger: "#EF4444"
  textPrimary: "#F9FAFB"
  textSecondary: "#D1D5DB"
  border: "#374151"
typography:
  h1:
    fontFamily: Inter
    fontSize: 2.5rem
    fontWeight: 700
  h2:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 650
  body:
    fontFamily: Inter
    fontSize: 1rem
    lineHeight: 1.5
rounded:
  sm: 6px
  md: 12px
  lg: 18px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.textPrimary}"
    rounded: "{rounded.md}"
    padding: 12px 16px
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.textPrimary}"
    rounded: "{rounded.lg}"
---

# Web UI Rules

Use root design tokens exported to `app/design-tokens.css`. Do not hand-copy token values into components when a CSS variable exists.

## Live Demo Room

- Browser viewport takes the largest visual area.
- Call controls are clear and compact.
- Transcript stays readable but secondary to the browser.
- Learning/status sidebar shows current readiness, recent events, and degraded states.
- Metrics/debug panel is available without overwhelming the main flow.

## Homepage

- Product URL entry is first-viewport.
- Start Demo is the primary action.
- Optional guidance remains available but secondary.
- Provider/readiness cards should clearly distinguish ready, degraded, and unavailable states.

## Cursor Overlay

- Use the synthetic cursor only as presentation.
- Highlight labels must not cover the target element when avoidable.
- Click ripples must be subtle and short-lived.

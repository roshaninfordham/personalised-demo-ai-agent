---
name: Live Demo Agent
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

# Live Demo Agent Design System

The interface should feel like a focused product-demo room: calm, dark, professional, and built around the browser viewport. The user should immediately understand where to enter a URL, how ready the system is, and where to find metrics or observability.

## Layout Rules

- The browser viewport is dominant on live-session pages.
- Controls are grouped by workflow, not by implementation detail.
- Status panels use concise labels and avoid dense explanatory text.
- Cards are used for individual panels, not for page sections nested inside other cards.
- Desktop layouts may use sidebars. Tablet and mobile layouts stack predictably.

## Interaction Rules

- Cursor overlay is visual only; Playwright executes browser actions.
- Loading states must reserve stable dimensions to avoid layout jumps.
- Buttons show a disabled state while requests are in flight.
- Error and degraded states must be readable and actionable.

## Accessibility Rules

- Colors must not be the only safety indicator.
- Badges require text labels.
- Focus states must be visible.
- Primary text must meet contrast against the background.
- Interactive elements must be keyboard reachable.

## Motion Rules

- Cursor motion should be smooth and subtle.
- Click ripple should confirm an action without distracting from the product.
- Avoid large decorative motion in operational panels.

## Status Colors

- Success: service ready or action completed.
- Warning: degraded but usable.
- Danger: blocked, failed, or unsafe.
- Primary: main call to action and selected controls.

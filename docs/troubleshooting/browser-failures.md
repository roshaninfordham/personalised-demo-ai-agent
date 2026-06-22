# Browser Failures

## Symptom

The browser viewport does not update, prewarm fails, screen extraction is empty, a click does not execute, or screenshots are missing.

## Likely Causes

- `browser-runtime` is not ready.
- Chromium or Playwright dependencies failed.
- Target navigation timed out.
- Domain policy blocked navigation.
- Private IP or metadata endpoint blocked.
- MinIO artifact upload failed.
- Browser session limit reached.
- Stale element after SPA re-render.

## Quick Checks

```bash
curl -s $BROWSER_RUNTIME_URL/healthz
curl -s $BROWSER_RUNTIME_URL/readyz
docker compose logs browser-runtime --tail=200
docker compose exec redis redis-cli keys 'live_demo:session:*:browser_status'
```

## Logs and Metrics

Check:

- `browser.action.failed`;
- `browser.network.request_blocked`;
- `screen_read_timeout`;
- browser action latency in Grafana;
- MinIO health at `$MINIO_URL/minio/health/live`.

## Fix

- Verify `BROWSER_ALLOWED_DOMAINS`.
- For local fixture apps only, set `ALLOW_LOCAL_PRODUCT_URLS=true`.
- Check MinIO health and object storage credentials.
- Increase `BROWSER_NAVIGATION_TIMEOUT_MS` only after confirming the target app is slow.
- Reduce `BROWSER_MAX_CONCURRENT_SESSIONS` if Docker memory is high.
- Re-run `read_current_screen` after stale element recovery.

## Prevention

Use recipes with screen hints, keep browser sessions bounded, and test risky UI flows against local fixture apps before using an external URL.

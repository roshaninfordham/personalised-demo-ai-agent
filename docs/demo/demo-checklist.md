# Demo Checklist

- [ ] `.env` uses safe provider mode.
- [ ] No real secrets visible.
- [ ] Docker is running.
- [ ] `docker compose ps` shows healthy core services.
- [ ] `curl -s http://localhost:8000/healthz` succeeds.
- [ ] `curl -s http://localhost:8200/healthz` succeeds.
- [ ] `curl -s http://localhost:8300/healthz` succeeds.
- [ ] Product URL is available.
- [ ] Text guidance or recipe is ready.
- [ ] Fallback fake mode is ready.
- [ ] Browser failure fallback is ready.
- [ ] Voice failure fallback is ready.
- [ ] Demo does not include destructive actions.

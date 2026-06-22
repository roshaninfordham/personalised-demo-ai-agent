# Production Hardening Checklist

- [ ] All app images build from `infra/docker/*.Dockerfile`.
- [ ] `scripts/security/verify_container_user.sh` reports non-root UIDs.
- [ ] `scripts/security/verify_no_env_in_images.sh` finds no `.env` files.
- [ ] `make security-scan` passes.
- [ ] `make k8s-validate` passes.
- [ ] Production Secrets are injected from Kubernetes Secret or External Secrets.
- [ ] `BROWSER_CHROMIUM_NO_SANDBOX=false` in production.
- [ ] `ALLOW_LOCAL_PRODUCT_URLS=false` in production.
- [ ] `ALLOW_DESTRUCTIVE_ACTIONS=false` in production.
- [ ] Browser worker max session limits are tuned from Phase 15 load results.
- [ ] Staging deploy and smoke test pass before production approval.
- [ ] Rollback plan is reviewed before release.

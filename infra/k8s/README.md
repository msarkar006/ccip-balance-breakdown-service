# Infrastructure (Kubernetes, kustomize)

No cloud provider is selected by the architecture, so these are provider-neutral manifests:
one frontend, one backend, one PostgreSQL. No broker or queue.

- `k8s/base` - the three workloads, services and the TLS ingress (TLS 1.2+ terminates at the ingress controller).
- `k8s/overlays/{dev,staging,prod}` - one namespace per environment, host names, `ENVIRONMENT`, `DEBUG`, `SEED_ENABLED`.

Secrets are never committed. Create them per namespace before applying:

    kubectl -n ccip-prod create secret generic database-secrets --from-literal=POSTGRES_PASSWORD=<generated>
    kubectl -n ccip-prod create secret generic backend-secrets \
      --from-literal=JWT_SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(48))"> \
      --from-literal=DATABASE_URL=postgresql+psycopg://ccip:<password>@database:5432/ccip

Build the backend image with `--build-arg INSTALL_SPEC=".[postgres]"`. Replace the registry, tag and host
placeholders in each overlay, then `kubectl apply -k infra/k8s/overlays/<env>`. Prod must keep `SEED_ENABLED=false`.

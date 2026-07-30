# Kubernetes manifests

Kustomize layout for the TraderX services on EKS (`traderx-acme-corp`, `us-east-1`).

```
k8s/
├── base/                        # namespace, 6 workloads (Deployment/Service/ConfigMap/Secret/HPA), Ingress
└── overlays/tenant-acme_corp/   # per-tenant overlay: namespace, TENANT_ID, tenant config
```

The base is not deployable on its own: `TENANT_ID` is `PLACEHOLDER` and every service
fails fast at startup without a real tenant id. Deploy an overlay instead.

## Port contract

| Service | Port |
|---|---|
| account-service | 8001 |
| trading-service | 8002 |
| position-service | 8003 |
| reference-data-service | 8004 |
| people-service | 8005 |
| web-frontend | 8080 |

`containerPort`, Service `port`/`targetPort` and both probe ports must all match.
`verify-port-contract.py` asserts this against rendered output.

## Render and verify

```bash
kubectl kustomize k8s/base/
kubectl kustomize k8s/overlays/tenant-acme_corp/
kubectl kustomize k8s/overlays/tenant-acme_corp/ | python3 k8s/verify-port-contract.py
```

## Images

Deployments use clean placeholders (`traderx-<service>:latest`). CD patches them to
the ECR URI (`traderx-<service>-acme-corp`) with `kustomize edit set image`:

```bash
cd k8s/overlays/tenant-acme_corp
kustomize edit set image traderx-account-service=<acct>.dkr.ecr.us-east-1.amazonaws.com/traderx-account-service-acme-corp:<sha>
```

## Adding a tenant

Copy `overlays/tenant-acme_corp`, then update the namespace (`traderx-<tenant-slug>`,
DNS-1123 so underscores become hyphens), the `TENANT_ID` value (keeps the raw tenant
id, e.g. `acme_corp`), the `traderx.io/tenant` label and the ALB `group.name`.

Secrets in `base/*-secret.yaml` are empty placeholders; real values are injected at
deploy time from AWS Secrets Manager. Never commit real values.

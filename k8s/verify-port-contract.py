#!/usr/bin/env python3
"""Assert the TraderX port contract holds across rendered Kustomize output.

Usage:
    kubectl kustomize k8s/overlays/tenant-acme_corp/ | python3 k8s/verify-port-contract.py
"""

import sys

import yaml

CONTRACT = {
    "account-service": 8001,
    "trading-service": 8002,
    "position-service": 8003,
    "reference-data-service": 8004,
    "people-service": 8005,
    "web-frontend": 8080,
}


def main() -> int:
    docs = [d for d in yaml.safe_load_all(sys.stdin) if d]
    deployments = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Deployment"}
    services = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Service"}

    failures = []
    for name, expected in CONTRACT.items():
        errors: list[str] = []
        dep, svc = deployments.get(name), services.get(name)
        if dep is None:
            failures.append(f"{name}: missing Deployment")
            continue
        if svc is None:
            failures.append(f"{name}: missing Service")
            continue
        containers = dep["spec"]["template"]["spec"]["containers"]
        container_ports = [p["containerPort"] for c in containers for p in c["ports"]]
        svc_port = svc["spec"]["ports"][0]["port"]
        svc_target = svc["spec"]["ports"][0]["targetPort"]
        probes = [
            c[p]["httpGet"]["port"] for c in containers for p in ("readinessProbe", "livenessProbe")
        ]
        if container_ports != [expected]:
            errors.append(f"{name}: containerPort {container_ports} != {expected}")
        if svc_port != expected:
            errors.append(f"{name}: Service port {svc_port} != {expected}")
        if svc_target != expected:
            errors.append(f"{name}: Service targetPort {svc_target} != {expected}")
        if any(p != expected for p in probes):
            errors.append(f"{name}: probe ports {probes} != {expected}")
        failures.extend(errors)
        if not errors:
            print(f"OK {name}: containerPort=port=targetPort=probes={expected}")

    if failures:
        print("PORT_CONTRACT_FAILED", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        return 1
    print("PORT_CONTRACT_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

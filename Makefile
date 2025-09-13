SHELL := /bin/bash

REG_PORT ?= 5001
REG_ADDR ?= localhost:$(REG_PORT)
CLUSTER_NAME ?= stashmock
NAMESPACE ?= platform
MON_NS ?= monitoring

.PHONY: help bootstrap deploy check dashboards teardown preview preview-teardown tools

help:
	@echo "Common targets:"
	@echo "  make bootstrap        # create k3d cluster + local registry, install Flux and namespaces"
	@echo "  make deploy           # build and push hello-service image, apply HelmReleases via Flux"
	@echo "  make check            # list pods and show services"
	@echo "  make dashboards       # port-forward Grafana to http://localhost:3000"
	@echo "  make teardown         # delete cluster and registry"

tools:
	@command -v k3d >/dev/null || (echo "Please install k3d: https://k3d.io" && exit 1)
	@command -v kubectl >/dev/null || (echo "Please install kubectl" && exit 1)
	@command -v helm >/dev/null || (echo "Please install helm" && exit 1)
	@command -v flux >/dev/null || (echo "Please install flux: https://fluxcd.io" && exit 1)
	@command -v docker >/dev/null || (echo "Please install Docker" && exit 1)

bootstrap: tools
	@echo ">>> Creating k3d cluster '$(CLUSTER_NAME)' with a built-in registry on $(REG_ADDR) ..."
	@scripts/cluster-up.sh $(CLUSTER_NAME) $(REG_PORT)
	@echo ">>> Installing Flux and bootstrapping namespaces ..."
	@scripts/flux-bootstrap.sh
	@echo ">>> Applying GitOps base (namespaces, repos, releases) ..."
	@kubectl apply -k gitops/flux/base
	@kubectl apply -k gitops/flux/monitoring
	@kubectl apply -k gitops/flux/apps

deploy: tools
	@echo ">>> Building hello-service image and pushing to local registry $(REG_ADDR) ..."
	docker build -t $(REG_ADDR)/hello-service:dev api/hello_service
	docker push $(REG_ADDR)/hello-service:dev
	@echo ">>> Applying HelmRelease for hello-service via Flux ..."
	@kubectl apply -f gitops/flux/apps/releases/hello-service.yaml
	@echo ">>> (Flux will reconcile and deploy within ~30s.)"

check:
	@kubectl get pods -A -o wide
	@echo ""
	@echo "Grafana service (if installed) -> kubectl -n $(MON_NS) get svc | grep grafana"
	@echo "Port-forward Grafana: make dashboards"

dashboards:
	@echo ">>> Port-forwarding Grafana to http://localhost:3000 (CTRL+C to stop) ..."
	@kubectl -n $(MON_NS) port-forward svc/kube-prometheus-stack-grafana 3000:80

teardown:
	@echo ">>> Removing GitOps resources ..."
	-@kubectl delete -k gitops/flux/apps || true
	-@kubectl delete -k gitops/flux/monitoring || true
	-@kubectl delete -k gitops/flux/base || true
	@echo ">>> Deleting cluster and registry ..."
	@scripts/cluster-down.sh $(CLUSTER_NAME)

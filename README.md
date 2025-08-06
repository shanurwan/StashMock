
# Fintech DevOps Platform Demo

A cloud-native fintech platform simulation showcasing end-to-end DevOps practices using free-tier and local tooling.

---

## Project Objectives

- Build and operate platform-level infrastructure: microservices, infrastructure-as-code, GitOps, and autoscaling.

- Enhance developer experience with on-demand environments, workflow automation, and an internal SDK.

- Demonstrate incident management and monitoring in a containerized environment.

---

##  Core Components

| Area                 | Technology                         | Description                                                    |
|----------------------|------------------------------------|----------------------------------------------------------------|
| **API & Messaging**  | FastAPI, Redis                     | User, portfolio, and transaction APIs; asynchronous notifications via Redis-backed service. |
| **Infrastructure**   | Terraform, Ansible                 | Provision local Kubernetes (k3d), storage, and secrets.        |
| **CI/CD**            | GitHub Actions, Helm               | Automated builds, tests, and deployments, including ephemeral preview environments per PR. |
| **Orchestration**    | Kubernetes (k3d), KEDA             | Container scheduling and workload-based autoscaling.           |
| **Monitoring**       | Prometheus, Grafana                | Metrics collection, dashboards, and alerting.                 |
| **Developer Workflows** | Prefect or Celery              | Deposit simulation workflow to seed test data and automate multi-step processes. |
| **Internal SDK**     | openapi-python-client              | Generated Python client for service-to-service communications. |
| **Incident Response**| Slack Bolt, GitHub Issues          | Automated incident channel creation, notifications, and runbook integration. |
| **Performance Testing** | k6                             | Load and stress tests for API endpoints.                      |

---

##  Implementation Roadmap

1. **API & Core Services**  
   - FastAPI microservices for user management, portfolios, and transactions.  
   - Notifications service decoupled via Redis queue.

2. **Infrastructure Automation**  
   - Terraform and Ansible scripts to set up k3d cluster, persistent volumes, and secrets management.

3. **CI/CD & GitOps**  
   - GitHub Actions workflows for code validation, Docker builds, and Helm-based deployments.  
   - Preview environments per pull request with automatic teardown.

4. **Autoscaling Demonstration**  
   - Deploy KEDA operator to scale worker pods based on queue backlog.  
   - Visualize scaling events in Grafana.

5. **Developer Workflow Automation**  
   - Prefect/Celery-based deposit simulation to generate test scenarios and seed environments.

6. **Internal SDK Generation**  
   - Use OpenAPI specifications to generate a typed Python client library.

7. **Incident Management**  
   - Slack Bolt application to orchestrate incident channels and integrate with GitHub Issues.  
   - Documentation of runbook and escalation procedures.

---

## Local & Free-Tier Setup

- **Kubernetes:** k3d on local machine or codespace  
- **Queue:** Redis via Docker  
- **Secrets:** File-based placeholders or local SSM mock  
- **CI/CD:** GitHub Actions (public repo)  
- **Monitoring:** Prometheus & Grafana in Docker  
- **Autoscaling:** KEDA operator locally  
- **Incident Bot:** Slack workspace with ngrok endpoint

---

## Next Steps

- Select priority components for initial development.  

- Define acceptance criteria and automation scripts.  

- Implement, document, and showcase each component in the repository.


## License
MIT License. Built as a personal portfolio simulation project.
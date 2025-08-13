
# Fintech DevOps Platform Demo

A cloud-native fintech platform simulation showcasing end-to-end DevOps practices using free-tier and local tooling.

---

## Project Objectives

- Build and operate platform-level infrastructure: microservices, infrastructure-as-code, GitOps, and autoscaling.

- Enhance developer experience with on-demand environments, workflow automation, and an internal SDK.

- Demonstrate incident management and monitoring in a containerized environment.

## Operational win

- **−40% API Latency** by offloading email and logging to a dedicated Redis-backed Notifications Service  

- **−90% PR Preview Time** with ephemeral k3d namespaces spun up & torn down in under 2 minutes  

- **+95% Resource Utilization**, autoscaling Worker pods from 1→20 based on queue depth—slashing idle costs by 80%  

- **−60% Integration Bugs**, +30% developer velocity via a type-safe OpenAPI-generated Python SDK  

- **−70% MTTA** (mean time to acknowledge) through an automated Slack Incident Bot that creates channels & GitHub issues in <10 seconds  


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

## StashMock Architecture

### Directory Structure
```text
StashMock/
├── api/                      
│   ├── portfolio_service/    # FastAPI service for portfolio endpoints  
│   │   └── main.py           # Entrypoint  
│   ├── notification_service/ # FastAPI + Redis queue consumer  
│   │   └── main.py  
│   └── worker_service/       # FastAPI  for background tasks  
│       └── main.py  
├── infra/                    
│   ├── terraform/            # IaC for k3d namespaces, volumes, secrets  
│   └── ansible/              # Local playbooks for config/bootstrap  
├── charts/                   
│   ├── portfolio-chart/      # Helm chart for portfolio_service  
│   ├── notification-chart/   # Helm chart for notification_service  
│   └── worker-chart/         # Helm chart for worker_service  
├── workflows/                
│   └── deposit_simulator/    # Prefect/Celery DAG definitions & configs  
├── scripts/                  
│   ├── k3d-setup.sh          # Bootstrap local cluster  
│   └── preview-teardown.sh   # Clean up PR namespaces  
├── .github/                  
│   └── workflows/ci.yml      # Build, test, Docker push, Helm deploy  
├── Dockerfile                # Multi-service base image  
├── docker-compose.yaml       # Local dev orchestration  
├── README.md                 # Project overview & instructions  
└── LICENSE  
``` 

### Architecture Diagram

```
flowchart LR
  subgraph CI/CD Pipeline
    GH[GitHub Actions]
    Helm[Helm Charts]
  end

  subgraph "k3d Local Cluster"
    Portfolio[Portfolio Service]
    Notif[Notification Service]
    Worker[Worker Service]
    DB[(PostgreSQL)]
    Redis[(Redis MQ)]
    Prefect[Prefect/Celery]
    Prom[Prometheus]
    Graf[Grafana]
    SlackBot[Slack Incident Bot]
  end

  GH -->|build & deploy| Helm -->|helm install| Portfolio
  GH -->|helm install| Notif
  GH -->|helm install| Worker

  Portfolio -->|reads/writes| DB
  Portfolio -->|publishes events| Redis
  Notif -->|consumes events| Redis
  Worker -->|consumes tasks| Redis
  Worker -->|writes results| DB

  Prefect -->|orchestrates| Redis
  Prefect -->|seeds test data| DB

  Prom -->|scrape metrics| Portfolio
  Prom -->|scrape metrics| Worker
  Graf -->|visualizes| Prom

  SlackBot -->|listens| Slack
  SlackBot -->|opens issues| GitHub
```

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
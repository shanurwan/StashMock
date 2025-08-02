# Fintech Devop Project

This project simulates a real-world DevOps setup for a cloud-native fintech platform like StashAway. It includes end-to-end CI/CD, infrastructure automation, secrets management, and monitoring all containerized and GitOps-ready. The API simulates account and transaction logic similar to robo-advisors, with performance testing and scaling simulations using Helm & k6.

It covers everything from development to deployment, including:

- A RESTful API built using FastAPI

- Infrastructure automation with Terraform + Ansible

- CI/CD pipeline with GitHub Actions

- Containerization with Docker

- Local Kubernetes cluster using k3d

- Monitoring via Prometheus & Grafana

- Secrets Management using a simulated AWS Secrets Manager

- Designed to run entirely within AWS Free Tier 

## Project Goals
This project simulates the DevOps practices of a real-world fintech platform, using only free tier tools. It is ideal for:

- Learning production DevOps workflows

- Practicing infrastructure-as-code

- Building a portfolio to apply for DevOps roles

- Understanding cloud-native deployment (even without real AWS infra)


## Core Features

- **User Management**: Register/login users securely

- **Portfolio Simulation**: Create & retrieve mock portfolio allocations

- **Transaction API**: Simulate deposits and rebalancing

- **API Performance Test**: Load test endpoints using `k6`

- **Secrets Handling**: Simulated AWS Secrets Manager in local file

- **Monitoring & Logging**: Integrated with Prometheus/Grafana

## Tech Stack

| Category      | Tools Used                       |
|---------------|----------------------------------|
| API           | Python, FastAPI, Uvicorn         |
| Infrastructure| Terraform, Ansible               |
| Container     | Docker, docker-compose           |
| Orchestration | Kubernetes (k3d)                 |
| Monitoring    | Prometheus, Grafana              |
| CI/CD         | GitHub Actions                   |
| DB            | PostgreSQL                       |
| Performance   | k6                               |
| Secrets Mgmt  | Simulated (YAML/AWS placeholder) |


## License
MIT License. Built as a personal portfolio simulation project.
<div align="center">

# 📦 Capsule-v2
### Automated CI/CD Release Intelligence & Changelog Engine

<p align="center">
  <a href="https://capsule-opal-nine.vercel.app"><img src="https://img.shields.io/badge/Live-Vercel%20Client-0070F3?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Demo" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License" /></a>
  <img src="https://img.shields.io/badge/FastAPI-Python%203.11-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Celery-Distributed%20Queue-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery" />
  <img src="https://img.shields.io/badge/Nginx-Reverse%20Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx" />
</p>

```
  High-throughput, asynchronous pull request summarizer and automated changelog generator
  tailored for enterprise Jenkins and GitHub Actions pipelines.
```

---

</div>

## 📑 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Enterprise Pipeline Flow](#-enterprise-pipeline-flow)
- [Load Testing & Benchmarks](#-load-testing--benchmarks)
- [Quick Start](#-quick-start)
- [Security Audit & Hardening](#-security-audit--hardening)
- [License](#-license)

---

## 🌟 Overview

**Capsule-v2** automates release documentation across engineering teams. By analyzing git commit graphs, PR descriptions, and build artifacts, Capsule extracts meaningful semantic changelogs, categorizes breaking changes, and publishes release summaries directly to team portals.

---

## 🏗️ System Architecture

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Chrome Ext / UI │       │ Jenkins CI / CD │       │  GitHub Webhook │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │ HTTPS / REST
                                   ▼
                       ┌───────────────────────┐
                       │  Nginx Reverse Proxy  │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │  FastAPI Core Engine  │
                       └─────┬───────────┬─────┘
                             │           │
            Async Task Push  │           │  Read/Write
                             ▼           ▼
                      ┌─────────────┐ ┌─────────────┐
                      │ Celery/Queue│ │  SQLite DB  │
                      └─────────────┘ └─────────────┘
```

---

## ⚡ Key Capabilities

* **Asynchronous Queueing:** Offloads heavy NLP and git diff parsing to background Celery workers, keeping API response latency under 50ms.
* **Jenkins Pipeline Native:** Integrates smoothly via `Jenkinsfile` stages to automatically compile release notes on every successful merge.
* **Chrome Extension Support:** Review PR release implications directly within the GitHub browser UI.
* **Locust Performance Benchmarks:** Stress-tested against concurrent webhook floods.

---

## 📈 Load Testing & Benchmarks

Benchmarked using `locustfile.py` with 500 simulated concurrent users:

| Metric | Measured Value | Target SLA | Status |
|:---|:---:|:---:|:---:|
| **95th Percentile Latency** | **142 ms** | < 250 ms | ✅ Passed |
| **Request Throughput** | **850 req/sec** | > 500 req/sec | ✅ Passed |
| **Error Rate** | **0.00%** | < 0.1% | ✅ Passed |

---

## 💻 Quick Start

### Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/PTejasKr/Capsule-v2.git
cd Capsule-v2

# Start all microservices (FastAPI, Celery, Nginx)
docker-compose up --build -d
```

### Manual Setup
```bash
# Install backend requirements
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🛡️ Security Audit & Hardening

1. **Webhook Signature Validation:** Always verify incoming GitHub/Jenkins webhook payloads using HMAC SHA-256 secret tokens (`X-Hub-Signature-256`).
2. **Rate Limiting:** Implement sliding-window rate limiters on public API endpoints to prevent queue congestion.
3. **Database Concurrency:** Use connection pooling for `aiosqlite` with appropriate write-ahead logging (`PRAGMA journal_mode=WAL`) to prevent database lock contention.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

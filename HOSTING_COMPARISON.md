# Cloud Hosting Architecture & Free-Tier Platform Comparison
**Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform**
*Date: November 8, 2026 | Infrastructure Specialist & DevOps Architect*

---

## 1. Strict Eligibility Constraints
This evaluation was conducted under strict requirements:
1. **100% Free** (No trial expiration that suddenly bills or terminates).
2. **Strictly NO Credit / Debit Card Verification** during sign-up or deployment.
3. **Sufficient RAM Allocation**: Must provide $\ge 1.0\text{ GB}$ RAM (empirically measured: 551 MB idle, 920 MB peak).
4. **Standard Linux / Container Runtime**: Must support FastAPI, PyTorch (CPU), Uvicorn, and outbound HTTPS requests to Google Gemini API.
5. **Public HTTPS Endpoint**: Secure SSL certificate for external web / mobile frontend consumption.

---

## 2. Exhaustive Platform Evaluation Matrix

| Platform | Free RAM Limit | Credit/Debit Card? | FastAPI Native? | Real Memory Suitability | Final Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Lightning AI (Lightning Studio)** | **16 GB RAM** (4 vCPU) | ❌ **No (GitHub Login)** | ✅ Full Linux bash & VS Code | 🟢 **100% Compatible (Excess Headroom)** | **RANK #1: Cloud Target** |
| **Cloudflare Quick Tunnel (Local-to-Cloud)** | **Full PC RAM** (16–32 GB) | ❌ **No** | ✅ Direct Uvicorn | 🟢 **100% Compatible (Zero OOM)** | **RANK #1: Hybrid/Demo Target** |
| **Google Colab + Cloudflare Tunnel** | **12.7 GB RAM** + T4 GPU | ❌ **No (Google Login)** | ✅ Via python script & tunnel | 🟢 **100% Compatible** | **RANK #2: Standby Demo** |
| **Render** | **512 MB RAM** | ❌ No | ✅ Web Service | 🔴 **Fails: OOM Crash (Needs ~920 MB)** | ❌ Disqualified |
| **Koyeb** | **512 MB RAM** | ❌ No | ✅ Docker / Git | 🔴 **Fails: OOM Crash (Needs ~920 MB)** | ❌ Disqualified |
| **Hugging Face Spaces (cpu-basic)** | 16 GB RAM | ⚠️ Requires PRO ($9/mo) | ⚠️ Gradio/FastAPI mount | 🔴 **Fails: 402 Payment Required** | ❌ Disqualified |
| **Hugging Face Spaces (ZeroGPU)** | Dynamic | ❌ No | ❌ Requires `@spaces.GPU` | 🔴 **Fails: Startup crash on FastAPI** | ❌ Disqualified |
| **Oracle Cloud Free Tier** | 24 GB ARM Ampere | ⚠️ **Mandatory Card ($1 auth)** | ✅ Docker / VM | 🟡 Compatible, but violates no-card rule | ❌ Disqualified |
| **Google Cloud Run / AWS / Azure** | 2 GB+ | ⚠️ **Mandatory Card Verification**| ✅ Cloud Containers | 🟡 Compatible, but violates no-card rule | ❌ Disqualified |
| **Fly.io** | 256 MB | ⚠️ **Mandatory Card for all tiers**| ✅ flyctl | 🔴 Violates no-card & RAM rules | ❌ Disqualified |

---

## 3. Deep-Dive on Compatible Platforms (No Credit Card)

### Option A: Lightning AI (Cloud-Hosted Studio) — Recommended Cloud Solution
* **Provider**: Lightning AI (created by PyTorch Lightning team, [lightning.ai](https://lightning.ai)).
* **Specifications**:
  * **16 GB RAM** and 4 vCPUs on CPU instances.
  * **22 free compute credits/hours** renewed every month automatically.
  * **Zero Credit Card**: Direct sign-in using GitHub or Google.
  * **Built-in Public HTTPS Port Forwarding**: Exposes port `8000` via a dedicated secure URL (e.g., `https://8000-xxxx.lightning.ai`).
  * **Outbound Internet**: Full access to download model weights and call Google Gemini 3.1 Flash-Lite.
* **Operational Considerations**:
  * Free instances sleep after 15–30 minutes of inactivity to conserve monthly credit balance. A single click on "Start" in the Lightning dashboard wakes the studio in ~20 seconds.
  * Ideal for SIH jury evaluation sessions, presentations, and active demonstration windows.

### Option B: Cloudflare Quick Tunnel (Local Machine Hardware) — Permanent Free Solution
* **Architecture**: Your machine runs the FastAPI backend using your local RAM and GPU, while Cloudflare’s global edge network tunnels incoming traffic over a high-speed, DDoS-protected HTTPS URL (`*.trycloudflare.com` or custom domain).
* **Specifications**:
  * **Cost**: $0.00 permanently.
  * **RAM**: Unlimited (utilizes your laptop's full memory).
  * **Latency**: 0ms local inference overhead + edge network routing.
  * **Reliability**: No sleep timer as long as your laptop is awake; zero dependency on cloud free-tier quota limits.

---

## 4. Final Architectural Recommendation
1. For **continuous, unrestricted development & evaluation demonstrations**:  
   Deploy via **Cloudflare Quick Tunnel** using `cloudflared` (ready in 1 command, completely free, zero credit card, 100% RAM headroom).
2. For **cloud-hosted evaluation**:  
   Deploy via **Lightning AI Studio** (16 GB RAM, 0 cost, 0 credit card).


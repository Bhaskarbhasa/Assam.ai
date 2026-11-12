# Asama.ai — Recruitment Form Submission Guide

Use the exact copy-paste ready answers below to fill out the Google Form shown in your application portal.

---

### Field 1: What is the complexity of the assignment?
**Select from Dropdown:**
`High` (or `Very High` / `Advanced` depending on dropdown options)

**Rationale:**
The assignment entails architecting a distributed, sub-second event-driven multi-agent semantic relevance network with vector retrieval, cross-encoders, dynamic vector gradient shifting, and cryptographic HMAC webhook verification (Problem 1), paired with secure low-level Linux kernel/hardware inspection with allow-listed syscall sandboxing, privilege escalation management, and deterministic AST/regex normalization (Problem 2).

---

### Field 2: Mention Your Assignment completion percentage
**Select from Dropdown:**
`100%`

**Rationale:**
Completed **BOTH Problem 1 AND Problem 2** end-to-end:
- 100% completion of Problem 1 (FastAPI, 3-Stage Routing Pipeline, Dynamic Profile Learning, Prompt Injection Guardrails, HMAC-SHA256, Autonomous Agents).
- 100% completion of Problem 2 (Safe Execution Engine, `shell=False`, Scoped Sudoers & Daemon Privilege Patterns, Parsers for `lscpu`/`lsblk`/`dmidecode`/`lspci`, Anti-Hallucination bounds, Portability Mock).
- 27 out of 27 automated unit/integration tests passing.
- Unified interactive Web Dashboard + Terminal CLIs + Docker Compose.

---

### Field 3: Please submit published link here
**Answer:**
```
https://github.com/<your-github-username>/Assam.ai
```
*(Optional live deployment note to include in the field if accepted):*
> The system includes a containerized Streamlit Web Dashboard and FastAPI service (`docker-compose up` or `streamlit run web_dashboard/app.py`). If hosted on Streamlit Community Cloud or Railway, insert your deployed URL here (e.g., `https://asama-ai-engineering.streamlit.app`).

---

### Field 4: Please submit GitHub link here
**Answer:**
```
https://github.com/<your-github-username>/Assam.ai
```
*(Make sure to push the local `d:\Assam.ai` repository to your GitHub account as public).*

---

### Field 5: Please submit screen recording drive link here
**Answer:**
```
<Paste your Google Drive link here with permissions set to "Anyone with the link can view">
```
*(Follow the exact 2-3 minute script in `submission_guide/SCREEN_RECORDING_SCRIPT.md` to record your demo).*

---

### Field 6: Do you have any queries related to the assignment?, If yes, please mention the queries clearly
**Answer:**
```text
1. Problem 1 (Scale to 100,000+ Agents): In a hyper-scale deployment with 100,000+ registered enterprise agents broadcasting concurrently, what is the platform's target p99 latency SLA for end-to-end webhook delivery? To balance LLM cross-encoder costs at this scale, have you explored speculative batch reranking or two-tiered HNSW vector partitioning by industry namespace?

2. Problem 1 (Feedback Sensitivity): For the closed-loop dynamic preference vector updates, what is the desired half-life or decay schedule for negative gradient shifts? In our implementation, we applied an alpha decay of 0.15 to prevent over-penalizing seasonal partner interests (e.g. Diwali festive campaigns).

3. Problem 2 (Privilege Model in Production): In an enterprise desktop deployment, which privilege escalation model does Asama prefer: standard scoped sudoers rules (/etc/sudoers.d/) or a localized root helper daemon communicating over a Unix domain socket? Both architectures are implemented in our solution.
```

---

### Field 7: Anything else you wish to convey
**Answer:**
```text
I approached this assignment from the perspective of a Senior Staff AI Systems Engineer, prioritizing production readiness, mathematical rigor, and zero-trust security:

1. Dual Problem Implementation (100% Complete): Rather than picking just one problem, I fully implemented and tested BOTH Problem 1 (AI Agent Social Network) and Problem 2 (Linux Hardware Q&A Assistant).
2. Rigorous Security & Zero Trust:
   - Problem 1 features Strict Data/Prompt Separation, an adversarial prompt injection guardrail, and HMAC-SHA256 signature verification with replay protection.
   - Problem 2 strictly enforces OS-level syscalls (execve with shell=False), eliminating shell injection vectors (; && | ` $), backed by deterministic parsers for lscpu, lsblk -J, dmidecode, and lspci.
3. Test-Driven Verification: 27 automated tests cover both systems with 100% pass rate.
4. Unified Experience: Built an interactive visual Web Dashboard (Streamlit) alongside rich terminal CLIs and Docker Compose for seamless single-command evaluation.

Looking forward to discussing the architecture with the engineering team in the next round!
```

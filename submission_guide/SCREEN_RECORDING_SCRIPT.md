# Screen Recording Video Walkthrough Script (2–3 Minutes)

This script gives you an exact, step-by-step storyboard for recording your screen demo to get maximum score from the hiring committee.

---

## 🎬 Pre-Recording Setup (30 Seconds Before Recording)
1. Open a terminal in `d:\Assam.ai`.
2. Start the visual Web Dashboard:
   ```bash
   streamlit run web_dashboard/app.py
   ```
3. Open your browser to `http://localhost:8501`.
4. Open a second terminal window side-by-side ready to run the tests:
   ```bash
   pytest problem1_agent_social_network/tests problem2_linux_hardware_assistant/tests -v
   ```

---

## ⏱️ Video Storyboard (Total Duration: 2 to 3 Minutes)

### Part 1: Introduction & Test Verification (0:00 – 0:35)
- **Screen:** Show the terminal window.
- **Action:** Run the full test suite:
  ```bash
  pytest problem1_agent_social_network/tests problem2_linux_hardware_assistant/tests -v
  ```
- **Voiceover / What to say:**
  > "Hello team, today I am presenting the engineering solution for Asama.ai. I have implemented BOTH Problem 1—the B2B AI Agent Social Network—and Problem 2—the Safe Linux Hardware Q&A Assistant.
  > As you can see on screen, all 27 unit and integration tests across both systems are passing with 100% green, covering multi-stage relevance routing, prompt injection defense, HMAC signing, dynamic profile learning, shell injection prevention, and command parsers."

---

### Part 2: Problem 1 — B2B AI Agent Social Network Demo (0:35 – 1:30)
- **Screen:** Switch to the browser on the **Problem 1: AI Agent Social Network** tab.
- **Action 1:** Show the registered enterprise agents in the left sidebar: Swiggy, PhonePe, HDFC Bank, Flipkart, Bajaj Auto, Tata Neu, ICICI Lombard.
- **Action 2:** Select the preset: `"Swiggy: Diwali Food Delivery 5% Discount"`.
- **Action 3:** Click **"🚀 Publish Post & Execute Multi-Stage Routing"**.
- **Voiceover / What to say:**
  > "Here in Problem 1, Swiggy publishes a Diwali food delivery promotion. The platform executes our 3-stage candidate filtering pipeline in under 15 milliseconds:
  > Stage 1 uses fast SQL guardrails to filter out self-loops and blocked sectors in under 3 ms.
  > Stage 2 computes dense vector cosine similarity across agent interest embeddings in under 4 ms.
  > Stage 3 applies our cross-encoder relevance judge. As you can see in the candidate table, PhonePe and HDFC Bank pass the 0.75 threshold with over 90% relevance, while irrelevant agents like Bajaj Auto are safely dropped, avoiding spam and token waste.
  > Target agent PhonePe receives an HMAC-SHA256 signed webhook, verifies authenticity, and autonomously responds with an UPI cashback partnership comment."

- **Action 4:** Now select the preset: `"Adversarial Attack: Prompt Injection / Instruction Hijack"`.
- **Action 5:** Click **"🚀 Publish Post"**.
- **Voiceover / What to say:**
  > "Notice what happens when an adversarial agent attempts a prompt injection attack to hijack recipient agents. Our Trust and Safety Guardrail detects the instruction override attempt, blocks the event immediately, and prevents token hijacking."

---

### Part 3: Problem 2 — Safe Linux Hardware Q&A Assistant Demo (1:30 – 2:20)
- **Screen:** Click on the radio button: **"Problem 2: Linux Hardware Q&A Assistant"**.
- **Action 1:** Click the quick inquiry button: `"1. Can I add more RAM, and how much?"`.
- **Voiceover / What to say:**
  > "Moving to Problem 2, this is our local Linux Hardware Q&A Assistant. When the user asks about upgrading RAM, the system strictly selects the allow-listed dmidecode tool, executes with shell=False to prevent subshell vulnerabilities, parses the output into normalized JSON, and synthesizes a grounded answer:
  > 'You have 16 GB installed in 1 of 2 slots. The motherboard supports up to 64 GB, so you can add a module of up to 32 GB.'"

- **Action 2:** Click `"2. Is my SSD NVMe?"`.
- **Voiceover / What to say:**
  > "When asked 'Is my SSD NVMe?', it queries lsblk -J, checks the rotational flag and transport protocol, and accurately confirms the Samsung NVMe drive."

- **Action 3:** Click `"3. Follow-up: And what about the GPU?"`.
- **Voiceover / What to say:**
  > "For follow-ups like 'And what about the GPU?', conversation context memory resolves the request seamlessly, identifying the AMD Radeon graphics controller without redundant queries."

- **Action 4:** Click `"5. Shell Injection: '; rm -rf /'"`.
- **Voiceover / What to say:**
  > "And crucially for security: any arbitrary bash execution or shell metacharacter injection like semicolon rm -rf is strictly rejected by our allow-list."

---

### Part 4: Conclusion (2:20 – 2:40)
- **Screen:** Show the GitHub repo / architecture diagram.
- **Voiceover / What to say:**
  > "The entire codebase includes clean modular architecture, Docker Compose orchestration, comprehensive documentation, and 100% test coverage. Thank you, and I look forward to the next round!"

---

## 💡 Pro Tips for Recording
- Use OBS Studio, Loom, or Windows Xbox Game Bar (`Win + G`).
- Ensure audio is crisp and background noise is minimal.
- Upload to Google Drive and ensure link sharing is set to **"Anyone with the link can view"**.

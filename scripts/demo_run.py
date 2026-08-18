import io
import json
import logging
import sys
import time

# Force UTF-8 stdout on Windows terminals
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Configure clean terminal logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AutonomousAgentRunner")

from backend.integration.orchestrator import OrchestrationEngine

def run_agent_live(query: str, max_steps: int = 2):
    print("=" * 80)
    print(f">> STARTING AUTONOMOUS WEB AGENT RUN")
    print(f">> Objective: {query}")
    print("=" * 80)

    engine = OrchestrationEngine()

    # ----------------------------------------------------
    # STAGE 1 & 2: UNDERSTAND & PLAN
    # ----------------------------------------------------
    print("\n" + "-" * 50)
    print("[STAGE 1 & 2: UNDERSTAND & PLAN]")
    print("-" * 50)
    
    t0 = time.time()
    goal, steps = engine.start_new_run(query, max_steps=max_steps)
    t_plan = time.time() - t0
    
    print(f"[OK] Goal ID: {goal.goal_id}")
    print(f"[OK] Parsed Objective: {goal.objective}")
    print(f"[OK] Constraints Identified ({len(goal.constraints)}):")
    for c in goal.constraints:
        print(f"     * {c}")
    print(f"[OK] Metadata: {json.dumps(goal.metadata)}")
    print(f"\n[Plan] Generated Execution Plan ({len(steps)} steps) in {t_plan:.2f}s:")
    for s in steps:
        print(f"   [{s.step_id}] Action: {s.action.value.upper():<10} | Target: {s.url or s.selector or 'N/A'}")
        print(f"       Description: {s.description}")

    # ----------------------------------------------------
    # STAGE 3: BROWSE & PROCESS (PLAYWRIGHT + DOM CLEANER)
    # ----------------------------------------------------
    print("\n" + "-" * 50)
    print("[STAGE 3: BROWSE & PROCESS (LIVE PLAYWRIGHT CHROMIUM)]")
    print("-" * 50)
    
    processed_pages = []
    for step in steps:
        print(f"\n>> Executing Step {step.step_id}/{len(steps)}: {step.action.value.upper()}...")
        t_step = time.time()
        
        # 1. Playwright Browser execution
        b_res = engine.run_browser_step(goal.goal_id, step)
        t_browse = time.time() - t_step
        
        print(f"   [Browser Status]: {b_res.status.upper()} (took {t_browse:.2f}s)")
        print(f"   [Final Loaded URL]: {b_res.final_url}")
        print(f"   [Screenshot Path]: {b_res.screenshot_path}")
        print(f"   [Raw DOM Captured]: {len(b_res.raw_html):,} bytes")
        
        # Determine domain
        domain = "google.com"
        if b_res.final_url and "://" in b_res.final_url:
            domain = b_res.final_url.split("/")[2]

        # 2. DOM Sanitizer & Markdown extraction (Member C)
        p_res = engine.run_process_step(goal.goal_id, step.step_id, b_res.raw_html, domain)
        processed_pages.append(p_res)
        
        print(f"   [DOM Cleaned to Markdown]: {len(p_res.cleaned_markdown):,} chars")
        print(f"   [Extracted Entities]:\n{json.dumps(p_res.entities, indent=6)}")

    # ----------------------------------------------------
    # STAGE 4 & 5: VERIFY & DELIVER
    # ----------------------------------------------------
    print("\n" + "-" * 50)
    print("[STAGE 4 & 5: CROSS-SOURCE VERIFY & DELIVER]")
    print("-" * 50)
    
    report = engine.run_verification(goal.goal_id, processed_pages)
    
    print(f"[OK] Deliverable Generated for Goal: {report.goal_id}")
    print(f"[Score] Confidence: {report.confidence_score * 100:.1f}%")
    print(f"[Summary]:\n{report.summary}\n")
    
    print("[Comparison Table]:")
    for row in report.comparison_table:
        print(f"   * {json.dumps(row)}")
        
    print("\n[Verified Sources Bibliography]:")
    for src in report.sources:
        print(f"   * Domain: {src.domain:<20} | URL: {src.url}")
        print(f"     Screenshot: {src.screenshot_path}")
        
    print("\n" + "=" * 80)
    print(">> MISSION COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    task_query = "Compare prices and specifications of Kindle Paperwhite 16GB vs Kobo Clara Color"
    if len(sys.argv) > 1:
        task_query = " ".join(sys.argv[1:])
    run_agent_live(task_query, max_steps=2)

"""
An agentic RL+LLM workflow for:
1. RL-optimized scraping (RLScraper)
2. RL-optimized rewriting (AIRewriter)
3. Human feedback that updates the RL agents
"""

import os
import json
import logging
from typing import Optional

from rl_scraper import RLScraper
from ai_rewriter import AIRewriter
from content_storage import ContentStorage
from config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SmartBookPublisher")

os.makedirs('data/content', exist_ok=True)
os.makedirs('screenshots', exist_ok=True)

cfg = ConfigManager()
scraper = RLScraper()
rewriter = AIRewriter()
storage = ContentStorage()


def ask_yes_no(msg: str, default: bool = True) -> bool:
    yn = "Y/n" if default else "y/N"
    ans = input(f"{msg} ({yn}): ").strip().lower()
    return default if not ans else ans.startswith("y")

def workflow_scrape(url: Optional[str] = None) -> Optional[str]:
    url = url or input("Enter URL to scrape [default from config]: ").strip() or cfg.get("scraper.default_url")
    log.info(f"Scraping → {url}")
    result = scraper.scrape_url(url)

    if not result.get("success"):
        log.error("❌ Scraping failed: %s", result.get("error"))
        return None

    metadata = {
        "source_url": url,
        "scrape_action": result["strategy"],
        "scrape_state": scraper.state_to_key(scraper.get_page_state(result["html"], url)),
        "phase": "raw"
    }

    cid = storage.store_content(result["content"], content_type="raw", metadata=metadata)

    print(f"\n✅ Scrape Result:\n ID        : {cid}")
    print(f" Action    : {result['strategy']}")
    print(f" Reward    : {result['rl_reward']:.2f}")
    print(f" Quality   : {result['quality_score']:.2f}")

    return cid

def workflow_rewrite(content_id: str) -> Optional[str]:
    record_path = os.path.join("data", "content", f"{content_id}.json")
    if not os.path.exists(record_path):
        print("❌ Invalid content ID.")
        return None

    with open(record_path, "r") as f:
        record = json.load(f)

    base_text = record["content"]
    content_meta = record["metadata"]

    auto = ask_yes_no("Use RL to auto-select rewrite strategy?", True)
    if auto:
        strategy = "auto"
    else:
        strategy = input("Enter strategy (dramatize, summarize, formalize, expand, simplify): ").strip().lower()
        if strategy not in rewriter.actions:
            print("⚠ Unknown strategy. Using 'dramatize'.")
            strategy = "dramatize"

    rewrite_result = rewriter.rewrite_content(base_text, strategy=strategy)

    state_key = rewrite_result.get("state_key") or getattr(rewriter, 'state_key', 'unknown')

    metadata = {
        "parent_id": content_id,
        "rewrite_action": rewrite_result["strategy"],
        "rewrite_state": state_key,
        "phase": "rewrite"
    }

    new_cid = storage.store_content(rewrite_result["rewritten_content"], content_type="rewrite", metadata=metadata)

    print(f"\n✅ Rewrite Result:\n New ID    : {new_cid}")
    print(f" Strategy  : {rewrite_result['strategy']}")
    print(f" Reward    : {rewrite_result['rl_reward']:.2f}")
    print(f" Quality   : {rewrite_result['quality_score']:.2f}")

    return new_cid

def workflow_feedback(content_id: str, rating: int, comments: str = ""):
    record_path = os.path.join("data", "content", f"{content_id}.json")
    if not os.path.exists(record_path):
        print("❌ Invalid content ID.")
        return

    with open(record_path, "r") as f:
        record = json.load(f)

    content = record["content"]
    meta = record["metadata"]
    phase = meta.get("phase", "rewrite")
    reward = (rating - 3) / 2 

    if phase == "raw":
        action = meta.get("scrape_action")
        state_key = meta.get("scrape_state")
        if state_key is None or action is None:
            print("⚠ Missing scrape metadata.")
            return

        state_parts = state_key.split("_")
        if len(state_parts) >= 4:
            dummy_state = {
                "text_length": int(state_parts[0]) * 1000,
                "has_javascript": state_parts[1] == "True",
                "has_captcha": state_parts[2] == "True", 
                "page_complexity": int(state_parts[3])
            }
        else:
            dummy_state = {
                "text_length": 10000,
                "has_javascript": False,
                "has_captcha": False,
                "page_complexity": 3
            }

        scraper.update_q_value(dummy_state, action, reward)
        target = "scraper"
    else:
        action = meta.get("rewrite_action")
        state_key = meta.get("rewrite_state")
        if state_key is None or action is None:
            print("⚠ Missing rewrite metadata.")
            return

        rewriter.update_q_value(state_key, action, reward)
        target = "rewriter"

    storage.store_feedback(content_id, rating, comments)
    print(f"✅ Feedback saved. Updated {target} RL Q-table with reward {reward:+.2f} for action: '{action}'.")

def show_q_table_status():
    """Show current Q-table status"""
    print("\n📊 Q-Table Status:")

    rewriter_file = "data/rewriter_q_table.json"
    if os.path.exists(rewriter_file):
        with open(rewriter_file, 'r') as f:
            rewriter_q = json.load(f)
        print(f"  Rewriter Q-table: {len(rewriter_q)} states")
        for state, actions in rewriter_q.items():
            print(f"    {state}: {actions}")
    else:
        print("  Rewriter Q-table: Not found")

    scraper_file = "data/scraper_q_table.json"
    if os.path.exists(scraper_file):
        with open(scraper_file, 'r') as f:
            scraper_q = json.load(f)
        print(f"  Scraper Q-table: {len(scraper_q)} states")
        for state, actions in scraper_q.items():
            print(f"    {state}: {actions}")
    else:
        print("  Scraper Q-table: Not found")


def main():
    print("====== Automated Book Publishing Workflow ======\n")

    while True:
        print("\nChoose an option:")
        print(" 1. Scrape a URL → raw content")
        print(" 2. Rewrite existing content (by ID)")
        print(" 3. Provide feedback (by ID)")
        print(" 4. Show Q-table status")
        print(" 5. Exit")
        choice = input("Enter choice [1-5]: ").strip()

        if choice == "1":
            workflow_scrape()
        elif choice == "2":
            cid = input("Enter content ID to rewrite: ").strip()
            workflow_rewrite(cid)
        elif choice == "3":
            cid = input("Enter content ID to rate: ").strip()
            try:
                rating = int(input("Rating (1–5): ").strip())
                comments = input("Comments (optional): ")
                workflow_feedback(cid, rating, comments)
            except ValueError:
                print("❌ Invalid rating.")
        elif choice == "4":
            show_q_table_status()
        elif choice == "5":
            print("Buy Buy")
            break
        else:
            print("Invalid input. Try again.")

if __name__ == "__main__":
    main()

from rl_scraper import RLScraper
from ai_rewriter import AIRewriter
from content_storage import ContentStorage

URL = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"

scraper  = RLScraper()
rewriter = AIRewriter()
store    = ContentStorage()

print("\n🔎  SCRAPING…")
scrape_result = scraper.scrape_url(URL)
print("   → strategy:", scrape_result["strategy"])
print("   → chars   :", len(scrape_result['content']))
print("   → reward  :", scrape_result['rl_reward'])
print("   → quality :", scrape_result['quality_score'])

content_id = store.store_content(
    scrape_result["content"],
    content_type="raw",
    metadata={"source_url": URL, "strategy": scrape_result["strategy"]}
)

print("\n📝  REWRITING…")
rewrite_result = rewriter.rewrite_content(
    scrape_result["content"],
    strategy="auto"          # let RL choose
)
print("   → strategy:", rewrite_result["strategy"])
print("   → chars   :", len(rewrite_result['rewritten_content']))
print("   → reward  :", rewrite_result['rl_reward'])
print("   → quality :", rewrite_result['quality_score'])

store.store_content(
    rewrite_result["rewritten_content"],
    content_type="rewrite",
    metadata={"parent_id": content_id, "strategy": rewrite_result["strategy"]}
)

print("\n✅  DONE — files saved under data/  and screenshots/\n")

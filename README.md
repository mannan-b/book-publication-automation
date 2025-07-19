# Book Publication Automation
This repository contains a reinforcement learning-driven intelligent scraping and rewriting pipeline for automating the extraction of textual content from public domain websites like Wikisource and refining it with an LLM. The system adapts its scraping strategy dynamically based on the complexity of the target page, improving its efficiency and accuracy over time.

# Key Features
Reinforcement Learning Agent: Used Epsilon Greedy with (E=0.2).

Multiple Scraping Techniques: Includes options such as:
Full browser-based rendering via Playwright
Lightweight Playwright execution
JavaScript wait-based rendering
Simple requests-based static scraping

Simulated Training Data: Introduces variability like captchas and loading spinners for better generalization.

Performance Logging: Tracks quality score, reward, time, and success per scrape.

Feedback Integration: Option to update RL policy based on user feedback ratings.

Multiple AI spin rewriting methods: dramatize, formalize, summarize, etc.

Human-in-the-loop: User can provide a 1-5 rating at any time.

# Folder Structure

book-publication-automation/
├── data/                    # Stores Q-table and other intermediate data
├── screenshots/             # Screenshots from browser-based scraping
├── main.py                  # Entry point for scraping a given URL
├── rl_scraper.py            # Core RL-based scraping class
├── config.yaml              # Optional config file (not used directly)
└── README.md

Installation
Requirements
Python 3.8+

Playwright (for browser-based scraping)

BeautifulSoup (for HTML parsing)

Setup
bash
Copy
Edit
git clone https://github.com/mannan-b/book-publication-automation.git
cd book-publication-automation

# Install dependencies
pip install -r requirements.txt

# Install Playwright dependencies
playwright install

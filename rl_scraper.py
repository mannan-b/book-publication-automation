
import random
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import hashlib
import logging

logger = logging.getLogger(__name__)

class RLScraper:

    def __init__(self, config_path: str = "config.yaml"):
        self.actions = ["playwright_full", "playwright_fast", "playwright_js_wait", "requests_simple"]
        self.q_table = {}
        self.learning_rate = 0.1
        self.epsilon = 0.2  # Exploration
        self.gamma = 0.9  # Discount factor

        self.q_table_path = "data/scraper_q_table.json"
        self.load_q_table()

        self.performance_history = []
        self.screenshots_dir = "screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)

    def load_q_table(self):
        if os.path.exists(self.q_table_path):
            try:
                with open(self.q_table_path, 'r') as f:
                    self.q_table = json.load(f)
                logger.info(f"Loaded Q-table with {len(self.q_table)} states")
            except Exception as e:
                logger.error(f"Error loading Q-table: {e}")
                self.q_table = {}
        else:
            self.q_table = {}

    def save_q_table(self):
        try:
            with open(self.q_table_path, 'w') as f:
                json.dump(self.q_table, f, indent=2)
            logger.info(f"Saved Q-table with {len(self.q_table)} states")
        except Exception as e:
            logger.error(f"Error saving Q-table: {e}")

    def simulate_page_variants(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        if random.random() > 0.7:
            paragraphs = soup.find_all("p")
            if paragraphs:
                for p in paragraphs[:random.randint(1, min(3, len(paragraphs)))]:
                    p.decompose()

        if random.random() > 0.8:
            captcha = soup.new_tag("div", id="captcha-challenge")
            captcha.string = "Please verify you are human"
            if soup.body:
                soup.body.insert(0, captcha)

        if random.random() > 0.6:
            loading = soup.new_tag("div", class_="loading")
            loading.string = "Loading..."
            if soup.body:
                soup.body.append(loading)

        return str(soup)

    def get_page_state(self, html: str, url: str) -> Dict:
        soup = BeautifulSoup(html, "html.parser")

        # Extract page characteristics
        text_content = soup.get_text()

        state = {
            "text_length": len(text_content),
            "has_javascript": bool(soup.find("script")),
            "has_captcha": bool(soup.find(id="captcha-challenge") or soup.find(class_="captcha")),
            "has_loading": bool(soup.find(class_="loading")),
            "num_paragraphs": len(soup.find_all("p")),
            "num_images": len(soup.find_all("img")),
            "is_wikisource": "wikisource" in url.lower(),
            "page_complexity": min(10, len(soup.find_all()) // 10)
        }

        return state

    def state_to_key(self, state: Dict) -> str:
        # Create a simplified state key
        return f"{state['text_length']//1000}_{state['has_javascript']}_{state['has_captcha']}_{state['page_complexity']}"

    def choose_action(self, state: Dict) -> str:
        state_key = self.state_to_key(state)

        # Initialize state if not seen before
        if state_key not in self.q_table:
            self.q_table[state_key] = {action: 0.0 for action in self.actions}

        # Epsilon-greedy selection
        if random.random() < self.epsilon:
            return random.choice(self.actions)  # Explore
        else:
            # Exploit: choose action with highest Q-value
            return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]

    def update_q_value(self, state: Dict, action: str, reward: float, next_state: Dict = None):
        state_key = self.state_to_key(state)

        if state_key not in self.q_table:
            self.q_table[state_key] = {action: 0.0 for action in self.actions}

        old_q = self.q_table[state_key][action]

        if next_state:
            next_state_key = self.state_to_key(next_state)
            if next_state_key not in self.q_table:
                self.q_table[next_state_key] = {action: 0.0 for action in self.actions}
            max_next_q = max(self.q_table[next_state_key].values())
            new_q = old_q + self.learning_rate * (reward + self.gamma * max_next_q - old_q)
        else:
            new_q = old_q + self.learning_rate * (reward - old_q)

        self.q_table[state_key][action] = new_q

        # Save Q-table periodically
        if len(self.q_table) % 10 == 0:
            self.save_q_table()

    def execute_scraping_action(self, url: str, action: str) -> Dict:
        start_time = time.time()

        try:
            if action == "playwright_full":
                result = self._playwright_full_scrape(url)
            elif action == "playwright_fast":
                result = self._playwright_fast_scrape(url)
            elif action == "playwright_js_wait":
                result = self._playwright_js_wait_scrape(url)
            elif action == "requests_simple":
                result = self._requests_simple_scrape(url)
            else:
                raise ValueError(f"Unknown action: {action}")

            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            result["success"] = True

            return result

        except Exception as e:
            logger.error(f"Scraping action {action} failed: {str(e)}")
            return {
                "content": "",
                "html": "",
                "screenshot_path": None,
                "execution_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }

    def _playwright_full_scrape(self, url: str) -> Dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, wait_until="load", timeout=30000)

            screenshot_path = f"{self.screenshots_dir}/screenshot_{int(time.time())}.png"
            page.screenshot(path=screenshot_path, full_page=True)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            for script in soup(["script", "style"]):
                script.decompose()

            content = soup.get_text()

            browser.close()

            return {
                "content": content,
                "html": html,
                "screenshot_path": screenshot_path
            }

    def _playwright_fast_scrape(self, url: str) -> Dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=15000)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            content = soup.get_text()

            browser.close()

            return {
                "content": content,
                "html": html,
                "screenshot_path": None
            }

    def _playwright_js_wait_scrape(self, url: str) -> Dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for potential dynamic content
            page.wait_for_timeout(2000)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            content = soup.get_text()

            browser.close()

            return {
                "content": content,
                "html": html,
                "screenshot_path": None
            }

    def _requests_simple_scrape(self, url: str) -> Dict:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        content = soup.get_text()

        return {
            "content": content,
            "html": html,
            "screenshot_path": None
        }

    def calculate_reward(self, result: Dict, state: Dict) -> float:
        if not result["success"]:
            return -1.0

        reward = 0.0
        content_length = len(result["content"])

        # Reward based on content length
        if content_length > 1000:
            reward += 1.0
        elif content_length > 500:
            reward += 0.5
        else:
            reward -= 0.5

        # Penalty for long execution time
        if result["execution_time"] > 10:
            reward -= 0.3
        elif result["execution_time"] < 3:
            reward += 0.2

        # Bonus for screenshot if needed
        if result["screenshot_path"] and state.get("is_wikisource", False):
            reward += 0.1

        return reward

    def calculate_quality_score(self, result: Dict) -> float:
        if not result["success"]:
            return 1.0

        content_length = len(result["content"])

        # Base score from content length
        if content_length > 2000:
            base_score = 5.0
        elif content_length > 1000:
            base_score = 4.0
        elif content_length > 500:
            base_score = 3.0
        elif content_length > 100:
            base_score = 2.0
        else:
            base_score = 1.0

        # Adjust for execution time
        if result["execution_time"] > 15:
            base_score -= 1.0
        elif result["execution_time"] < 5:
            base_score += 0.5

        return max(1.0, min(5.0, base_score))

    def scrape_url(self, url: str, strategy: Optional[str] = None) -> Dict:
        logger.info(f"Starting RL scrape of: {url}")

        try:
            response = requests.get(url, timeout=5)
            initial_html = response.text
        except:
            initial_html = "<html><body>fallback</body></html>"

        # Simulate page variants for training
        if random.random() > 0.7:  # 30% chance to use variant
            initial_html = self.simulate_page_variants(initial_html)

        state = self.get_page_state(initial_html, url)
        if strategy:
            action = strategy
        else:
            action = self.choose_action(state)

        # Execute scraping
        result = self.execute_scraping_action(url, action)

        # Calculate reward and quality
        reward = self.calculate_reward(result, state)
        quality_score = self.calculate_quality_score(result)

        # Update Q-table
        self.update_q_value(state, action, reward)

        # Log performance
        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "action": action,
            "reward": reward,
            "quality_score": quality_score,
            "execution_time": result["execution_time"],
            "content_length": len(result["content"]),
            "success": result["success"]
        }

        self.performance_history.append(performance_record)

        # Keep only last 100 records
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        return {
            "content": result["content"],
            "html": result["html"],
            "screenshot_path": result.get("screenshot_path"),
            "strategy": action,
            "quality_score": quality_score,
            "rl_reward": reward,
            "execution_time": result["execution_time"],
            "success": result["success"]
        }

    def update_from_feedback(self, content_id: str, rating: int, comments: str = None) -> str:
        reward = (rating - 3) / 2
        if self.performance_history:
            last_record = self.performance_history[-1]

            # Create dummy state for update
            dummy_state = {"text_length": 1000, "has_javascript": False, "has_captcha": False, "page_complexity": 5}

            # Update Q-value based on feedback
            self.update_q_value(dummy_state, last_record["action"], reward)

            logger.info(f"Updated scraper RL model with feedback: {rating}/5")
            return f"Updated Q-value for {last_record['action']}"

        return "No recent actions to update"

    def is_healthy(self) -> bool:
        return len(self.q_table) >= 0  # Basic health check

    def get_performance_stats(self) -> Dict:
        if not self.performance_history:
            return {"total_scrapes": 0, "success_rate": 0.0, "avg_quality": 0.0}

        total_scrapes = len(self.performance_history)
        successful_scrapes = sum(1 for record in self.performance_history if record["success"])
        success_rate = successful_scrapes / total_scrapes if total_scrapes > 0 else 0.0

        avg_quality = sum(record["quality_score"] for record in self.performance_history) / total_scrapes

        return {
            "total_scrapes": total_scrapes,
            "success_rate": success_rate,
            "avg_quality": avg_quality,
            "q_table_size": len(self.q_table)
        }

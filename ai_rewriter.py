import os
import random
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AIRewriter:
    """RL-optimized AI rewriting engine using Google Gemini"""

    def __init__(self):
        self.actions = [
            'dramatize',
            'summarize', 
            'formalize',
            'expand',
            'simplify'
        ]
        self.q_table = {}
        self.learning_rate = 0.1
        self.gamma = 0.9
        self.epsilon = 0.2
        self.q_table_file = 'data/rewriter_q_table.json'

        # Initialize state_key attribute
        self.state_key = None

        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        self.load_q_table()

        # Configure Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            genai.configure(api_key="your-api-key-here")
        else:
            genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def load_q_table(self):
        if os.path.exists(self.q_table_file):
            try:
                with open(self.q_table_file, 'r') as f:
                    self.q_table = json.load(f)
                logger.info(f"Loaded rewriter Q-table with {len(self.q_table)} states")
            except Exception as e:
                logger.error(f"Error loading Q-table: {e}")
                self.q_table = {}
        else:
            self.q_table = {}

    def save_q_table(self):
        try:
            os.makedirs(os.path.dirname(self.q_table_file), exist_ok=True)
            with open(self.q_table_file, 'w') as f:
                json.dump(self.q_table, f, indent=2)
            logger.info(f"Saved rewriter Q-table with {len(self.q_table)} states")
        except Exception as e:
            logger.error(f"Error saving Q-table: {e}")

    def choose_action(self, state_key: str):
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in self.actions}

        if random.random() < self.epsilon:
            return random.choice(self.actions)
        else:
            return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]

    def update_q_value(self, state_key: str, action: str, reward: float):
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in self.actions}

        old_q = self.q_table[state_key][action]
        new_q = old_q + self.learning_rate * (reward - old_q)
        self.q_table[state_key][action] = new_q

        # Save Q-table after every update (not just every 10)
        self.save_q_table()

        logger.info(f"Updated Q-value for {action} at {state_key}: {old_q:.3f} -> {new_q:.3f}")

    def generate_prompt(self, action: str, content: str) -> str:
        prompts = {
            'dramatize': f"""Rewrite the following text in a dramatic style, enhancing emotional impact while retaining core meaning:

{content}

""",
            'summarize': f"""Summarize the following text in clear, concise language:

{content}

""",
            'formalize': f"""Rewrite the following text to a formal academic tone:

{content}

""",
            'expand': f"""Expand the following text by adding descriptive detail and elaboration:

{content}

""",
            'simplify': f"""Simplify the following text, keeping the main ideas but using plain language:

{content}

"""
        }
        return prompts.get(action, content)

    def rewrite_content(self, content: str, strategy: str = 'auto') -> Dict:
        # Create state key based on content characteristics
        state_key = f"len_{len(content)//500}"

        # IMPORTANT: Set the state_key attribute so app.py can access it
        self.state_key = state_key

        # Choose strategy
        if strategy == 'auto':
            action = self.choose_action(state_key)
        else:
            action = strategy if strategy in self.actions else 'dramatize'

        prompt = self.generate_prompt(action, content)

        # Generate content with Gemini
        try:
            response = self.model.generate_content(prompt)
            rewritten = response.text.strip()

            # Check if rewrite actually happened
            if not rewritten or rewritten == content:
                raise ValueError("Rewrite content is identical or empty")

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            rewritten = f"[🛠 Rewrite failed: content kept original]\n\n{content}"

        # Simple quality assessment
        if rewritten.startswith("[🛠 Rewrite failed"):
            reward = -1.0
            quality_score = 1.0
        else:
            reward = 1.0 if len(rewritten) > len(content) * 0.8 else -0.2
            quality_score = 5.0 if reward > 0 else 2.0

        # Update Q-table
        self.update_q_value(state_key, action, reward)

        return {
            'rewritten_content': rewritten,
            'strategy': action,
            'quality_score': quality_score,
            'rl_reward': reward,
            'state_key': state_key
        }

    def update_from_feedback(self, content_id: str, rating: int, comments: str = None):
        # Convert rating to reward
        reward = (rating - 3) / 2

        # Try to get the actual state and action from stored content
        content_file = f"data/content/{content_id}.json"
        if os.path.exists(content_file):
            try:
                with open(content_file, 'r') as f:
                    content_data = json.load(f)

                state_key = content_data.get('metadata', {}).get('rewrite_state')
                action = content_data.get('metadata', {}).get('rewrite_action')

                if state_key and action:
                    self.update_q_value(state_key, action, reward)
                    return f"Updated Q-value for action {action} at state {state_key} with reward {reward}"

            except Exception as e:
                logger.error(f"Error reading content file: {e}")

        # Fallback to generic state
        state_key = 'generic_state'
        action = random.choice(self.actions)
        self.update_q_value(state_key, action, reward)
        return f"Updated Q-value for action {action} with reward {reward}"

    def is_healthy(self):
        return True

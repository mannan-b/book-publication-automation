
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

DATA_DIR = 'data'
CONTENT_DIR = os.path.join(DATA_DIR, 'content')
FEEDBACK_FILE = os.path.join(DATA_DIR, 'feedback.json')

os.makedirs(CONTENT_DIR, exist_ok=True)
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump([], f)

class ContentStorage:
    """Simple JSON-based storage for content and feedback"""
    def store_content(self, content: str, content_type: str, metadata: Dict) -> str:
        content_id = str(uuid.uuid4())
        file_path = os.path.join(CONTENT_DIR, f"{content_id}.json")
        record = {
            'id': content_id,
            'type': content_type,
            'content': content,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        with open(file_path, 'w') as f:
            json.dump(record, f, indent=2)
        logger.info(f'Saved {content_type} content with id {content_id}')
        return content_id

    def store_feedback(self, content_id: str, rating: int, comments: str = None):
        with open(FEEDBACK_FILE, 'r') as f:
            feedback_data = json.load(f)
        feedback_data.append({
            'content_id': content_id,
            'rating': rating,
            'comments': comments,
            'timestamp': datetime.now().isoformat()
        })
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        logger.info(f'Stored feedback for content {content_id}')

    def is_healthy(self):
        return os.path.isdir(CONTENT_DIR)

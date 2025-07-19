import streamlit as st
import os
import json
import logging
from typing import Optional, Dict, Any
import time
from datetime import datetime

# Import your existing modules
from rl_scraper import RLScraper
from ai_rewriter import AIRewriter
from content_storage import ContentStorage
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Smart Book Publisher",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.scraper = None
        st.session_state.rewriter = None
        st.session_state.storage = None
        st.session_state.config = None
        st.session_state.content_history = []
        st.session_state.current_content = None
        st.session_state.processing = False

# Cache the initialization of components
@st.cache_resource
def get_components():
    """Initialize and cache the main components"""
    try:
        # Ensure data directories exist
        os.makedirs('data/content', exist_ok=True)
        os.makedirs('screenshots', exist_ok=True)
        
        config = ConfigManager()
        scraper = RLScraper()
        rewriter = AIRewriter()
        storage = ContentStorage()
        
        return config, scraper, rewriter, storage
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        st.stop()

# Error handling decorator
def handle_errors(func):
    """Decorator to handle errors gracefully"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)
            return None
    return wrapper

# Main app function
def main():
    """Main Streamlit application"""
    init_session_state()
    
    # Get cached components
    config, scraper, rewriter, storage = get_components()
    
    # Store in session state
    st.session_state.config = config
    st.session_state.scraper = scraper
    st.session_state.rewriter = rewriter
    st.session_state.storage = storage
    
    # App header
    st.title("🤖 Smart Book Publisher")
    st.markdown("### RL-Powered Content Scraping & AI Rewriting Workflow")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "🔍 Scrape Content", "✍️ AI Rewriter", "📊 Q-Table Monitor", "📈 Analytics"],
            key="page_selector"
        )
        
        # API Key status
        st.divider()
        check_api_key_status()
    
    # Route to appropriate page
    if page == "🏠 Home":
        show_home_page()
    elif page == "🔍 Scrape Content":
        show_scraping_page()
    elif page == "✍️ AI Rewriter":
        show_rewriter_page()
    elif page == "📊 Q-Table Monitor":
        show_qtable_monitor()
    elif page == "📈 Analytics":
        show_analytics_page()

def check_api_key_status():
    """Check and display API key status"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        st.success("✅ Gemini API Key: Connected")
    else:
        st.error("❌ Gemini API Key: Not Found")
        st.info("Set your GOOGLE_API_KEY environment variable")

def show_home_page():
    """Display the home page"""
    st.header("Welcome to Smart Book Publisher!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 🚀 Features
        
        - **🔍 RL-Optimized Scraping**: Intelligent web scraping with reinforcement learning
        - **✍️ AI Content Rewriting**: Multiple rewriting strategies with Gemini AI
        - **🧠 Human-in-the-Loop**: Rate and improve AI performance
        - **📊 Learning Analytics**: Monitor Q-table performance and improvements
        - **🔄 Persistent Learning**: System learns from your feedback over time
        
        ## 🎯 How It Works
        
        1. **Scrape**: Extract content from web pages using RL-optimized strategies
        2. **Rewrite**: Transform content with AI using learned preferences
        3. **Feedback**: Rate results to improve future performance
        4. **Learn**: System adapts to your preferences automatically
        """)
    
    with col2:
        st.info("**Quick Stats**")
        if st.button("🔄 Refresh Stats"):
            show_system_stats()

def show_system_stats():
    """Display system statistics"""
    try:
        # Check Q-table files
        rewriter_file = "data/rewriter_q_table.json"
        scraper_file = "data/scraper_q_table.json"
        
        rewriter_states = 0
        scraper_states = 0
        
        if os.path.exists(rewriter_file):
            with open(rewriter_file, 'r') as f:
                rewriter_q = json.load(f)
                rewriter_states = len(rewriter_q)
        
        if os.path.exists(scraper_file):
            with open(scraper_file, 'r') as f:
                scraper_q = json.load(f)
                scraper_states = len(scraper_q)
        
        # Content count
        content_count = len([f for f in os.listdir('data/content') if f.endswith('.json')])
        
        st.metric("Content Processed", content_count)
        st.metric("Rewriter States", rewriter_states)
        st.metric("Scraper States", scraper_states)
        
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")

@handle_errors
def show_scraping_page():
    """Display the scraping page"""
    st.header("🔍 Content Scraping")
    
    # URL input form
    with st.form("scraping_form"):
        st.subheader("Enter URL to Scrape")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            url = st.text_input(
                "URL",
                value=st.session_state.config.get("scraper.default_url", ""),
                placeholder="https://en.wikisource.org/wiki/example"
            )
        
        with col2:
            st.write("Strategy")
            strategy = st.selectbox(
                "Scraping Strategy",
                ["auto", "playwright_full", "playwright_fast", "playwright_js_wait", "requests_simple"],
                help="Choose 'auto' for RL-optimized selection"
            )
        
        submitted = st.form_submit_button("🚀 Start Scraping", use_container_width=True)
    
    if submitted and url:
        if not url.startswith(('http://', 'https://')):
            st.error("Please enter a valid URL starting with http:// or https://")
            return
        
        # Show progress
        with st.spinner("Scraping content..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
                status_text.text(f"Scraping... {i+1}%")
            
            # Perform scraping
            result = perform_scraping(url, strategy)
            
            progress_bar.empty()
            status_text.empty()
        
        if result:
            display_scraping_results(result)

def perform_scraping(url: str, strategy: str) -> Optional[Dict]:
    """Perform the actual scraping operation"""
    try:
        scraper = st.session_state.scraper
        
        if strategy == "auto":
            result = scraper.scrape_url(url)
        else:
            result = scraper.scrape_url(url, strategy=strategy)
        
        if result.get("success"):
            # Store the content
            metadata = {
                "source_url": url,
                "scrape_action": result["strategy"],
                "scrape_state": scraper.state_to_key(scraper.get_page_state(result["html"], url)),
                "phase": "raw"
            }
            
            content_id = st.session_state.storage.store_content(
                result["content"], 
                content_type="raw", 
                metadata=metadata
            )
            
            result["content_id"] = content_id
            return result
        else:
            st.error(f"Scraping failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        return None

def display_scraping_results(result: Dict):
    """Display scraping results"""
    st.success("✅ Scraping completed successfully!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Strategy Used", result["strategy"])
    with col2:
        st.metric("RL Reward", f"{result['rl_reward']:.2f}")
    with col3:
        st.metric("Quality Score", f"{result['quality_score']:.2f}")
    
    # Content preview
    st.subheader("Content Preview")
    content = result["content"]
    
    # Show first 500 characters
    preview_length = min(500, len(content))
    st.text_area("Scraped Content", content[:preview_length], height=200, disabled=True)
    
    if len(content) > preview_length:
        st.info(f"Showing first {preview_length} characters of {len(content)} total")
    
    # Screenshot display
    if result.get("screenshot_path"):
        st.subheader("Screenshot")
        try:
            st.image(result["screenshot_path"], caption="Page Screenshot", use_column_width=True)
        except Exception as e:
            st.warning(f"Could not display screenshot: {str(e)}")
    
    # Store in session state for rewriting
    st.session_state.current_content = result
    
    # Quick rewrite button
    if st.button("➡️ Proceed to AI Rewriting"):
        st.session_state.page_selector = "✍️ AI Rewriter"
        st.rerun()

@handle_errors
def show_rewriter_page():
    """Display the AI rewriting page"""
    st.header("✍️ AI Content Rewriter")
    
    # Content selection
    content_options = get_content_options()
    
    if not content_options:
        st.warning("No content available for rewriting. Please scrape some content first.")
        return
    
    # Content selection form
    with st.form("rewriter_form"):
        st.subheader("Select Content to Rewrite")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_content = st.selectbox(
                "Choose content:",
                content_options,
                format_func=lambda x: f"ID: {x['id'][:8]}... | {x['source_url'][:50]}..."
            )
        
        with col2:
            strategy = st.selectbox(
                "Rewriting Strategy",
                ["auto", "dramatize", "summarize", "formalize", "expand", "simplify"],
                help="Choose 'auto' for RL-optimized selection"
            )
        
        submitted = st.form_submit_button("🤖 Start Rewriting", use_container_width=True)
    
    if submitted and selected_content:
        # Show progress
        with st.spinner("AI is rewriting content..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
                status_text.text(f"Rewriting... {i+1}%")
            
            # Perform rewriting
            result = perform_rewriting(selected_content, strategy)
            
            progress_bar.empty()
            status_text.empty()
        
        if result:
            display_rewriting_results(result, selected_content)

def get_content_options() -> list:
    """Get available content options"""
    try:
        content_dir = "data/content"
        content_files = [f for f in os.listdir(content_dir) if f.endswith('.json')]
        
        content_options = []
        for file in content_files:
            try:
                with open(os.path.join(content_dir, file), 'r') as f:
                    data = json.load(f)
                    content_options.append({
                        'id': data['id'],
                        'content': data['content'],
                        'source_url': data['metadata'].get('source_url', 'Unknown'),
                        'type': data['type']
                    })
            except Exception as e:
                logger.warning(f"Error reading {file}: {str(e)}")
        
        return content_options
    except Exception as e:
        st.error(f"Error loading content options: {str(e)}")
        return []

def perform_rewriting(content_data: Dict, strategy: str) -> Optional[Dict]:
    """Perform the actual rewriting operation"""
    try:
        rewriter = st.session_state.rewriter
        content = content_data['content']
        
        result = rewriter.rewrite_content(content, strategy=strategy)
        
        # Store the rewritten content
        metadata = {
            "parent_id": content_data['id'],
            "rewrite_action": result["strategy"],
            "rewrite_state": result.get("state_key", "unknown"),
            "phase": "rewrite"
        }
        
        content_id = st.session_state.storage.store_content(
            result["rewritten_content"], 
            content_type="rewrite", 
            metadata=metadata
        )
        
        result["content_id"] = content_id
        return result
        
    except Exception as e:
        st.error(f"Error during rewriting: {str(e)}")
        return None

def display_rewriting_results(result: Dict, original_content: Dict):
    """Display rewriting results"""
    st.success("✅ Content rewritten successfully!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Strategy Used", result["strategy"])
    with col2:
        st.metric("RL Reward", f"{result['rl_reward']:.2f}")
    with col3:
        st.metric("Quality Score", f"{result['quality_score']:.2f}")
    
    # Content comparison
    st.subheader("Content Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Original Content**")
        st.text_area("Original", original_content['content'][:500], height=300, disabled=True)
    
    with col2:
        st.write("**Rewritten Content**")
        st.text_area("Rewritten", result['rewritten_content'][:500], height=300, disabled=True)
    
    # Feedback form
    st.subheader("📝 Provide Feedback")
    
    with st.form("feedback_form"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            rating = st.slider("Rate the rewritten content", 1, 5, 3)
        
        with col2:
            comments = st.text_area("Comments (optional)", height=100)
        
        if st.form_submit_button("Submit Feedback"):
            submit_feedback(result["content_id"], rating, comments)

def submit_feedback(content_id: str, rating: int, comments: str):
    """Submit feedback for content"""
    try:
        # Store feedback
        st.session_state.storage.store_feedback(content_id, rating, comments)
        
        # Update RL models
        record_path = os.path.join("data", "content", f"{content_id}.json")
        if os.path.exists(record_path):
            with open(record_path, "r") as f:
                record = json.load(f)
            
            meta = record["metadata"]
            phase = meta.get("phase", "rewrite")
            reward = (rating - 3) / 2
            
            if phase == "rewrite":
                action = meta.get("rewrite_action")
                state_key = meta.get("rewrite_state")
                if action and state_key:
                    st.session_state.rewriter.update_q_value(state_key, action, reward)
            
            st.success(f"✅ Feedback submitted! Reward: {reward:+.2f}")
        
    except Exception as e:
        st.error(f"Error submitting feedback: {str(e)}")

def show_qtable_monitor():
    """Display Q-table monitoring page"""
    st.header("📊 Q-Table Monitor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 AI Rewriter Q-Table")
        display_qtable("data/rewriter_q_table.json", "rewriter")
    
    with col2:
        st.subheader("🔍 Scraper Q-Table")
        display_qtable("data/scraper_q_table.json", "scraper")

def display_qtable(file_path: str, table_type: str):
    """Display Q-table contents"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                q_table = json.load(f)
            
            if q_table:
                st.success(f"✅ {len(q_table)} states learned")
                
                # Show Q-table data
                for state, actions in q_table.items():
                    with st.expander(f"State: {state}"):
                        for action, q_value in actions.items():
                            st.write(f"**{action}**: {q_value:.3f}")
            else:
                st.info("No learning data yet")
        else:
            st.warning("Q-table file not found")
    
    except Exception as e:
        st.error(f"Error loading Q-table: {str(e)}")

def show_analytics_page():
    """Display analytics page"""
    st.header("📈 Analytics & Performance")
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Content", get_content_count())
    with col2:
        st.metric("Average Quality", f"{get_average_quality():.2f}")
    with col3:
        st.metric("Learning Progress", f"{get_learning_progress():.1f}%")
    
    # Recent activity
    st.subheader("Recent Activity")
    show_recent_activity()

def get_content_count() -> int:
    """Get total content count"""
    try:
        return len([f for f in os.listdir('data/content') if f.endswith('.json')])
    except:
        return 0

def get_average_quality() -> float:
    """Get average quality score"""
    try:
        feedback_file = "data/feedback.json"
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
            
            if feedback_data:
                ratings = [item['rating'] for item in feedback_data]
                return sum(ratings) / len(ratings)
    except:
        pass
    return 0.0

def get_learning_progress() -> float:
    """Get learning progress percentage"""
    try:
        # Simple metric based on number of states learned
        rewriter_states = 0
        scraper_states = 0
        
        if os.path.exists("data/rewriter_q_table.json"):
            with open("data/rewriter_q_table.json", 'r') as f:
                rewriter_states = len(json.load(f))
        
        if os.path.exists("data/scraper_q_table.json"):
            with open("data/scraper_q_table.json", 'r') as f:
                scraper_states = len(json.load(f))
        
        # Normalize to percentage (max 100)
        return min(100, (rewriter_states + scraper_states) * 10)
    except:
        return 0.0

def show_recent_activity():
    """Show recent content activity"""
    try:
        content_dir = "data/content"
        content_files = [f for f in os.listdir(content_dir) if f.endswith('.json')]
        
        # Sort by modification time
        content_files.sort(key=lambda x: os.path.getmtime(os.path.join(content_dir, x)), reverse=True)
        
        # Show recent 5 items
        for file in content_files[:5]:
            try:
                with open(os.path.join(content_dir, file), 'r') as f:
                    data = json.load(f)
                
                with st.expander(f"ID: {data['id'][:8]}... | {data['type']}"):
                    st.write(f"**Type**: {data['type']}")
                    st.write(f"**Timestamp**: {data['timestamp']}")
                    if 'source_url' in data['metadata']:
                        st.write(f"**Source**: {data['metadata']['source_url']}")
                    st.write(f"**Content**: {data['content'][:100]}...")
            except Exception as e:
                st.warning(f"Error reading {file}: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading recent activity: {str(e)}")

# Custom CSS for better styling
def load_css():
    """Load custom CSS"""
    st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    .stSuccess {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
    }
    .stError {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    load_css()
    main()

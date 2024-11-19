import asyncio
import nest_asyncio
nest_asyncio.apply()
import streamlit as st
import pandas as pd
import google.generativeai as genai
from telegram import Bot
import telegram
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel("gemini-1.5-flash")

# Page configuration
st.set_page_config(
    page_title="TrueVision - CSV Summarizer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for improved readability and styling
st.markdown("""
    <style>
    .summary-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        color: black;
        font-size: 16px;
        line-height: 1.6;
        margin-bottom: 20px;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

def send_summary_to_telegram(summary):
    """
    Sends the given summary to Telegram using async approach.
    Args:
        summary (str): The summary text to send.
    """
    async def send_message():
        try:
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=summary)
            st.success("Summary sent successfully to Telegram! 🚀")
        except telegram.error.TelegramError as e:
            st.error(f"Telegram Error: {e}")
        except Exception as e:
            st.error(f"Failed to send summary: {e}")

    try:
        asyncio.run(send_message())
    except RuntimeError:
        # If event loop is already running, use alternative method
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message())

def summarize_article(article_content):
    """
    Summarize article content using Gemini API
    """
    try:
        prompt = f"Professionally summarize the following content: {article_content}"
        with st.spinner("Generating AI Summary... Please wait ⏳"):
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Summary generation failed: {e}"

def main():
    st.title("📄 Article Summarizer")
    st.markdown("**Intelligent CSV Article Summarization with AI**")

    # Initialize session state for summaries
    if 'summaries' not in st.session_state:
        st.session_state.summaries = []

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload CSV File", 
        type=["csv"], 
        help="Upload a CSV with 'Article Name' and 'Article Content' columns"
    )

    if uploaded_file is not None:
        # Load and process CSV
        df = pd.read_csv(uploaded_file)
        
        # Validate columns
        if not all(col in df.columns for col in ["Article Name", "Article Content"]):
            st.error("CSV must contain 'Article Name' and 'Article Content' columns")
            return

        # Display index range and selection
        st.info(f"Available Articles: 0 to {len(df) - 1}")
        
        selected_index = st.number_input(
            "Select Article Index", 
            min_value=0, 
            max_value=len(df) - 1, 
            value=0,
            help="Choose the index of the article to summarize"
        )

        # Generate Summary Button
        if st.button("Generate Summary", help="Create AI-powered summary"):
            try:
                article_name = df.loc[selected_index, "Article Name"]
                article_content = df.loc[selected_index, "Article Content"]
                
                # Generate Summary 
                summary = summarize_article(article_content)
                
                # Add to session state
                st.session_state.summaries.append({
                    "Article Name": article_name, 
                    "Summary": summary
                })
            
            except Exception as e:
                st.error(f"Error generating summary: {e}")

        # Display all summaries
        if st.session_state.summaries:
            st.subheader("Generated Summaries")
            for summary_item in st.session_state.summaries:
                st.markdown("<div class='summary-container'>", unsafe_allow_html=True)
                st.markdown(f"**Article:** {summary_item['Article Name']}")
                st.markdown(f"**Summary:** {summary_item['Summary']}")
                st.markdown("</div>", unsafe_allow_html=True)

            # Separate Telegram Send Button
            if st.button("Send All Summaries to Telegram"):
                all_summaries_text = "\n\n".join([
                    f"Article: {item['Article Name']}\n\nSummary: {item['Summary']}" 
                    for item in st.session_state.summaries
                ])
                send_summary_to_telegram(all_summaries_text)

        # Clear Summaries Button
        if st.session_state.summaries:
            if st.button("Clear Summaries"):
                st.session_state.summaries = []
                st.experimental_rerun()

if __name__ == "__main__":
    main()
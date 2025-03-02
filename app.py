import streamlit as st
import requests
import json
import os
from groq import Groq
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in .env file. Please set it.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# File to store book data
BOOKS_FILE = "books.json"

# Load previously saved books
def load_books():
    if os.path.exists(BOOKS_FILE):
        try:
            with open(BOOKS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return {}
        except (json.JSONDecodeError, ValueError) as e:
            st.warning(f"Invalid JSON in {BOOKS_FILE}: {e}. Starting with an empty book list.")
            return {}
    return {}

# Save books to file
def save_books(books):
    with open(BOOKS_FILE, "w") as f:
        json.dump(books, f, indent=4)

# Fetch book content and metadata
def fetch_book(book_id):
    metadata_url = f"https://www.gutenberg.org/ebooks/{book_id}"
    try:
        metadata_response = requests.get(metadata_url)
        metadata_response.raise_for_status()
        metadata_html = metadata_response.text
    except requests.RequestException as e:
        st.error(f"Error fetching metadata page: {e}")
        return None

    soup = BeautifulSoup(metadata_html, "html.parser")
    text_link = soup.find("a", href=True, string=lambda x: "Plain Text UTF-8" in x if x else False)
    
    if not text_link:
        st.error(f"No Plain Text UTF-8 file found for book ID {book_id}.")
        return None

    content_url = f"https://www.gutenberg.org{text_link['href']}"
    try:
        content_response = requests.get(content_url)
        content_response.raise_for_status()
        content = content_response.text
    except requests.RequestException as e:
        st.error(f"Error fetching book content: {e}")
        return None

    try:
        title = metadata_html.split("<title>")[1].split("</title>")[0]
    except IndexError:
        title = f"Book {book_id} (Title Unavailable)"

    return {"content": content, "title": title}

# Condense text locally, weighting later chunks
def condense_text(text, max_chars=10000):
    start_idx = text.find("*** START OF THE PROJECT GUTENBERG EBOOK")
    if start_idx != -1:
        text = text[start_idx + 100:]
    
    chunk_size = 5000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    condensed = []
    for i, chunk in enumerate(chunks):
        sentences = re.split(r'(?<=[.!?])\s+', chunk)
        key_sentences = [s for s in sentences if '"' in s or re.search(r'[A-Z][a-z]+', s)]
        if key_sentences:
            weight = min(2, len(chunks) - i)  # More sentences from later chunks
            condensed.extend(sorted(key_sentences, key=len, reverse=True)[:weight])
        else:
            condensed.append(sentences[0] if sentences else "")
    
    condensed_text = " ".join(condensed)
    return condensed_text[:max_chars] if len(condensed_text) > max_chars else condensed_text

# Analyze text with Groq LLM
def analyze_text(text, analysis_type, model="llama3-70b-8192"):
    condensed_text = condense_text(text, max_chars=10000)  # ~2,500 tokens
    
    prompts = {
        "summary": (
             "Provide a comprehensive plot summary of this text, detailing all main events in strict chronological order "
            "from start to finish. Ensure the summary flows smoothly, weaving key moments into a cohesive narrative "
            "with clear cause-and-effect connections. Begin with the story’s initial setup, progress through critical "
            "developments (including character actions, major deaths, conflicts, and pivotal incidents), and conclude "
            "with the final resolution, keeping it concise yet complete. Do not omit significant plot points, such as "
            "murders, betrayals, or shifts in power. After the summary. Limit the entire response to 500 words.\n\nText: {condensed_text}"
        ),
        "sentiment": (
            "Analyze the sentiment of this text based on its ending for the main character, not metadata or introductory notes. "
            "Focus on the emotional tone of the main character's ending (positive, negative, or neutral). If the main character’s "
            "ending is sad or tragic (e.g., contains 'death,' 'dies,' 'killed'), classify the sentiment as negative; "
            "if the main character's ending is happy life, love, romantic, marriage then classify the sentiment as positive; otherwise, use neutral if the tone is balanced "
            "or unclear.\n\nText: {condensed_text}"
        ),
        "characters": (
            "Identify all key characters in this text, excluding minor figures unless they significantly impact the plot. "
            "For each character, provide a concise one-liner description of their role or significance in the story, "
            "based on the narrative content, not metadata. Ensure the list is comprehensive and reflects the entire text."
            "\n\nText: {condensed_text}"
        )
    }
    
    prompt = prompts.get(analysis_type, "Invalid analysis type").format(condensed_text=condensed_text)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            timeout=20,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error during analysis: {e}")
        return "Analysis failed."

# Streamlit app
def main():
    st.title("📚 Project Gutenberg Explorer")
    st.write("Enter a Project Gutenberg book ID to explore and analyze free e-books!")

    books = load_books()

    with st.sidebar:
        st.subheader("Previously Accessed Books")
        if books:
            for book_id, data in books.items():
                if st.button(f"{data['title']} (ID: {book_id})", key=book_id):
                    st.session_state["current_book_id"] = book_id
        else:
            st.write("No books yet!")

    book_id = st.text_input("Enter Book ID (e.g., 1787 for 'Hamlet', 161 for Sense and Sensibility, and 1497 for the Republic, 1513 for Romeo and Juliet , and 1342 for Pride and Prejudice, 84 for Frankenstein; Or, The Modern Prometheus )", "")
    
    if book_id:
        if book_id not in books:
            with st.spinner("Fetching book..."):
                book_data = fetch_book(book_id)
                if book_data:
                    books[book_id] = book_data
                    save_books(books)
                    st.session_state["current_book_id"] = book_id
        else:
            st.session_state["current_book_id"] = book_id

    if "current_book_id" in st.session_state:
        current_id = st.session_state["current_book_id"]
        if current_id in books:
            book = books[current_id]
            st.subheader(book["title"])
            st.text_area("Book Content", book["content"][:1000] + "...", height=200)

            analysis_type = st.selectbox("Choose Analysis Type", ["summary", "sentiment", "characters"])
            st.write("**Recommended Model**: llama3-70b-8192 (best overall for accuracy across summary, sentiment, and characters)")
            model = st.selectbox("Choose Model", ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"], index=0)
            if st.button("Analyze Text"):
                with st.spinner("Analyzing..."):
                    result = analyze_text(book["content"], analysis_type, model)
                    st.write("**Analysis Result:**")
                    st.write(result)

# Custom CSS
st.markdown("""
    <style>
    .stApp { max-width: 1200px; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
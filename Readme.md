# Project Gutenberg Explorer

A web application built with Streamlit and Models from Groq platform to explore and analyze free e-books from Project Gutenberg, featuring plot summaries, sentiment analysis, and character identification.

---

## Overview

Project Gutenberg Explorer allows users to:
- Input a Project Gutenberg book ID to fetch and display book text and metadata.
- Save books locally for future access.
- View a list of previously accessed books.
- Analyze book text using an LLM for plot summaries, sentiment, and key characters.

- Built with Streamlit for rapid deployment and Groq (`llama3-70b-8192`, `mixtral-8x7b-32768`, `gemma2-9b-it`) for text analysis, this app meets the core functionality and analysis requirements of the task.

---

## Features

- **Core Functionality**: Input field, fetch/display, save, and list view of books.
- **Text Analysis**: 
  - Generic plot summaries for any narrative.
  - Sentiment analysis based on the main character’s ending (positive, negative, neutral).
  - Comprehensive character identification with role descriptions.
- **Styling**: Simple, functional UI with Streamlit 

---

## Setup Instructions

Follow these steps to run the app locally using Conda:

### Prerequisites

- **Conda**: Installed for environment management (download from [Anaconda](https://www.anaconda.com/)).
- **Git**: To clone the repository.

### Step-by-Step Setup

1. **Clone the Repository**
   - Open a terminal and navigate to your project directory:
     ```bash
     cd /path/to/your/directory
2. Clone the repo: `git clone <repo-url>`
3. Create a virtual environment named venv with Python 3.11: `conda create -p venv python=3.11 -y`
4. Activate the venv environment `conda activate venv/`
5. Install dependencies: `pip install -r requirements.txt`
6. Add your Groq API key to `.env`  as GROQ_API_KEY=
7. Run locally: `streamlit run app.py`

## Features
- Fetch books by ID
- Display content and metadata
- Save books locally
- Analyze text (summary, sentiment, characters)  

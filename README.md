# Smart Expense Tracker

A private expense tracker powered by a local, open-source AI model.
Type expenses in plain language (for example "tea 20, bus 100, lunch 120")
and the AI organises them into categories, shows charts, and gives saving tips.
All data stays on your own machine.

Built for the Hacktoberfest 2026 Weekend Challenge: Build for a Friend.

## Features
- Natural-language expense entry
- Automatic categorisation with Gemma 3 (4B) via Ollama
- Bar and donut charts
- AI-generated summary and saving tips
- Data saved locally in a CSV file

## Setup
1. Install Ollama from https://ollama.com
2. Download the model: `ollama pull gemma3:4b`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python -m streamlit run newtracker.py`

## Tech Stack
Python, Streamlit, Ollama, Gemma 3, Pandas, Altair

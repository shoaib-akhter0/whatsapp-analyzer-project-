# WhatsApp Chat Analyzer

A professional Streamlit dashboard for analyzing exported WhatsApp chat conversations. Upload a WhatsApp `.txt` export and get rich insights about activity, users, timing, text patterns, media sharing, links, emojis, and more.

## Features

- Upload and parse WhatsApp chat exports in `.txt` format
- View high-level conversation statistics
- Analyze user activity and contribution percentages
- Explore timeline and activity trends over time
- Generate word clouds and common-word summaries
- Review emoji usage and shared links
- Inspect media breakdowns and advanced chat insights
- Download the cleaned dataset as CSV

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- Matplotlib
- WordCloud
- Emoji
- VaderSentiment
- Urlextract

## Project Structure

- `app.py` — Streamlit UI and dashboard layout
- `helper.py` — analysis logic and chart/data helpers
- `preprocessor.py` — WhatsApp export parsing and preprocessing
- `test_parser.py` — quick parser sanity check for exported chat files
- `requirements.txt` — Python dependencies

## Setup

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

Start the dashboard with:

```bash
streamlit run app.py
```

## Test the Parser

You can quickly verify whether a chat export can be parsed:

```bash
python test_parser.py path/to/your_chat.txt
```

## Exporting a WhatsApp Chat

To generate a compatible export:

1. Open the WhatsApp chat
2. Tap the menu
3. Choose "More"
4. Select "Export chat"
5. Choose "Without Media"
6. Save the `.txt` file and upload it to the app

## Notes

All processing happens locally in your session. The app does not store or transmit your chat data anywhere else.

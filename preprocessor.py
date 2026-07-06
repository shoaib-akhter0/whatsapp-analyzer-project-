"""
preprocessor.py
----------------
Parses a raw WhatsApp exported .txt chat file into a clean, structured
pandas DataFrame ready for analysis.

Supports the common WhatsApp export variants:
  - Android 12-hour : 12/31/23, 11:45 PM - John: Hello
  - Android 24-hour  : 31/12/2023, 23:45 - John: Hello
  - iOS bracket 12h  : [31/12/2023, 11:45:30 PM] John: Hello
  - iOS bracket 24h  : [31/12/2023, 23:45:30] John: Hello
"""

import re
import pandas as pd


# ---------------------------------------------------------------------------
# Regex patterns for the different date/time stamp styles WhatsApp uses
# ---------------------------------------------------------------------------
DATE_PATTERNS = [
    r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?[APMapm]{2}\s-\s',   # Android 12h: 12/31/23, 11:45 PM -
    r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s',                 # Android 24h: 31/12/2023, 23:45 -
    r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\s?[APMapm]{2}\]\s',  # iOS 12h
    r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\]\s',          # iOS 24h
    r'\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{2}:\d{2}\s?[APMapm]{0,2}\s-\s',   # ISO: 2026-01-20 21:15:00 -
    r'\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{2}\s?[APMapm]{0,2}\s-\s',         # ISO no seconds: 2026-01-20 21:15 -
    r'\d{1,2}-\d{1,2}-\d{2,4}\s\d{1,2}:\d{2}\s?[APMapm]{0,2}\s-\s',       # dd-mm-yyyy 21:15 -
]

DATE_FORMATS = [
    "%m/%d/%y, %I:%M %p", "%d/%m/%y, %I:%M %p",
    "%m/%d/%Y, %I:%M %p", "%d/%m/%Y, %I:%M %p",
    "%m/%d/%y, %H:%M", "%d/%m/%y, %H:%M",
    "%m/%d/%Y, %H:%M", "%d/%m/%Y, %H:%M",
    "%d/%m/%Y, %I:%M:%S %p", "%d/%m/%y, %I:%M:%S %p",
    "%d/%m/%Y, %H:%M:%S", "%d/%m/%y, %H:%M:%S",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M:%S %p",
    "%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p",
    "%d-%m-%Y %H:%M", "%d-%m-%y %H:%M",
    "%d-%m-%Y %I:%M %p", "%d-%m-%y %I:%M %p",
]

# Media placeholders WhatsApp inserts when media is exported "without media"
MEDIA_TYPE_MARKERS = {
    "Image": ["image omitted", "<media omitted>"],  # generic media often = image on Android
    "Video": ["video omitted"],
    "Audio": ["audio omitted"],
    "Sticker": ["sticker omitted"],
    "GIF": ["gif omitted"],
    "Document": ["document omitted"],
}


def _clean_date_token(token: str) -> str:
    """Strip brackets / trailing dash artefacts from a matched date token."""
    token = token.strip().strip('[]')
    token = token.rstrip('-').strip()
    return token


def classify_media(message: str):
    """
    Returns the media type name if the message is a media placeholder,
    otherwise returns None.
    """
    m = message.strip().lower()
    for media_type, markers in MEDIA_TYPE_MARKERS.items():
        if any(marker in m for marker in markers):
            return media_type
    return None


def preprocess(data: str) -> pd.DataFrame:
    """
    Convert raw WhatsApp .txt export content into a structured DataFrame.

    Returns a DataFrame with columns:
    date, user, message, year, month, month_name, day, day_name,
    hour, minute, only_date, period, message_length, is_media,
    media_type, is_weekend
    """

    messages, dates = None, None

    for pattern in DATE_PATTERNS:
        found_dates = re.findall(pattern, data)
        if len(found_dates) > 5:
            messages = re.split(pattern, data)[1:]
            dates = found_dates
            break

    if not messages:
        raise ValueError(
            "Could not detect a known WhatsApp date/time format in this file. "
            "Please re-export the chat as 'Without Media' .txt from WhatsApp."
        )

    df = pd.DataFrame({"date_str": dates, "message": messages})
    df["date_str"] = df["date_str"].apply(_clean_date_token)

    parsed = None
    for fmt in DATE_FORMATS:
        try:
            candidate = pd.to_datetime(df["date_str"], format=fmt, errors="coerce")
            if candidate.notna().mean() > 0.9:
                parsed = candidate
                break
        except (ValueError, TypeError):
            continue

    if parsed is None:
        parsed = pd.to_datetime(df["date_str"], errors="coerce", dayfirst=True)

    df["date"] = parsed
    df = df.dropna(subset=["date"]).reset_index(drop=True)

    # Split "User: message" -> user, message. System lines -> Group Notification.
    users, messages_clean = [], []
    for message in df["message"]:
        entry = re.split(r"([^:]+):\s", message, maxsplit=1)
        if len(entry) >= 3:
            users.append(entry[1].strip())
            messages_clean.append(entry[2])
        else:
            users.append("Group Notification")
            messages_clean.append(entry[0])

    df["user"] = users
    df["message"] = messages_clean

    # --- Feature engineering ---
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    df["only_date"] = df["date"].dt.date
    df["message_length"] = df["message"].str.len()
    df["is_weekend"] = df["day_name"].isin(["Saturday", "Sunday"])

    df["media_type"] = df["message"].apply(classify_media)
    df["is_media"] = df["media_type"].notna()

    period = []
    for hour in df["hour"]:
        start = hour
        end = (hour + 1) % 24
        period.append(f"{start:02d}-{end:02d}")
    df["period"] = period

    df = df.sort_values("date").reset_index(drop=True)
    return df
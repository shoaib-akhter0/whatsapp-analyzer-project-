"""
helper.py
---------
All analysis functions for the WhatsApp Chat Analyzer.
Pure data functions only - no Streamlit / UI code lives here, so this
module can be unit-tested and reused independently of the app layer.
"""

from collections import Counter
from urllib.parse import urlparse

import pandas as pd
import emoji
from urlextract import URLExtract
from wordcloud import WordCloud, STOPWORDS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

extract = URLExtract()
analyzer = SentimentIntensityAnalyzer()

# English + common Hinglish/Romanized stopwords so the word cloud / common
# words aren't dominated by filler words.
STOP_WORDS = set(STOPWORDS) | {
    'the', 'is', 'to', 'of', 'and', 'a', 'i', 'you', 'it', 'in',
    'for', 'on', 'this', 'that', 'with', 'my', 'me', 'your', 'media',
    'omitted', 'im', "i'm", 'are', 'was', 'be', 'have', 'has', 'not',
    'but', 'so', 'if', 'or', 'at', 'as', 'by', 'we', 'us', 'will',
    'hai', 'ha', 'ki', 'ka', 'ke', 'ko', 'h', 'hy', 'hn', 'nahi',
    'nhi', 'kya', 'k', 'hu', 'hoon', 'tha', 'thi', 'bhi',
    'ok', 'okay', 'yes', 'no', 'na', 'toh', 'ye', 'yeh', 'wo',
    'woh', 'aur', 'hum', 'mein', 'se', 'par', 'pe',
}


def _filter_user(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    return df


def _real(df):
    """Exclude system 'Group Notification' rows."""
    return df[df['user'] != 'Group Notification']


# ---------------------------------------------------------------------------
# 1. Overall Statistics
# ---------------------------------------------------------------------------

def fetch_stats(selected_user, df):
    """Returns (num_messages, num_words, num_media_messages, num_links)."""
    df = _real(_filter_user(selected_user, df))

    num_messages = df.shape[0]

    words = []
    for message in df.loc[~df['is_media'], 'message']:
        words.extend(message.split())

    num_media_messages = int(df['is_media'].sum())

    links = []
    for message in df['message']:
        links.extend(extract.find_urls(message))

    return num_messages, len(words), num_media_messages, len(links)


# ---------------------------------------------------------------------------
# 2. User Analysis
# ---------------------------------------------------------------------------

def most_busy_users(df):
    """Returns (counts_series_top10, percentage_dataframe)."""
    real = _real(df)
    counts = real['user'].value_counts().head(10)
    pct = round((real['user'].value_counts() / real.shape[0]) * 100, 2).reset_index()
    pct.columns = ['User', 'Percentage']
    return counts, pct


# ---------------------------------------------------------------------------
# 3. Timeline Analysis
# ---------------------------------------------------------------------------

def monthly_timeline(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    timeline = df.groupby(['year', 'month', 'month_name']).count()['message'].reset_index()
    timeline = timeline.sort_values(['year', 'month'])
    timeline['time'] = [f"{r['month_name']}-{r['year']}" for _, r in timeline.iterrows()]
    return timeline


def daily_timeline(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    return df.groupby('only_date').count()['message'].reset_index()


# ---------------------------------------------------------------------------
# 4. Activity Analysis
# ---------------------------------------------------------------------------

def week_activity_map(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    return df['day_name'].value_counts()


def month_activity_map(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    return df['month_name'].value_counts()


def hourly_activity_map(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    return df['hour'].value_counts().sort_index()


def activity_heatmap(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    heatmap = df.pivot_table(
        index='day_name', columns='period', values='message', aggfunc='count'
    ).fillna(0)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return heatmap.reindex([d for d in day_order if d in heatmap.index])


def weekend_vs_weekday(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    counts = df['is_weekend'].value_counts()
    return pd.Series({
        'Weekday': int(counts.get(False, 0)),
        'Weekend': int(counts.get(True, 0)),
    })


# ---------------------------------------------------------------------------
# 5. Text Analysis
# ---------------------------------------------------------------------------

def _clean_words(df):
    words = []
    for _, row in df.iterrows():
        if row['is_media']:
            continue
        for word in str(row['message']).lower().split():
            word = word.strip('.,!?;:"\'()[]{}')
            if word and word not in STOP_WORDS and not word.startswith(('http', 'www')):
                words.append(word)
    return words


def create_wordcloud(selected_user, df):
    df = _real(_filter_user(selected_user, df))
    words = _clean_words(df)
    text = " ".join(words) if words else "no_data_available"
    return WordCloud(
        width=900, height=500, background_color='white',
        colormap='viridis', max_words=200,
    ).generate(text)


def most_common_words(selected_user, df, top_n=20):
    df = _real(_filter_user(selected_user, df))
    words = _clean_words(df)
    return pd.DataFrame(Counter(words).most_common(top_n), columns=['word', 'count'])


# ---------------------------------------------------------------------------
# 6. Emoji Analysis
# ---------------------------------------------------------------------------

def emoji_helper(selected_user, df):
    df = _filter_user(selected_user, df)
    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
    return pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))),
                         columns=['emoji', 'count'])


# ---------------------------------------------------------------------------
# 7. Link Analysis
# ---------------------------------------------------------------------------

def extract_links(selected_user, df, top_n=20):
    df = _filter_user(selected_user, df)
    links = []
    for message in df['message']:
        links.extend(extract.find_urls(message))
    return pd.DataFrame(Counter(links).most_common(top_n), columns=['Link', 'Count'])


def top_domains(selected_user, df, top_n=10):
    """Returns a DataFrame of the most frequently shared domains."""
    df = _filter_user(selected_user, df)
    links = []
    for message in df['message']:
        links.extend(extract.find_urls(message))

    domains = []
    for link in links:
        try:
            netloc = urlparse(link if link.startswith('http') else f'http://{link}').netloc
            domains.append(netloc.replace('www.', ''))
        except ValueError:
            continue

    return pd.DataFrame(Counter(domains).most_common(top_n), columns=['Domain', 'Count'])


# ---------------------------------------------------------------------------
# 8. Media Analysis
# ---------------------------------------------------------------------------

def media_breakdown(selected_user, df):
    """Returns a Series of counts per media type (Image, Video, Audio, Sticker, Document, GIF)."""
    df = _filter_user(selected_user, df)
    media_df = df[df['is_media']]
    if media_df.empty:
        return pd.Series(dtype=int)
    return media_df['media_type'].value_counts()


# ---------------------------------------------------------------------------
# 9. Advanced Analytics
# ---------------------------------------------------------------------------

def response_time_analysis(df):
    """
    Average response time (minutes) per user - time elapsed since the
    previous message when the speaker changes. Ignores gaps over 24h
    (treated as inactivity, not a 'response').
    """
    real = _real(df).sort_values('date').copy()
    real['prev_user'] = real['user'].shift(1)
    real['prev_time'] = real['date'].shift(1)
    real['response_time'] = (real['date'] - real['prev_time']).dt.total_seconds() / 60

    resp = real[(real['user'] != real['prev_user']) & (real['response_time'] >= 0)]
    resp = resp[resp['response_time'] <= 24 * 60]

    avg_resp = resp.groupby('user')['response_time'].mean().sort_values()
    return avg_resp, resp[['user', 'date', 'response_time']]


def longest_messages(selected_user, df, top_n=10):
    df = _real(_filter_user(selected_user, df))
    df = df[~df['is_media']]
    return df.nlargest(top_n, 'message_length')[['user', 'message', 'message_length']]


def message_length_distribution(selected_user, df):
    """Returns the message_length series (for a histogram), excluding media."""
    df = _real(_filter_user(selected_user, df))
    return df.loc[~df['is_media'], 'message_length']


def chat_streaks(df):
    """
    Returns dict: longest_streak, streak_start, streak_end, longest_gap, current_streak.
    """
    real = _real(df)
    unique_dates = sorted(set(real['only_date']))

    if not unique_dates:
        return {"longest_streak": 0, "streak_start": None, "streak_end": None,
                "longest_gap": 0, "current_streak": 0}

    longest_streak = cur_streak = 1
    best_start = best_end = run_start = unique_dates[0]
    longest_gap = 0

    for i in range(1, len(unique_dates)):
        gap = (unique_dates[i] - unique_dates[i - 1]).days
        if gap == 1:
            cur_streak += 1
        else:
            if cur_streak > longest_streak:
                longest_streak = cur_streak
                best_start, best_end = run_start, unique_dates[i - 1]
            cur_streak = 1
            run_start = unique_dates[i]
            longest_gap = max(longest_gap, gap - 1)

    if cur_streak > longest_streak:
        longest_streak = cur_streak
        best_start, best_end = run_start, unique_dates[-1]

    return {
        "longest_streak": longest_streak, "streak_start": best_start,
        "streak_end": best_end, "longest_gap": longest_gap,
        "current_streak": cur_streak,
    }


def sentiment_analysis(selected_user, df):
    """
    Adds a VADER compound sentiment score to each message and buckets it into
    Positive / Neutral / Negative.
    Returns (df_with_sentiment, summary_counts, avg_score_by_user).
    """
    df = _real(_filter_user(selected_user, df))
    df = df[~df['is_media']].copy()
    df = df[df['message'].str.strip().astype(bool)]

    if df.empty:
        return df, pd.Series(dtype=int), pd.Series(dtype=float)

    df['sentiment_score'] = df['message'].apply(
        lambda m: analyzer.polarity_scores(str(m))['compound']
    )

    def bucket(score):
        if score >= 0.05:
            return 'Positive'
        elif score <= -0.05:
            return 'Negative'
        return 'Neutral'

    df['sentiment'] = df['sentiment_score'].apply(bucket)
    summary = df['sentiment'].value_counts()
    by_user = df.groupby('user')['sentiment_score'].mean().sort_values(ascending=False)
    return df, summary, by_user


def avg_message_length_by_user(df, top_n=10):
    real = _real(df)
    real = real[~real['is_media']]
    stats = real.groupby('user').agg(
        Messages=('message', 'count'),
        Avg_Length=('message_length', 'mean')
    ).sort_values('Messages', ascending=False).head(top_n)
    stats['Avg_Length'] = stats['Avg_Length'].round(1)
    return stats
"""
Sentiment scoring using VADER (Valence Aware Dictionary and sEntiment Reasoner).
Offline, no API calls, no tokens consumed.

Install: pip install vaderSentiment
VADER returns a compound score from -1.0 (maximally negative) to +1.0 (maximally positive).
"""
import os
import sys
import json
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "JSON Outputs")
OUTPUT_FILE = os.environ.get("SENTIMENT_OUTPUT", os.path.join(BASE_DIR, "sentiment_scores.json"))


def derive_category(compound, comment_type):
    """Map VADER compound score + comment type to a human-readable category."""
    if compound >= 0.4:
        return "praise"
    elif compound >= 0.05:
        # Positive-toned tip = a suggestion (not a complaint); positive top = praise
        return "suggestion" if comment_type == "tip" else "praise"
    elif compound > -0.1:
        return "neutral"
    elif compound > -0.5:
        # Mildly negative — typically a critique with nuance, mapped as constructive
        return "constructive"
    else:
        return "complaint"


def derive_intensity(compound):
    abs_c = abs(compound)
    if abs_c < 0.2:
        return "low"
    elif abs_c < 0.5:
        return "medium"
    else:
        return "high"


def collect_comments():
    comments = []
    seen_ids = set()
    for f in glob.glob(os.path.join(INPUT_DIR, "*.json")):
        with open(f, encoding='utf-8') as fh:
            data = json.load(fh)
        for g_data in data['tips_by_tutorial_group'].values():
            for c in g_data['comments']:
                if c['id'] not in seen_ids:
                    comments.append({"id": c['id'], "text": c['text'], "type": "tip"})
                    seen_ids.add(c['id'])
        for g_data in data['tops_by_tutorial_group'].values():
            for c in g_data['comments']:
                if c['id'] not in seen_ids:
                    comments.append({"id": c['id'], "text": c['text'], "type": "top"})
                    seen_ids.add(c['id'])
    return comments


def main():
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        import subprocess
        print("vaderSentiment not found — installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "vaderSentiment", "-q"])
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    comments = collect_comments()
    if not comments:
        print("No comments found in JSON Outputs.")
        return

    print(f"Scoring {len(comments)} comments with VADER (offline, no API)...")
    analyzer = SentimentIntensityAnalyzer()
    scores = {}

    for c in comments:
        result = analyzer.polarity_scores(c['text'])
        compound = result['compound']
        scores[c['id']] = {
            "valence":   round(compound, 4),
            "intensity": derive_intensity(compound),
            "category":  derive_category(compound, c['type']),
            "confidence": 1.0,
            "vader": {"neg": result['neg'], "neu": result['neu'], "pos": result['pos']},
        }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(scores)} sentiment scores to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()

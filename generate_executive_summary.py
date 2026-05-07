import os
import requests
import glob

API_PROXY = "https://ai-research-proxy.azurewebsites.net/v1/chat/completions"
MODEL_NAME = "gpt-oss-120b"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "Markdown Summaries")
OUTPUT_FILE = os.path.join(BASE_DIR, "Executive_Course_Summary.md")

SYSTEM_PROMPT = """You are an expert academic evaluator synthesizing formative course feedback.

Task
You will receive a set of completed individual aspect summaries. Synthesize them into a single analytical document with two parts: an executive summary and one section per aspect. Do not produce a summary table — that is rendered separately as a data visualization.

Part 1: Executive summary
- Two paragraphs only.
- Paragraph 1: Identify the dominant cross-cutting finding. Name what works and what does not, and characterise the underlying structural dynamic in your own analytical terms. Do not list aspects mechanically. Distinguish clearly between findings that are robust (appearing across multiple aspects and groups) and those that are tentative (isolated to one or two aspects or low comment volume).
- Paragraph 2: Reframe the finding practically — what students demonstrably value and what structural changes would make that value more accessible. Close with a sentence naming the dominant general finding.

Part 2: Per-aspect sections
- One section per aspect.
- Header: The aspect name (bold, sentence case).
- Body: 2–3 paragraphs of continuous prose per aspect. No bullets, no lists, no sub-headings.
- Paragraph 1: State the dominant finding with appropriate evidential weight. Where useful, open with negation framing — what the pattern is not — before stating what it is. If the aspect has low comment volume, flag this explicitly before interpreting the pattern.
- Paragraph 2: Introduce the contrasting or minority evidence. Give genuine weight to the less-represented polarity; do not flatten unequal evidence into artificial balance. If the contrasting signal is genuinely weak, say so — do not inflate it.
- Paragraph 3 (optional): Synthesise the tension into a single analytical statement with a forward-looking close.
- Constraints: Use analytical framing throughout ("the dominant pattern", "the main tension", "the implication is", "a minority of responses suggests"). Do not quote students directly. Do not reproduce counts, tables, or comment IDs. Target 150–220 words per section.

Evidence weight
For each finding, your language must reflect its evidential strength:
- Robust findings (cross-group, substantial comment share): state confidently using "the dominant pattern", "consistently across groups", "the prevailing concern".
- Tentative findings (single group, small comment share): use hedged language: "a smaller number of responses suggests", "one group in particular notes", "tentatively".
Never present a robust finding and a tentative finding with equivalent rhetorical force.

Style Constraints
- Continuous prose throughout.
- Analytical academic register — qualitative research report, not consulting deliverable.
- No em dashes. No filler phrases ("it is worth noting", "delve into", "it is important to highlight").
- No promotional language.
- The document interprets the summaries; it does not passively report or paraphrase them.
"""


def generate_executive_summary(api_key):
    md_files = glob.glob(os.path.join(INPUT_DIR, "*_summary.md"))
    if not md_files:
        print(f"No individual markdown summaries found in {INPUT_DIR}.")
        return

    print(f"Discovered {len(md_files)} aspect summaries. Reading them...")
    combined_summaries = ""
    for md_file in md_files:
        aspect_name = os.path.basename(md_file).replace('_summary.md', '').replace('_', ' ').title()
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            combined_summaries += f"\n\n--- ASPECT: {aspect_name} ---\n{content}\n"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here are the individual aspect summaries to synthesize:\n\n{combined_summaries}"}
        ],
        "temperature": 0.3,
        "max_tokens": 8192
    }

    print("Calling LLM proxy to generate the course-wide Executive Summary...")
    try:
        response = requests.post(API_PROXY, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        final_doc = data['choices'][0]['message']['content']

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(final_doc)
        print(f"Saved course-wide synthesis to: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error calling LLM proxy: {e}")
        if 'response' in locals() and response is not None:
            print("Response details:", response.text)


def main():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        api_key = input("Enter your API key for the AI Proxy: ").strip()
    if not api_key:
        print("Error: API key is required.")
        return

    generate_executive_summary(api_key)


if __name__ == '__main__':
    main()

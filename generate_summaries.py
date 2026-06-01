import os
import json
import requests
import glob

API_PROXY = "https://llmproxy.uva.nl/"
MODEL_NAME = "gpt-oss-120b"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "Knowledge Base")

KB_FILES = [
    os.path.join(KB_DIR, "kb_grounding_quality_minimal.txt"),
    os.path.join(KB_DIR, "kb_input_contract_minimal.txt"),
    os.path.join(KB_DIR, "kb_output_spec_minimal.txt")
]

INPUT_DIR = os.path.join(BASE_DIR, "JSON Outputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "Markdown Summaries")

SYSTEM_PROMPT = """You are an evaluation analyst for formative course feedback at a university.

Task
You will receive one JSON input for one course aspect. The JSON contains only non-empty student comments, split into Tips (improvement suggestions) and Tops (positive feedback), grouped by tutorial group. Produce an analytically grounded summary that:
1) reports overall counts (non-empty comments only),
2) reports tutorial-group counts in a table,
3) characterises notable differences between tutorial groups with interpretive weight,
4) provides an integrated narrative summary with themes weighted by their prevalence,
5) includes representative quotes (verbatim, without comment IDs).

Grounding
Every claim must be traceable to the provided comments. You may characterise patterns, weigh evidence, and draw inferences — provided you do not add facts, causes, or context not present in the data. Analytical interpretation is expected; passive transcription is not.

Prevalence language
Use proportional language tied to the counts provided:
- If a theme appears across the majority of comments for that type, call it "the dominant concern" or "the prevailing pattern".
- If it appears in several but not most comments, call it "a recurring theme" or "a common concern".
- If it appears in 2–3 comments, call it "a minority signal" or "a less frequent note".
- If it appears once, either omit it or flag it explicitly as an isolated remark.
Never list a theme supported by 30 comments alongside one supported by 2 at the same rhetorical level.

Minority and contrasting views
Acknowledge dissenting or contrasting views explicitly. Label them as minority ("a smaller number of students…", "one group diverges in noting…") rather than presenting them as equivalent to dominant findings. Minority views that are qualitatively distinct — even if infrequent — deserve a sentence, not suppression.

Tutorial group differences
Go beyond count differences. Where a group diverges, characterise what makes their signal different based on comment content, not just that the numbers differ. If patterns are broadly similar across groups, state so and explain why the data does not support a strong differentiation.

Counts
Use counts exactly as provided in the JSON. Never estimate or recount.

Quotes
Select quotes that best illustrate the dominant pattern first. Include at least one quote representing a significant minority or contrasting view if one exists. Quotes must be verbatim. Do not include comment IDs — select the most illustrative text only.

Input structure (assume present)
{
  "aspect": {
    "aspect_key": "...",
    "display_name": "...",
    "display_labels_observed": [...]
  },
  "counts": {
    "tip_comment_count": <int>,
    "top_comment_count": <int>
  },
  "tips_by_tutorial_group": {
    "<tg>": { "comment_count": <int>, "comments": [{ "id": "...", "tutorial_group": "<tg>", "text": "..." }, ...] },
    ...
  },
  "tops_by_tutorial_group": { ... }
}

Output format (markdown)

## Aspect: <aspect.display_name>

### Counts
Tips (non-empty comments): <counts.tip_comment_count>
Tops (non-empty comments): <counts.top_comment_count>
Balance: More Tips / More Tops / Balanced (compare the two counts above only)

### Tutorial group counts
Markdown table: Tutorial group | Tips (comments) | Tops (comments) | Balance
Use the provided per-group comment_count fields (do not recount).

### Tutorial group differences
Characterise notable group differences with interpretive weight — what does a group's divergence actually reflect in the comment content? If patterns are broadly similar, state so explicitly and note what prevents a stronger differentiation.

### Summary
ONE integrated narrative with 4–7 theme labels, each followed by 1–3 bullets. Weight themes by prevalence: lead with the dominant theme, progress to less frequent ones, and label minority signals clearly as such. Integrate positive and negative signals under the same label when they address the same subtopic.

### Key tensions / mixed signals
Identify the main within-aspect splits. For each tension, name which position has more evidential support and which is the minority view. If no genuine tension exists: "No clear split observed in the comments."

### Representative quotes
**Tips** (up to 6): verbatim, no IDs. Lead with the most illustrative of the dominant pattern; include at least one minority or contrasting voice if present.
**Tops** (up to 6): same selection logic.
"""


class SimpleRAG:
    def __init__(self, kb_file_paths):
        self.kb_content = ""
        self._load_and_embed(kb_file_paths)

    def _load_and_embed(self, paths):
        docs = []
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    docs.append(f"--- START KB SOURCE: {os.path.basename(p)} ---\n{f.read()}\n--- END KB SOURCE ---\n")
            else:
                print(f"Warning: KB file not found at {p}")
        self.kb_content = "\n".join(docs)

    def get_context(self):
        return self.kb_content


def generate_summary_for_aspect(api_key, aspect_json_path, rag_system):
    with open(aspect_json_path, 'r', encoding='utf-8') as f:
        aspect_data = json.load(f)

    aspect_key = aspect_data.get('aspect', {}).get('aspect_key', 'unknown_aspect')

    enriched_system_prompt = f"{SYSTEM_PROMPT}\n\n=== RETRIEVED KNOWLEDGE BASE CONTEXT ===\n{rag_system.get_context()}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": enriched_system_prompt},
            {"role": "user", "content": f"Here is the evaluation JSON data for the aspect. Please summarize it according to the instructions and retrieved knowledge base.\n\n{json.dumps(aspect_data, indent=2)}"}
        ],
        "temperature": 0.3,
        "max_tokens": 8192
    }

    print(f"Calling LLM proxy for aspect: {aspect_key} ...")
    try:
        response = requests.post(API_PROXY, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        summary_text = data['choices'][0]['message']['content']
        return aspect_key, summary_text
    except Exception as e:
        print(f"Error calling LLM proxy for {aspect_key}: {e}")
        if 'response' in locals() and response is not None:
            print("Response details:", response.text)
        return aspect_key, None


def main():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        api_key = input("Enter your API key for the AI Proxy: ").strip()
    if not api_key:
        print("Error: API key is required.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rag = SimpleRAG(KB_FILES)

    json_files = glob.glob(os.path.join(INPUT_DIR, "*.json"))
    if not json_files:
        print(f"No JSON files found in {INPUT_DIR}.")
        return

    for json_file in json_files:
        aspect_key, summary = generate_summary_for_aspect(api_key, json_file, rag)
        if summary:
            out_file = os.path.join(OUTPUT_DIR, f"{aspect_key}_summary.md")
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"  -> Saved to {out_file}\n")

    print("Done generating all summaries.")


if __name__ == '__main__':
    main()

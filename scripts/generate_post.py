"""
Auto blog post generator for LykofosAI.
Reads a topic from topics.txt, writes an article with Gemini,
fetches an image from Pexels, saves it as a Chirpy-compatible markdown post.
"""
import os
import re
import json
import random
import datetime
from pathlib import Path

import requests
from google import genai


# === Config ===
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
MODEL_NAME = "gemini-2.5-flash"

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "_posts"
TOPICS_FILE = REPO_ROOT / "topics.txt"


# === 1. Pick a topic ===
raw_topics = TOPICS_FILE.read_text(encoding="utf-8").splitlines()
topics = [t.strip() for t in raw_topics if t.strip() and not t.startswith("#")]
if not topics:
    print("No topics left in topics.txt. Nothing to post.")
    exit(0)
topic = random.choice(topics)
print(f"Selected topic: {topic}")


# === 2. Generate article with Gemini ===
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""Write a complete, engaging blog post about: {topic}

Requirements:
- 800-1200 words
- Compelling SEO-friendly title (under 60 chars)
- Conversational but authoritative tone
- 4-6 main sections with ## headings
- Practical, actionable content
- Include one personal anecdote or unique perspective
- End with a thought-provoking question for readers

Respond with ONLY valid JSON (no markdown code blocks, no extra text) in this exact format:
{{
  "title": "the blog post title (under 60 chars)",
  "description": "SEO meta description, 140-160 chars",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "category": "one of: AI, Travel, Finance, Lifestyle, Tech",
  "image_search": "2-3 word search term for stock photo matching post theme",
  "content": "full blog post body in markdown, no title heading, start with the intro paragraph"
}}"""

response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
raw = response.text.strip()
raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
raw = re.sub(r"\n?```\s*$", "", raw)

try:
    data = json.loads(raw)
except json.JSONDecodeError:
    # Try extracting content field separately to handle newlines
    content_match = re.search(r'"content"\s*:\s*"(.*?)"\s*\}', raw, re.DOTALL)
    if content_match:
        content_block = content_match.group(1)
        safe = raw[:content_match.start()] + '"content": ""}'
        data = json.loads(safe)
        data["content"] = content_block.replace('\\"', '"')
    else:
    print("Gemini returned invalid JSON:")
    print(raw[:500])
    raise

title = data["title"].strip()
description = data["description"].strip()
tags = data.get("tags", [])
category = data.get("category", "Lifestyle").strip()
image_search = data.get("image_search", topic).strip()
content = data["content"].strip()

print(f"Title: {title}")
print(f"Category: {category}")


# === 3. Fetch image from Pexels ===
image_url = None
image_alt = image_search
if PEXELS_API_KEY:
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": image_search, "per_page": 5, "orientation": "landscape"},
            headers={"Authorization": PEXELS_API_KEY},
            timeout=15,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if photos:
            chosen = random.choice(photos)
            image_url = chosen["src"]["large"]
            image_alt = chosen.get("alt") or image_search
            print(f"Image: {image_url}")
    except Exception as e:
        print(f"Image fetch failed (continuing without image): {e}")


# === 4. Build the markdown post ===
utc_now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
now = utc_now.astimezone(datetime.timezone(datetime.timedelta(hours=9)))  # KST
date_display = now.strftime("%Y-%m-%d %H:%M:%S +0900")
date_slug = now.strftime("%Y-%m-%d")

slug = re.sub(r"[^\w\s-]", "", title.lower())
slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:60] or "post"

filename = f"{date_slug}-{slug}.md"
post_path = POSTS_DIR / filename


def yaml_quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


tags_yaml = "[" + ", ".join(yaml_quote(t) for t in tags) + "]"

lines = [
    "---",
    f"title: {yaml_quote(title)}",
    f"date: {date_display}",
    f"categories: [{yaml_quote(category)}]",
    f"tags: {tags_yaml}",
    f"description: {yaml_quote(description)}",
]
if image_url:
    lines += [
        "image:",
        f"  path: {image_url}",
        f"  alt: {yaml_quote(image_alt)}",
    ]
lines += ["---", ""]

markdown = "\n".join(lines) + "\n" + content + "\n"


# === 5. Write the post ===
POSTS_DIR.mkdir(parents=True, exist_ok=True)
post_path.write_text(markdown, encoding="utf-8")
print(f"Created: {post_path.relative_to(REPO_ROOT)}")


# === 6. Remove used topic from topics.txt ===
remaining = [t for t in raw_topics if t.strip() != topic]
TOPICS_FILE.write_text("\n".join(remaining).rstrip() + "\n", encoding="utf-8")
print(f"Topics remaining: {len([t for t in remaining if t.strip() and not t.startswith('#')])}")

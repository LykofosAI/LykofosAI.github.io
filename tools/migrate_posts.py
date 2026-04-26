"""
One-time migration: convert Chirpy-format frontmatter to Minimal Mistakes format.
- Adds header.teaser + header.overlay_image from existing image.path
- Adds excerpt from existing description
- Keeps original image: block for safety
"""
import re
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"

migrated = 0
skipped = 0

for post in sorted(POSTS_DIR.glob("*.md")):
    text = post.read_text(encoding="utf-8")

    # Skip if already has header.teaser
    if re.search(r"^header:\s*\n\s+teaser:", text, re.MULTILINE):
        print(f"SKIP (already migrated): {post.name}")
        skipped += 1
        continue

    # Find image block (Chirpy format)
    img_match = re.search(
        r"^image:\s*\n\s+path:\s+(.+?)\n\s+alt:\s+(.+?)\n",
        text, re.MULTILINE
    )
    desc_match = re.search(r'^description:\s+"(.+?)"\s*$', text, re.MULTILINE)

    if not img_match:
        print(f"SKIP (no image block): {post.name}")
        skipped += 1
        continue

    image_url = img_match.group(1).strip().strip('"')
    image_alt = img_match.group(2).strip().strip('"')
    description = desc_match.group(1).strip() if desc_match else ""

    # Build new frontmatter additions
    additions = []
    if description:
        additions.append(f'excerpt: "{description}"')
    additions.append("header:")
    additions.append(f'  teaser: "{image_url}"')
    additions.append(f'  overlay_image: "{image_url}"')
    additions.append("  overlay_filter: 0.5")
    additions.append(f'  caption: "{image_alt}"')

    # Insert after the image: block (before the closing ---)
    end_of_image = img_match.end()
    new_text = text[:end_of_image] + "\n".join(additions) + "\n" + text[end_of_image:]

    post.write_text(new_text, encoding="utf-8")
    print(f"MIGRATED: {post.name}")
    migrated += 1

print(f"\nDone. Migrated: {migrated}, Skipped: {skipped}")

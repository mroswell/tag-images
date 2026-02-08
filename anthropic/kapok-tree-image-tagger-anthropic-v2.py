"""
Artwork Image Analyzer using Claude API
========================================
Analyzes hand-drawn artwork images and generates descriptions + tags,
saving results to a CSV file.

Improvements over the original version:
- Uses official Anthropic Python SDK (no raw requests)
- Structured JSON output (no fragile text parsing)
- Resume capability (skips already-processed images)
- Rate limiting with retry/backoff
- Lower temperature for consistent results
- Uses Sonnet for cost efficiency (Opus is overkill for descriptions)

Requirements:
    pip install anthropic Pillow tqdm

Usage:
    # Set your API key
    export ANTHROPIC_API_KEY="your-key-here"

    # Run from command line
    python analyze_artwork.py

    # Or import and customize
    from analyze_artwork import process_images
    process_images(image_dir="my_images", output_csv="my_results.csv")
"""

import os
import csv
import json
import time
import base64
from pathlib import Path

from PIL import Image
from tqdm import tqdm
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Configuration — edit these or pass as arguments to process_images()
# ---------------------------------------------------------------------------
DEFAULT_IMAGE_DIR = "../kapok_tree_images"
DEFAULT_OUTPUT_CSV = "artwork_descriptions_claude.csv"
MODEL = "claude-sonnet-4-5-20250929"  # Cost-effective; swap to opus if needed
MAX_TOKENS = 1024
TEMPERATURE = 0.0  # Low temp = consistent, factual descriptions
DELAY_BETWEEN_REQUESTS = 1.0  # Seconds between API calls (rate-limit safety)
MAX_RETRIES = 3
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# ---------------------------------------------------------------------------
# The prompt — asking Claude to return structured JSON
# ---------------------------------------------------------------------------
ANALYSIS_PROMPT = """You are analyzing a hand-drawn artwork image. 
(Don't worry about blank spaces — they will hold text when this becomes a book.)

Return your analysis as a JSON object with exactly these three keys:
- "short_description": A 1-2 sentence overview of the artwork.
- "long_description": A 4-5 sentence detailed description of the artwork.
- "tags": A comma-separated string of descriptive tags for this image.

Return ONLY the JSON object, no other text."""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_media_type(filepath: Path) -> str:
    """Return the MIME type based on file extension."""
    ext = filepath.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


def encode_image_base64(filepath: Path) -> str:
    """Read an image file and return its base64-encoded string."""
    return base64.b64encode(filepath.read_bytes()).decode("utf-8")


def get_orientation(filepath: Path) -> str:
    """Return 'landscape' or 'portrait' based on image dimensions."""
    with Image.open(filepath) as img:
        width, height = img.size
        return "landscape" if width > height else "portrait"


def load_existing_results(csv_path: Path) -> set:
    """Load filenames already present in the CSV so we can skip them."""
    if not csv_path.exists():
        return set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["filename"] for row in reader if row.get("filename")}


def analyze_image(client: Anthropic, filepath: Path) -> dict:
    """
    Send an image to Claude and get back structured descriptions.
    Retries on transient errors with exponential backoff.
    """
    b64_data = encode_image_base64(filepath)
    media_type = get_media_type(filepath)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ANALYSIS_PROMPT},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64_data,
                                },
                            },
                        ],
                    }
                ],
            )

            # Extract and parse JSON from response
            raw_text = response.content[0].text.strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]  # remove first line
                raw_text = raw_text.rsplit("```", 1)[0]  # remove closing fence
                raw_text = raw_text.strip()

            result = json.loads(raw_text)

            # Validate expected keys
            return {
                "short_description": result.get("short_description", ""),
                "long_description": result.get("long_description", ""),
                "tags": result.get("tags", ""),
            }

        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON parse error on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                print(f"  ✗ Could not parse response for {filepath.name}")
                return _error_result(f"JSON parse error: {e}")

        except Exception as e:
            error_msg = str(e)
            # Check for rate limit (429) or server errors (5xx) — retry those
            if any(code in error_msg for code in ["429", "500", "502", "503", "529"]):
                wait = 2 ** attempt * DELAY_BETWEEN_REQUESTS
                print(f"  ⚠ Retryable error on attempt {attempt}/{MAX_RETRIES}, "
                      f"waiting {wait:.0f}s: {error_msg[:100]}")
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    continue

            print(f"  ✗ Error analyzing {filepath.name}: {error_msg[:200]}")
            return _error_result(error_msg[:200])

    return _error_result("Max retries exceeded")


def _error_result(detail: str) -> dict:
    """Return a standardized error row."""
    return {
        "short_description": "Error analyzing image",
        "long_description": f"API error: {detail}",
        "tags": "error, failed_analysis",
    }


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------

def process_images(
    image_dir: str = DEFAULT_IMAGE_DIR,
    output_csv: str = DEFAULT_OUTPUT_CSV,
):
    """
    Scan image_dir for artwork images, analyze each with Claude,
    and append results to output_csv. Skips images already in the CSV.
    """
    image_dir = Path(image_dir)
    output_csv = Path(output_csv)

    if not image_dir.exists():
        print(f"✗ Directory not found: {image_dir}")
        return

    # Gather image files (sorted for predictable order)
    image_files = sorted(
        f for f in image_dir.iterdir()
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not image_files:
        print(f"✗ No supported images found in {image_dir}")
        return

    print(f"Found {len(image_files)} images in {image_dir}")

    # Check for already-processed files (resume support)
    already_done = load_existing_results(output_csv)
    to_process = [f for f in image_files if f.name not in already_done]

    if already_done:
        print(f"  ✓ {len(already_done)} already processed — resuming with "
              f"{len(to_process)} remaining")

    if not to_process:
        print("Nothing new to process!")
        return

    # Ensure output directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Initialize the Anthropic client (reads ANTHROPIC_API_KEY from env)
    client = Anthropic()

    # Open CSV in append mode if it already has content, else write header
    write_header = not output_csv.exists() or output_csv.stat().st_size == 0
    fieldnames = ["filename", "short_description", "long_description", "tags", "orientation"]

    with open(output_csv, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for img_path in tqdm(to_process, desc="Analyzing artwork"):
            orientation = get_orientation(img_path)
            analysis = analyze_image(client, img_path)

            writer.writerow({
                "filename": img_path.name,
                "short_description": analysis["short_description"],
                "long_description": analysis["long_description"],
                "tags": analysis["tags"],
                "orientation": orientation,
            })

            # Flush after each row so progress is saved even if we crash
            csvfile.flush()

            # Respect rate limits
            time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"\n✓ Done! Results saved to {output_csv}")
    print(f"  Total entries: {len(already_done) + len(to_process)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    process_images()

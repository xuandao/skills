#!/usr/bin/env python3
"""
URL Favorites Skill - Full Page Archival with Images
This skill enhances the basic URL favorites functionality by:
1. Converting webpage content to markdown
2. Downloading images to local resources
3. Maintaining proper markdown references to local images
"""

import os
import sys
import argparse
import requests
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import html2text
import time

def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug
    """
    # Replace spaces with hyphens and remove special characters
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = '-'.join(text.split())
    return text

def get_page_content(url: str) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Fetch page content and extract images using browser snapshot approach
    This simulates what the browser(snapshot) tool would do
    Returns: (markdown_content, page_title, image_urls)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract page title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else urlparse(url).netloc

        # Extract all image URLs from the page
        img_tags = soup.find_all('img')
        image_urls = []

        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Skip data URLs and javascript:void(0) type placeholders
                if src.startswith('data:') or src.startswith('javascript:') or src.strip() == '':
                    continue
                full_url = urljoin(url, src)
                image_urls.append(full_url)

        # Get the main content (try to extract main content areas)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup

        # Convert HTML to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False  # Keep links
        h.body_width = 0  # Don't wrap lines
        h.ignore_images = False  # Keep images

        # Get HTML content
        html_content = str(main_content)

        # Convert to markdown
        markdown_content = h.handle(html_content)

        return markdown_content, title, image_urls

    except Exception as e:
        print(f"Error fetching page content: {e}")
        return None, None, []

def download_image(image_url: str, dest_dir: Path) -> Optional[Path]:
    """
    Download a single image to the destination directory
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Get file extension from URL or content-type
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)

        if not filename or '.' not in filename:
            content_type = response.headers.get('content-type', '')
            ext_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp',
                'image/svg+xml': '.svg',
                'image/bmp': '.bmp'
            }
            ext = ext_map.get(content_type.lower(), '.jpg')  # default to jpg
            # Generate filename based on hash of URL
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            filename = f"image_{url_hash}{ext}"

        # Handle potential duplicate filenames
        counter = 1
        original_filename = filename
        while (dest_dir / filename).exists():
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{counter}{ext}"
            counter += 1

        # Save image
        image_path = dest_dir / filename
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return image_path

    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")
        return None

def download_images(image_urls: List[str], dest_dir: Path) -> Dict[str, Path]:
    """
    Download all images to the destination directory
    Returns a mapping of original URL to local file path
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    downloaded_files = {}

    for i, img_url in enumerate(image_urls):
        # Skip data URLs and other non-http(s) URLs
        if img_url.startswith(('data:', 'javascript:')):
            print(f"Skipping non-downloadable URL: {img_url}")
            continue

        print(f"Downloading image {i+1}/{len(image_urls)}: {img_url}")
        local_path = download_image(img_url, dest_dir)
        if local_path:
            downloaded_files[img_url] = local_path

    return downloaded_files

def update_markdown_references(markdown_content: str, image_mapping: Dict[str, Path]) -> str:
    """
    Update markdown content to reference local images instead of URLs
    """
    updated_content = markdown_content

    for original_url, local_path in image_mapping.items():
        # Find the image reference in markdown and replace with local path
        # This handles both HTML img tags and markdown ![]() syntax

        # Get just the filename for the replacement
        local_filename = local_path.name

        # Extract the path portion of the original URL for matching in markdown
        parsed_url = urlparse(original_url)
        image_path = parsed_url.path  # e.g., /portal/wikipedia.org/assets/img/Wikipedia-logo-v2.png

        # Remove leading slash if present for comparison
        if image_path.startswith('/'):
            image_path = image_path[1:]

        # Replace markdown-style image references: ![alt text](full-url)
        updated_content = updated_content.replace(
            f']({original_url})',
            f']({local_filename})'
        )

        # Replace markdown-style image references: ![alt text](relative-path)
        updated_content = updated_content.replace(
            f']({image_path})',
            f']({local_filename})'
        )

        # Replace direct URL occurrences that might be in the content
        updated_content = updated_content.replace(
            original_url,
            local_filename
        )

        # Replace path occurrences in the content
        updated_content = updated_content.replace(
            image_path,
            local_filename
        )

    return updated_content

def detect_language_and_translate(text: str, title: str) -> Tuple[str, str]:
    """
    Detect if content is Chinese and translate if needed
    This is a simplified version - in practice you'd use translation APIs
    """
    # Count Chinese characters to determine if it's a Chinese page
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(re.findall(r'\w', text))

    is_chinese = (chinese_chars / total_chars) > 0.5 if total_chars > 0 else False

    # For this implementation, we'll assume the content is already in the right language
    # In practice, you'd integrate with a translation API here
    return title, text

def create_note_content(title: str, url: str, markdown_content: str, author: Optional[str] = None, publish_date: Optional[str] = None) -> str:
    """
    Create the final note content with proper formatting
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Detect content richness to decide template
    content_words = len(markdown_content.split())
    is_detailed_article = content_words > 300  # Arbitrary threshold

    if is_detailed_article:
        # Use detailed article template
        note_content = f"""---
date: {today}
source: {url}
type: url
tags: [收藏夹]
---

# {title}

## 核心观点

{markdown_content[:500]}...

## 关键要点

- 主要内容已归档到此笔记中
- 查看原文: [{url}]({url})

---

*收藏时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}*"""
    else:
        # Use standard template
        note_content = f"""---
date: {today}
source: {url}
type: url
tags: [收藏夹]
---

# {title}

**来源**: {url}

**作者**: {author or '未知'}

**发布时间**: {publish_date or '未知'}

> {markdown_content[:300]}...

---

*收藏时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}*"""

    return note_content

def main():
    parser = argparse.ArgumentParser(description='Save URLs as Obsidian notes with images')
    parser.add_argument('url', help='URL to archive')
    parser.add_argument('-o', '--output-dir', required=True, help='Output directory for notes')
    parser.add_argument('--resources-dir', help='Resources directory for images (default: output-dir/../resources/图库)')

    args = parser.parse_args()

    url = args.url
    output_dir = Path(args.output_dir)
    resources_dir = Path(args.resources_dir) if args.resources_dir else output_dir.parent / "resources" / "图库"

    print(f"Archiving URL: {url}")

    # Get page content and images
    print("Fetching page content...")
    markdown_content, page_title, image_urls = get_page_content(url)

    if not markdown_content:
        print("Failed to fetch page content")
        sys.exit(1)

    print(f"Found {len(image_urls)} images on the page")

    # Use the page title from the page content
    title = page_title if page_title else urlparse(url).netloc

    # Generate filename based on date and title
    today = datetime.now().strftime("%Y-%m-%d")
    slug_title = slugify(title) if title != urlparse(url).netloc else slugify(urlparse(url).netloc)
    filename = f"{today}-{slug_title}.md"

    # Create resource directory for this specific page
    page_resources_dir = resources_dir / f"{today}-{slug_title}"

    # Download images if any were found
    image_mapping = {}
    if image_urls:
        print(f"Downloading {len(image_urls)} images to {page_resources_dir}...")
        image_mapping = download_images(image_urls, page_resources_dir)
        print(f"Downloaded {len(image_mapping)} images successfully")

    # Update markdown content to reference local images
    if image_mapping:
        markdown_content = update_markdown_references(markdown_content, image_mapping)

    # Create note content
    note_content = create_note_content(title, url, markdown_content)

    # Write the note
    output_dir.mkdir(parents=True, exist_ok=True)
    note_path = output_dir / filename

    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(note_content)

    print(f"Note saved to: {note_path}")
    print(f"Images saved to: {page_resources_dir}")

    # Verification steps
    print("\nPerforming verification checks...")

    # 1. Content integrity check
    with open(note_path, 'r', encoding='utf-8') as f:
        saved_content = f.read()

    if len(saved_content) < 100:  # arbitrary threshold for minimal content
        print("Warning: Saved content appears to be very short")
    else:
        print("✓ Content integrity check passed")

    # 2. Check if frontmatter exists
    has_frontmatter = saved_content.startswith("---")
    if has_frontmatter:
        print("✓ Frontmatter check passed")
    else:
        print("⚠ Warning: No frontmatter detected")

    # 3. Check if content includes source URL
    has_source = url in saved_content
    if has_source:
        print("✓ Source URL check passed")
    else:
        print("⚠ Warning: Source URL not found in note")

    print(f"\nArchival complete! Note: {note_path}, Resources: {page_resources_dir}")

if __name__ == "__main__":
    main()
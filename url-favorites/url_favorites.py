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

        # Pre-process image tags to ensure we have the best source and absolute URLs
        img_tags = soup.find_all('img')
        image_urls = []

        for img in img_tags:
            # Try to find the real image source (handling lazy loading)
            src = (
                img.get('data-src') or 
                img.get('data-lazy-src') or 
                img.get('data-original') or
                img.get('src')
            )
            
            if src:
                if src.startswith('data:') or src.startswith('javascript:') or src.strip() == '':
                    continue
                
                full_url = urljoin(url, src)
                image_urls.append(full_url)
                # Update the src attribute in the soup so html2text uses the absolute URL
                img['src'] = full_url

        # Get the main content
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_='content') or 
            soup.find('div', id='content') or 
            soup.find('div', role='main') or 
            soup.find('div', class_='post-content') or
            soup.find('div', class_='entry-content') or
            soup
        )

        # Convert HTML to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.body_width = 0
        h.ignore_images = False
        h.protect_links = True
        h.unicode_snob = True
        h.wrap_links = False
        h.pad_tables = True
        h.mark_code = True
        h.ignore_emphasis = False
        h.bypass_tables = False
        h.escape_snob = True

        # Convert to markdown
        markdown_content = h.handle(str(main_content))

        return markdown_content, title, list(set(image_urls))  # Deduplicate

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

def update_markdown_references(markdown_content: str, image_mapping: Dict[str, Path], rel_path: str = "") -> str:
    """
    Update markdown content to reference local images instead of URLs
    """
    updated_content = markdown_content
    from urllib.parse import quote

    for original_url, local_path in image_mapping.items():
        # Get the final path to use in markdown
        local_filename = local_path.name
        final_markdown_path = os.path.join(rel_path, local_filename) if rel_path else local_filename

        # Replace markdown-style image references: ![alt text](full-url)
        # We also handle URL encoded versions because html2text might encode them
        encoded_url = quote(original_url, safe=':/')

        updated_content = updated_content.replace(f'({original_url})', f'({final_markdown_path})')
        updated_content = updated_content.replace(f'({encoded_url})', f'({final_markdown_path})')

        # Also replace HTML-style src attributes if any
        updated_content = updated_content.replace(f'src="{original_url}"', f'src="{final_markdown_path}"')
        updated_content = updated_content.replace(f'src="{encoded_url}"', f'src="{final_markdown_path}"')

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
    Create the final note content with proper formatting, ensuring full content is preserved.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Generate a summary (first 500 chars) for the top section
    summary_limit = 500
    summary = markdown_content[:summary_limit].strip()
    if len(markdown_content) > summary_limit:
        summary += "..."

    # Detection for rich content format
    content_words = len(markdown_content.split())
    is_detailed_article = content_words > 300

    if is_detailed_article:
        note_content = f"""---
date: {today}
source: {url}
type: url
tags: [收藏夹]
---

# {title}

## 摘要
> {summary}

---

## 核心内容

{markdown_content}

---

*收藏时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}*
*原文链接: [{url}]({url})*"""
    else:
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

---

{markdown_content}

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
        # Calculate relative path from output_dir to page_resources_dir
        rel_resources_path = os.path.relpath(page_resources_dir, output_dir)
        markdown_content = update_markdown_references(markdown_content, image_mapping, rel_resources_path)

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
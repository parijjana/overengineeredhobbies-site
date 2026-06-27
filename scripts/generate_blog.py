import os
import re
import datetime
import json

# ── CONFIGURATION ──────────────────────────────────────────────────────────
SOURCE_DIR = "blog"
OUTPUT_DIR = "blog/posts"
INDEX_FILE = "templates/base_index.html"
TEMPLATE_FILE = "templates/blog_post_template.html"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("templates", exist_ok=True)

# ── MARKDOWN PARSER ─────────────────────────────────────────────────────────
def parse_inline(text):
    # Bold / Underline nesting like **<u>**text**</u>**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    return text

def markdown_to_html(md_text):
    html_lines = []
    # Standardize newlines and split into blocks by blank lines
    blocks = md_text.replace('\r\n', '\n').strip().split('\n\n')
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Headers
        if block.startswith('## '):
            header_text = block[3:].strip()
            html_lines.append(f"<h2>{header_text}</h2>")
        elif block.startswith('# '):
            header_text = block[2:].strip()
            html_lines.append(f"<h1>{header_text}</h1>")
        elif block.startswith('### '):
            header_text = block[4:].strip()
            html_lines.append(f"<h3>{header_text}</h3>")
        # Bullet points
        elif block.startswith('- ') or block.startswith('* '):
            list_items = []
            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    item_text = line[2:].strip()
                    list_items.append(f"<li>{parse_inline(item_text)}</li>")
            html_lines.append(f"<ul>{''.join(list_items)}</ul>")
        # Blockquotes
        elif block.startswith('> '):
            quote_lines = [line.strip().lstrip('> ').strip() for line in block.split('\n')]
            quote_text = '<br>'.join(quote_lines)
            html_lines.append(f"<blockquote>{parse_inline(quote_text)}</blockquote>")
        # Standard paragraphs
        else:
            # Preserve paragraphs but convert single newlines to spacing/br
            lines = [line.strip() for line in block.split('\n')]
            paragraph_text = ' '.join(lines)  # Join with spaces for standard flow
            html_lines.append(f"<p>{parse_inline(paragraph_text)}</p>")
            
    return '\n'.join(html_lines)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

# ── PARSE POST FRONTMATTER / CONTENT ────────────────────────────────────────
def parse_post(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()
        
    metadata = {}
    content = raw_content
    
    # Parse YAML-like frontmatter if present
    if raw_content.startswith("---"):
        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            content = parts[2].strip()
            
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip().lower()] = val.strip()

    # Fallbacks for metadata
    filename = os.path.basename(file_path)
    default_title = os.path.splitext(filename)[0]
    
    # Extract date from mtime or use current date
    mtime = os.path.getmtime(file_path)
    file_date = datetime.date.fromtimestamp(mtime).strftime("%Y-%m-%d")
    
    title = metadata.get("title", default_title)
    date = metadata.get("date", file_date)
    tags_raw = metadata.get("tags", "General")
    tags = [t.strip().upper() for t in tags_raw.split(",")]
    
    # Generate slug and excerpt
    slug = slugify(default_title)
    
    # Get short plain-text excerpt
    plain_text = re.sub(r'[#\*_`<u><\/u>]', '', content)
    first_paragraph = plain_text.strip().split('\n\n')[0]
    # Clean indentation/extra whitespace
    first_paragraph = ' '.join(first_paragraph.split())
    excerpt = first_paragraph[:160] + "..." if len(first_paragraph) > 160 else first_paragraph
    
    html_content = markdown_to_html(content)
    
    return {
        "title": title,
        "date": date,
        "tags": tags,
        "slug": slug,
        "excerpt": excerpt,
        "html_content": html_content
    }

# ── TEMPLATES ──────────────────────────────────────────────────────────────
BLOG_POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — overengineeredhobbies.dev</title>
  <link rel="icon" type="image/png" href="../../assets/favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Fira+Code:wght@300;400;500;600&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #08111f;
      --surface: #0d1a2e;
      --surface-raised: #112238;
      --grid-major: rgba(78,140,220,0.10);
      --grid-minor: rgba(78,140,220,0.05);
      --border: rgba(78,140,220,0.20);
      --border-bright: rgba(78,140,220,0.45);
      --text: #8aaed0;
      --text-dim: #3f5f85;
      --text-bright: #ddeeff;
      --accent: #e8a020;
      --accent-dim: rgba(232, 160, 32, 0.1);
      --font-display: 'Bebas Neue', sans-serif;
      --font-mono: 'Fira Code', monospace;
      --font-body: 'Lora', serif;
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      background-image:
        linear-gradient(var(--grid-major) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-major) 1px, transparent 1px),
        linear-gradient(var(--grid-minor) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-minor) 1px, transparent 1px);
      background-size: 80px 80px, 80px 80px, 16px 16px, 16px 16px;
      background-attachment: fixed;
      min-height: 100vh;
    }}

    nav {{
      height: 60px;
      background: rgba(8,17,31,0.92);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 2rem; position: sticky; top: 0; z-index: 100;
    }}
    .nav-logo {{
      font-family: var(--font-mono); font-size: 13px; color: var(--accent); text-decoration: none;
    }}
    .nav-logo span {{ color: var(--text-dim); }}

    main {{
      max-width: 900px;
      margin: 0 auto;
      padding: 4rem 2rem;
      min-height: calc(100vh - 60px);
    }}

    .blog-container {{
      background: rgba(13, 26, 46, 0.6);
      border: 1px solid var(--border);
      padding: 4rem;
      backdrop-filter: blur(10px);
    }}

    .label {{
      font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);
      letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.5rem;
      display: flex; align-items: center; gap: 0.75rem;
    }}
    .label::before {{ content: ''; display: block; width: 24px; height: 1px; background: var(--accent); }}

    h1 {{
      font-family: var(--font-display);
      font-size: clamp(3rem, 6vw, 4.5rem);
      color: var(--text-bright);
      line-height: 1.1;
      margin-bottom: 1rem;
      letter-spacing: 0.02em;
    }}

    .meta-row {{
      display: flex;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 3rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.5rem;
    }}
    .post-date {{
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--accent);
    }}
    .tag-container {{
      display: flex; gap: 0.5rem;
    }}
    .tag {{
      font-family: var(--font-mono); font-size: 10px; padding: 2px 8px;
      border: 1px solid var(--border); color: var(--text); background: var(--surface-raised);
    }}

    .blog-content h2 {{
      font-family: var(--font-display);
      font-size: 2rem;
      color: var(--text-bright);
      margin: 3rem 0 1rem;
      letter-spacing: 0.05em;
    }}

    .blog-content p {{
      margin-bottom: 1.75rem;
      line-height: 1.9;
      color: var(--text);
      font-size: 1.05rem;
      text-indent: 1.5rem; /* Give indent style for creative prose */
    }}
    
    .blog-content p:first-of-type {{
      text-indent: 0; /* No indent on first paragraph */
    }}
    
    .blog-content ul {{
      margin-bottom: 1.5rem;
      padding-left: 1.5rem;
      list-style-type: none;
    }}
    .blog-content li {{
      margin-bottom: 0.75rem;
      line-height: 1.6;
      position: relative;
    }}
    .blog-content li::before {{
      content: '•';
      color: var(--accent);
      position: absolute;
      left: -1.25rem;
    }}

    .btn-back {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--accent);
      text-decoration: none;
      padding: 10px 20px;
      border: 1px solid var(--accent);
      transition: all 0.2s;
      margin-top: 3rem;
    }}
    .btn-back:hover {{
      background: var(--accent-dim);
      box-shadow: 0 0 15px var(--accent-dim);
    }}

    @media (max-width: 768px) {{
      .blog-container {{ padding: 2rem; }}
      main {{ padding: 2rem 1rem; }}
      .blog-content p {{ text-indent: 0; }} /* Remove indent on small screens */
    }}
  </style>
</head>
<body>

<nav>
  <a href="../../index.html" class="nav-logo">oeh<span>.dev</span></a>
  <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);">PROJECT_ID: BLOG_POST</div>
</nav>

<main>
  <article class="blog-container">
    <div class="label">FIELD NOTES & MUSINGS</div>
    <h1>{title}</h1>
    <div class="meta-row">
      <div class="post-date">LOG DATE: {date}</div>
      <div class="tag-container">
        {tag_html}
      </div>
    </div>

    <div class="blog-content">
      {html_content}
    </div>

    <a href="../../index.html#blog" class="btn-back">← BACK TO HOME</a>
  </article>
</main>

</body>
</html>
"""

# ── COMPILER ENGINE ─────────────────────────────────────────────────────────
def compile_blog():
    # Save template to file
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        f.write(BLOG_POST_TEMPLATE)
        
    print("Scanning for markdown posts...")
    posts = []
    
    for filename in os.listdir(SOURCE_DIR):
        if filename.endswith(".md"):
            file_path = os.path.join(SOURCE_DIR, filename)
            print(f"Parsing post: {filename}")
            post_data = parse_post(file_path)
            posts.append(post_data)
            
            # Generate the HTML page
            tag_html = "".join([f'<span class="tag">{t}</span>' for t in post_data["tags"]])
            
            html_page = BLOG_POST_TEMPLATE.format(
                title=post_data["title"],
                date=post_data["date"],
                tag_html=tag_html,
                html_content=post_data["html_content"]
            )
            
            output_file = os.path.join(OUTPUT_DIR, f"{post_data['slug']}.html")
            with open(output_file, "w", encoding="utf-8") as out:
                out.write(html_page)
            print(f"  + Generated {output_file}")
            
    # Sort posts by date descending
    posts.sort(key=lambda x: x["date"], reverse=True)
    
    # Update index.html blog section with compiled list
    update_home_index(posts)

def update_home_index(posts):
    if not os.path.exists(INDEX_FILE):
        print(f"Error: {INDEX_FILE} not found. Cannot inject blog lists.")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_content = f.read()

    # Generate the cards HTML
    cards = []
    for i, post in enumerate(posts):
        tag_html = "".join([f'<span class="tag">{t}</span>' for t in post["tags"]])
        delay = i * 0.07
        cards.append(f"""
    <div class="blog-card reveal" style="transition-delay:{delay:.2f}s">
      <div class="blog-date">LOG DATE: {post['date']}</div>
      <div class="blog-title">{post['title']}</div>
      <p class="blog-excerpt">{post['excerpt']}</p>
      <div class="card-tags" style="margin-bottom:0.75rem">
        {tag_html}
      </div>
      <a href="blog/posts/{post['slug']}.html" class="card-link">READ FULL REPORT →</a>
    </div>""")

    cards_html = "\n".join(cards)
    
    # Now let's construct/update the blog section on index.html
    # We want to uncomment and inject the posts
    blog_section_template = f"""<!-- ── BLOG ───────────────────────────────────────────── -->
<section id="blog">
  <p class="section-label">SECTION 04 — FIELD NOTES &amp; MUSINGS <span class="rev-stamp">REV A</span></p>
  <h2 class="section-title">BLOG</h2>
  <div class="blog-grid">
{cards_html}
  </div>
</section>"""

    # We will search index.html for either:
    # 1. An existing active <section id="blog">...
    # 2. Or the commented out blog section.
    
    pattern_active = r'<!-- ── BLOG ───────────────────────────────────────────── -->\s*<section id="blog">.*?</section>'
    pattern_commented = r'<!-- ── BLOG ───────────────────────────────────────────── -->\s*<!--\s*<section id="blog">.*?</section>\s*-->'
    
    if re.search(pattern_active, index_content, re.DOTALL):
        print("Found active blog section in index.html, updating content...")
        new_content = re.sub(pattern_active, blog_section_template, index_content, flags=re.DOTALL)
    elif re.search(pattern_commented, index_content, re.DOTALL):
        print("Found commented-out blog section in index.html, uncommenting and updating...")
        new_content = re.sub(pattern_commented, blog_section_template, index_content, flags=re.DOTALL)
    else:
        # Fallback: find footer and insert right before it
        print("Blog section placeholder not found. Inserting before <footer>...")
        footer_pattern = r'<!-- ── FOOTER ─────────────────────────────────────────── -->'
        if footer_pattern in index_content:
            new_content = index_content.replace(footer_pattern, f"{blog_section_template}\n\n{footer_pattern}")
        else:
            print("Could not find blog hook points in index.html.")
            return
            
    # Also uncomment/add the navigation link if it's commented out
    nav_link_active = r'<a href="#blog">~/blog</a>'
    nav_link_commented = r'<!--\s*<a href="#blog">~/blog</a>\s*-->'
    
    if re.search(nav_link_commented, new_content):
        print("Uncommenting the blog nav link in index.html...")
        new_content = re.sub(nav_link_commented, nav_link_active, new_content)
        
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully updated index.html with the compiled blog list!")

if __name__ == "__main__":
    compile_blog()

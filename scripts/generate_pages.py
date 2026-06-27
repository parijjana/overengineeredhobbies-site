import json
import os
import re
import db

def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"

def clean_text(text):
    if not text: return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = text.replace("• ", "• ").replace("* ", "• ").replace("- ", "• ")
    text = text.replace("<br>", "\n").replace("\n", "<br>")
    return text

def build_tags_html(tags_list):
    if not tags_list:
        return ""
    return "".join([f'<span class="tag">{t.strip().upper()}</span>' for t in tags_list if t.strip()])

def get_primary_language(stack_str):
    if not stack_str:
        return "DART"
    tags = [s.strip().upper() for s in stack_str.split(",") if s.strip()]
    if "PYTHON" in tags:
        return "PYTHON"
    for t in tags:
        if "JS" in t or "JAVASCRIPT" in t or "NODE" in t or "TS" in t or "TYPESCRIPT" in t:
            return "JAVASCRIPT"
    return "DART"

def render_template(template_str, tokens):
    result = template_str
    for key, val in tokens.items():
        result = result.replace(f"{{{key}}}", str(val or ""))
    return result

def generate_pages():
    # Load configuration
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Load templates
    templates_dir = "templates"
    project_template_path = os.path.join(templates_dir, "base_project.html")
    index_template_path = os.path.join(templates_dir, "base_index.html")

    if not os.path.exists(project_template_path) or not os.path.exists(index_template_path):
        print("Error: HTML templates not found in templates/ directory.")
        return

    with open(project_template_path, "r", encoding="utf-8") as f:
        project_template = f.read()

    with open(index_template_path, "r", encoding="utf-8") as f:
        index_template = f.read()

    # Query projects from SQLite registry
    projects = db.get_all_projects()
    if not projects:
        print("No projects registered in the database.")
        return

    # Sort projects based on project_order in config.json
    project_order = config["projects"].get("project_order", [])
    if project_order:
        order_map = {name.lower(): idx for idx, name in enumerate(project_order)}
        projects.sort(key=lambda p: order_map.get(p["repo_name"].lower(), 999))

    # Resolve output directory dynamically based on config paths
    prod_dir = config.get("paths", {}).get("prod_website_directory")
    if prod_dir and os.path.exists(prod_dir):
        projects_dir = os.path.join(prod_dir, "projects")
        index_path = os.path.join(prod_dir, "index.html")
    else:
        projects_dir = "projects"
        index_path = "index.html"

    os.makedirs(projects_dir, exist_ok=True)

    project_cards = []
    app_cards = []

    # Original delay sequences to preserve layout feel
    project_delays = [0, 0.05, 0.1, 0.12, 0.18, 0.2, 0.22]
    app_delays = [0, 0.07, 0.14]

    for idx, proj in enumerate(projects):
        project_key = proj["project_key"]
        repo_name = proj["repo_name"]
        name = proj["name"]
        demo_path = proj.get("demo_path")
        
        # Color Logic
        accent = config["projects"]["accent_colors"].get(repo_name, config["site"]["default_accent_color"])
        accent_dim = hex_to_rgba(accent, 0.10)

        # Tags HTML
        tags_raw = [s.strip() for s in proj["stack"].split(",") if s.strip()]
        stack_html = build_tags_html(tags_raw)
        primary_lang = get_primary_language(proj["stack"])
        
        # Favicon Url
        favicon_url = "../assets/favicon.png"
        for asset in proj.get("assets", []):
            if asset["asset_type"] == "icon":
                ext = os.path.splitext(asset["original_name"])[1] or ".png"
                favicon_url = f"../assets/media/{asset['asset_key']}{ext}"
                break

        # External Links
        github_url = proj["github_url"] or f"https://github.com/{config['owner']['github_username']}/{repo_name}"
        playstore_url = proj["playstore_url"]
        playstore_html = f'<a href="{playstore_url}" class="btn-github">VIEW ON PLAY STORE →</a>' if playstore_url else ""
        
        # Web Demo Link
        demo_html = f'<a href="../{demo_path}" class="btn-github" style="color:var(--accent); border-color:var(--accent);">TRY WEB DEMO →</a>' if demo_path else ""
        
        # Auto-detect local privacy policy file in projects/ directory
        privacy_filename = f"{repo_name.lower()}_privacy.html"
        privacy_filepath = os.path.join(projects_dir, privacy_filename)
        privacy_url = privacy_filename if os.path.exists(privacy_filepath) else None
        privacy_html = f'<a href="{privacy_url}" class="btn-github">PRIVACY POLICY →</a>' if privacy_url else ""

        # Auto-detect blog post file in blog/posts/ directory
        blog_filename = None
        blog_dir = "blog/posts"
        if os.path.exists(blog_dir):
            for f in os.listdir(blog_dir):
                if f.endswith(".html") and repo_name.lower() in f.lower():
                    blog_filename = f"../blog/posts/{f}"
                    break
        blog_html = f'<a href="{blog_filename}" class="btn-github">READ DEV BLOG →</a>' if blog_filename else ""

        # Timeline HTML
        timeline_items = []
        done_features = sorted([f for f in proj["features"] if f["status"] == "done"], 
                                key=lambda x: x["completed_date"] or "0000-00-00", reverse=True)
        todo_features = [f for f in proj["features"] if f["status"] == "todo"]

        for feat in done_features:
            timeline_items.append(f"""
      <div class="timeline-item">
        <span class="timeline-date">{feat['completed_date'] or 'COMPLETED'}</span>
        <div class="timeline-content">
          <h3>{clean_text(feat['name'])}</h3>
        </div>
      </div>""")

        for feat in todo_features:
            timeline_items.append(f"""
      <div class="timeline-item planned">
        <span class="timeline-date">UPCOMING</span>
        <div class="timeline-content">
          <h3>{clean_text(feat['name'])}</h3>
        </div>
      </div>""")

        # Compile project detail page HTML
        project_tokens = {
            "title": name,
            "project_id": repo_name.upper().replace("_ANDROID", ""),
            "accent_color": accent,
            "accent_dim_color": accent_dim,
            "stack_html": stack_html,
            "github_url": github_url,
            "playstore_html": playstore_html,
            "demo_html": demo_html,
            "privacy_html": privacy_html,
            "blog_html": blog_html,
            "favicon_url": favicon_url,
            "about_text": clean_text(proj.get("about") or "Project documentation in progress."),
            "philosophy_text": clean_text(proj.get("philosophy") or ""),
            "architecture_text": proj.get("architecture") or "Architecture diagram pending.",
            "capabilities_text": clean_text(proj.get("capabilities") or ""),
            "timeline_html": "".join(timeline_items),
            "site_title_suffix": config["site"]["title_suffix"],
            "site_logo_text": config["site"]["logo_text"],
            "site_logo_sub": config["site"]["logo_sub"]
        }

        html_content = render_template(project_template, project_tokens)

        # Output page to projects directory
        output_path = os.path.join(projects_dir, f"{repo_name.lower()}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated {output_path}")

        # ----------------- Build Card Lists for index.html -----------------
        # Project Card delay style
        p_delay = project_delays[idx] if idx < len(project_delays) else 0.25
        p_delay_style = f' style="transition-delay:{p_delay}s"' if p_delay > 0 else ""

        # Project Card Demo Action Link
        demo_link_html = ""
        if demo_path:
            demo_link_html = f' · <a href="{demo_path}" class="card-link" style="color: var(--accent);">TRY DEMO →</a>'

        proj_card = f"""
    <div class="card reveal"{p_delay_style}>
      <div class="card-header">
        <div class="card-title" style="font-family:var(--font-mono);font-size:0.95rem;font-weight:400">
          <span style="color:var(--text-dim)">{config['owner']['github_username']} /</span> {name.upper()}
        </div>
        <div class="card-badge">PUBLIC</div>
      </div>
      <div class="card-meta">
        <span>★ 0</span>
        <span>⑂ 0</span>
        <span style="color:#7ec8e3">{primary_lang}</span>
      </div>
      <p>{proj.get('about') or ''}</p>
      <div class="card-tags">
        {stack_html}
      </div>
      <a href="projects/{repo_name.lower()}.html" class="card-link">VIEW PROJECT DETAILS →</a>{demo_link_html}
    </div>"""
        project_cards.append(proj_card)

        # App Card HTML (check if registered as an app in config)
        app_meta = config["projects"]["app_metadata"].get(repo_name.lower())
        if app_meta:
            app_idx = len(app_cards)
            a_delay = app_delays[app_idx] if app_idx < len(app_delays) else 0.20
            a_delay_style = f' style="transition-delay:{a_delay}s"' if a_delay > 0 else ""

            # App metadata details from config
            app_title = app_meta["title"]
            app_badge = app_meta["badge"]
            app_version = app_meta["version"]
            app_platform = app_meta["platform"]
            app_extra = app_meta.get("extra", "")
            app_about = app_meta["about"]
            app_tags_html = build_tags_html(app_meta["tags"])

            extra_span = f"<span>{app_extra}</span>" if app_extra else ""
            
            # Setup specific links for the app cards
            if repo_name.lower() == "pellucid":
                demo_btn = f'<a href="{demo_path}" class="card-link" style="margin-top: 0; color: var(--accent);">TRY DEMO →</a>' if demo_path else ""
                links_html = f"""
      <div style="display: flex; gap: 8px; margin-top: 1rem; flex-wrap: wrap; align-items: center;">
        <a href="{github_url}/releases" class="card-link" style="margin-top: 0;">⊞ WINDOWS .exe</a>
        {demo_btn}
        <a href="projects/{repo_name.lower()}.html" class="card-link" style="margin-top: 0; color: var(--text-dim);">DETAILS →</a>
      </div>"""
            elif repo_name.lower() == "contexthistory":
                demo_btn = f'<a href="{demo_path}" class="card-link" style="margin-top: 0; color: var(--accent);">TRY DEMO →</a>' if demo_path else ""
                links_html = f"""
      <div style="display: flex; gap: 8px; margin-top: 1rem; flex-wrap: wrap; align-items: center;">
        <a href="{github_url}" class="card-link" style="margin-top: 0;">📦 INSTALL</a>
        {demo_btn}
        <a href="projects/{repo_name.lower()}.html" class="card-link" style="margin-top: 0; color: var(--text-dim);">DETAILS →</a>
      </div>"""
            else:
                demo_btn = f'<a href="{demo_path}" class="card-link" style="margin-top: 0; color: var(--accent);">TRY DEMO →</a>' if demo_path else ""
                links_html = f"""
      <div style="display: flex; gap: 8px; margin-top: 1rem; flex-wrap: wrap; align-items: center;">
        <a href="projects/{repo_name.lower()}.html" class="card-link" style="margin-top: 0;">VIEW DETAILS →</a>
        {demo_btn}
      </div>"""

            app_card = f"""
    <div class="card reveal"{a_delay_style}>
      <div class="card-header">
        <div class="card-title">{app_title}</div>
        <div class="card-badge">{app_badge}</div>
      </div>
      <div class="card-meta">
        <span>{app_version}</span>
        <span>{app_platform}</span>
        {extra_span}
      </div>
      <p>{app_about}</p>
      <div class="card-tags">
        {app_tags_html}
      </div>
      {links_html}
    </div>"""
            app_cards.append(app_card)

    # Compile and output index.html using render_template
    index_tokens = {
        "owner_name": config["owner"]["name"],
        "owner_github_username": config["owner"]["github_username"],
        "owner_linkedin_url": config["owner"]["linkedin_url"],
        "cv_path": config["owner"]["cv_download_path"],
        "site_title_suffix": config["site"]["title_suffix"],
        "site_logo_text": config["site"]["logo_text"],
        "site_logo_sub": config["site"]["logo_sub"],
        "site_footer_note": config["site"]["footer_note"],
        "project_cards": "\n".join(project_cards),
        "app_cards": "\n".join(app_cards)
    }

    compiled_index = render_template(index_template, index_tokens)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(compiled_index)
    print(f"Generated {index_path} successfully!")

if __name__ == "__main__":
    generate_pages()

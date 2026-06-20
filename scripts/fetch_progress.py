import urllib.request
import re
import json
import os
import sys

# ── CONFIGURATION ──────────────────────────────────────────────────────────
# Add the exact repository names you want to track here.
# The script will only attempt to fetch FEATURE_TRACKER.md for these repos.
REPOS = [
    "lore",
    "thesign",
    "contexthistory",
    "pellucid",
    "KALKRA",
    "AULOS",
    "GASTROTATOR_ANDROID"
]

USER = "parijjana"
BASE_URL = "https://raw.githubusercontent.com/{user}/{repo}/main/FEATURE_TRACKER.md"
OUTPUT_FILE = "assets/projects_data.json"
LOCATIONS_FILE = "PROJECT_LOCATIONS.md"
TIMEOUT = 10 # Seconds

# ────────────────────────────────────────────────────────────────────────────

def get_local_paths():
    paths = {}
    if os.path.exists(LOCATIONS_FILE):
        with open(LOCATIONS_FILE, "r") as f:
            for line in f:
                match = re.match(r'\|\s*(.*?)\s*\|\s*`(.*?)`\s*\|', line)
                if match:
                    # Map both the display name and the directory name if possible
                    name = match.group(1).strip()
                    path = match.group(2).strip()
                    paths[name.lower()] = path
                    paths[os.path.basename(path).lower()] = path
    return paths

import shutil

def fetch_project_favicon(repo, local_path):
    dest_path = f"assets/favicon_{repo.lower()}.png"
    
    # Try local first
    if local_path:
        for possible_name in ["favicon.png", "assets/favicon.png"]:
            src_path = os.path.join(local_path, possible_name)
            if os.path.exists(src_path):
                print(f"  * Copying local favicon for {repo} from {src_path}")
                try:
                    shutil.copy2(src_path, dest_path)
                    return f"../{dest_path}"
                except Exception as e:
                    print(f"  * Error copying local favicon: {e}")
                    
    # Try GitHub
    for possible_url_path in ["favicon.png", "assets/favicon.png"]:
        url = f"https://raw.githubusercontent.com/{USER}/{repo}/main/{possible_url_path}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                print(f"  * Downloading remote favicon for {repo} from {url}")
                with open(dest_path, "wb") as f:
                    f.write(response.read())
                return f"../{dest_path}"
        except Exception:
            pass
            
    return None

def fetch_and_parse(repo, local_paths):
    content = None
    local_path = local_paths.get(repo.lower())
    
    # Try local first
    if local_path:
        tracker_path = os.path.join(local_path, "FEATURE_TRACKER.md")
        if os.path.exists(tracker_path):
            print(f"Reading {repo} from local path: {tracker_path}")
            with open(tracker_path, "r", encoding="utf-8") as f:
                content = f.read()
    
    # Fallback to GitHub
    if not content:
        url = BASE_URL.format(user=USER, repo=repo)
        print(f"Fetching {repo} data from GitHub...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                content = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  - Skipping {repo}: FEATURE_TRACKER.md not found locally or on GitHub.")
            else:
                print(f"  - Error fetching {repo} from GitHub (HTTP {e.code}): {e.reason}")
            return None
        except Exception as e:
            print(f"  - Unexpected error for {repo}: {e}")
            return None

    # Parse Content
    try:
        # 1. Parse About Section
        about_match = re.search(r'##\s+About\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        about_text = about_match.group(1).strip() if about_match else ""
        
        # 2. Parse Stack Section
        stack_match = re.search(r'##\s+Stack\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        stack_list = [s.strip().upper() for s in stack_match.group(1).split(',')] if stack_match else []
        
        # 3. Parse External Links
        github_match = re.search(r'##\s+GitHub\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        github_url = github_match.group(1).strip() if github_match else f"https://github.com/{USER}/{repo}"
        
        playstore_match = re.search(r'##\s+PlayStore\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        playstore_url = playstore_match.group(1).strip() if playstore_match else None

        # 4. Parse Rich Metadata
        philosophy_match = re.search(r'##\s+Philosophy\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        philosophy_text = philosophy_match.group(1).strip() if philosophy_match else ""

        architecture_match = re.search(r'##\s+Architecture\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        architecture_text = architecture_match.group(1).strip() if architecture_match else ""

        capabilities_match = re.search(r'##\s+Capabilities\s+(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        capabilities_text = capabilities_match.group(1).strip() if capabilities_match else ""

        # 5. Parse Features
        # Matches: - [x] 2026-06-15: Feature Name OR - [ ] Feature Name
        features = []
        lines = content.split('\n')
        for line in lines:
            # Check for implemented with date
            done_match = re.match(r'^\s*-\s+\[x\]\s*((\d{4}-\d{2}-\d{2}):)?\s*(.*?)$', line, re.IGNORECASE)
            if done_match:
                features.append({
                    "name": done_match.group(3).strip(),
                    "date": done_match.group(2),
                    "status": "done"
                })
                continue
            
            # Check for planned
            todo_match = re.match(r'^\s*-\s+\[\s\]\s*(.*?)$', line)
            if todo_match:
                features.append({
                    "name": todo_match.group(1).strip(),
                    "date": None,
                    "status": "todo"
                })

        if not features:
            print(f"  ! Found FEATURE_TRACKER.md for {repo} but no features defined.")
            return None
            
        implemented_count = len([f for f in features if f['status'] == 'done'])
        percentage = round((implemented_count / len(features) * 100), 1)
        
        favicon_path = fetch_project_favicon(repo, local_path)
        
        # Auto-detect local privacy policy file in website projects/ directory
        privacy_filename = f"{repo.lower()}_privacy.html"
        privacy_filepath = os.path.join("projects", privacy_filename)
        privacy_url = privacy_filename if os.path.exists(privacy_filepath) else None
        
        print(f"  + Success: {implemented_count}/{len(features)} features tracked.")
        return {
            "about": about_text,
            "stack": stack_list,
            "philosophy": philosophy_text,
            "architecture": architecture_text,
            "capabilities": capabilities_text,
            "links": {
                "github": github_url,
                "playstore": playstore_url,
                "favicon": favicon_path,
                "privacy": privacy_url
            },
            "features": features,
            "percentage": percentage,
            "stats": {
                "implemented": implemented_count,
                "total": len(features)
            }
        }
    except Exception as e:
        print(f"  - Parsing error for {repo}: {e}")
        return None

def main():
    # Use CLI arguments if provided, otherwise use the default REPOS list
    target_repos = sys.argv[1:] if len(sys.argv) > 1 else REPOS
    
    if not target_repos:
        print("No repositories specified. Please provide repo names as arguments or update REPOS in the script.")
        return

    # Ensure assets directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    local_paths = get_local_paths()
    results = {}
    print(f"Starting progress synchronization for {USER}...")
    
    for repo in target_repos:
        data = fetch_and_parse(repo, local_paths)
        if data:
            results[repo] = data
    
    # Save the successful results
    if results:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDone! Progress data for {len(results)} projects saved to {OUTPUT_FILE}")
    else:
        print("\nNo progress data fetched. Output file not updated.")

if __name__ == "__main__":
    main()

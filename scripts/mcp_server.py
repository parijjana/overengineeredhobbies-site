import os
import json
import traceback
import subprocess
import shutil
from mcp.server.fastmcp import FastMCP

import sys
# Ensure the scripts directory is in path
sys.path.append(os.path.dirname(__file__))

import db
import generate_pages

# Initialize FastMCP Server
mcp = FastMCP("Portfolio", dependencies=["sqlite3"])

@mcp.tool()
def list_projects() -> str:
    """
    List all tracked projects in the portfolio registry.
    Returns a JSON string containing project keys, names, repo names, and local paths.
    """
    try:
        projects = db.get_all_projects()
        simple_list = []
        for p in projects:
            simple_list.append({
                "project_key": p["project_key"],
                "name": p["name"],
                "repo_name": p["repo_name"],
                "local_path": p["local_path"]
            })
        return json.dumps(simple_list, indent=2)
    except Exception as e:
        return f"Error listing projects: {str(e)}\n{traceback.format_exc()}"

@mcp.tool()
def get_project(project_key: str) -> str:
    """
    Get full details of a specific project by its project key (e.g. PRJ001).
    Returns a JSON string of project info, features, and assets.
    """
    try:
        project = db.get_project_by_key(project_key)
        if not project:
            return f"Error: Project with key '{project_key}' not found."
        return json.dumps(project, indent=2)
    except Exception as e:
        return f"Error getting project details: {str(e)}"

@mcp.tool()
def register_project(name: str, repo_name: str, local_path: str) -> str:
    """
    Register a new project in the portfolio.
    Generates a unique project key (e.g. PRJ001).
    """
    try:
        project_key = db.register_project(name, repo_name, local_path)
        return f"Success: Registered project '{name}' with key: {project_key}"
    except Exception as e:
        return f"Error registering project: {str(e)}"

@mcp.tool()
def update_project_profile(
    project_key: str, 
    about: str = None, 
    stack: str = None, 
    github_url: str = None, 
    playstore_url: str = None, 
    philosophy: str = None, 
    architecture: str = None, 
    capabilities: str = None
) -> str:
    """
    Update the descriptive profile details of a registered project.
    Only provided fields will be updated. stack must be a comma-separated list of tags.
    """
    try:
        db.update_project_profile(
            project_key, 
            about=about, 
            stack=stack, 
            github_url=github_url, 
            playstore_url=playstore_url, 
            philosophy=philosophy, 
            architecture=architecture, 
            capabilities=capabilities
        )
        return f"Success: Updated profile for project '{project_key}'."
    except Exception as e:
        return f"Error updating project profile: {str(e)}"

@mcp.tool()
def update_project_features(project_key: str, features_json: str) -> str:
    """
    Replace the roadmap features for a project.
    features_json: A JSON string containing a list of feature objects,
    e.g. '[{"name": "Implement core logic", "status": "done", "date": "2026-06-15"}, {"name": "TDD Tests", "status": "todo"}]'
    """
    try:
        features_list = json.loads(features_json)
        db.update_project_features(project_key, features_list)
        return f"Success: Updated {len(features_list)} features for project '{project_key}'."
    except json.JSONDecodeError:
        return "Error: features_json must be a valid JSON array of feature objects."
    except Exception as e:
        return f"Error updating features: {str(e)}"

@mcp.tool()
def store_project_asset(project_key: str, asset_type: str, file_path: str, label: str = None) -> str:
    """
    Store an asset (icon, banner, screenshot_phone, screenshot_tablet, screenshot_desktop) for a project.
    Copies the file to the central asset store renamed to its SHA-256 hash (Rule 11) and updates the database registry.
    file_path: The absolute local file path of the source asset.
    """
    try:
        asset_hash, dest_path = db.store_project_asset(project_key, asset_type, file_path, label)
        return json.dumps({
            "status": "success",
            "asset_key": asset_hash,
            "destination_path": dest_path,
            "message": f"Registered '{asset_type}' asset with content hash key: {asset_hash}"
        }, indent=2)
    except FileNotFoundError as fnf:
        return f"Error: Source file not found: {str(fnf)}"
    except ValueError as ve:
        return f"Error: Validation failed: {str(ve)}"
    except Exception as e:
        return f"Error storing asset: {str(e)}"

@mcp.tool()
def build_and_deploy_demo(project_key: str) -> str:
    """
    Build a Flutter web release build of the project with compile-time flag IS_DEMO=true,
    then copy the web assets to the portfolio website's demos/ folder, and update DB.
    Automatically rebuilds the portfolio index and project subpages.
    """
    try:
        # 1. Retrieve project profile
        proj = db.get_project_by_key(project_key)
        if not proj:
            return f"Error: Project with key '{project_key}' not found."
            
        local_path = proj["local_path"]
        repo_name = proj["repo_name"]
        
        if not local_path or not os.path.exists(local_path):
            return f"Error: Project local path '{local_path}' does not exist on this device."
            
        # 2. Verify it's a Flutter project
        pubspec_path = os.path.join(local_path, "pubspec.yaml")
        if not os.path.exists(pubspec_path):
            return f"Error: Local path '{local_path}' does not contain a pubspec.yaml. Demos can only be compiled for Flutter projects."
            
        print(f"Starting Flutter web build for {proj['name']} in {local_path}...")
        
        # 3. Compile the Flutter web release build with IS_DEMO=true
        cmd = f"flutter build web --release --dart-define=IS_DEMO=true --base-href /demos/{repo_name.lower()}/"
        # Use shell=True for Windows environments to resolve command aliases
        process = subprocess.run(cmd, cwd=local_path, capture_output=True, text=True, shell=True)
        
        if process.returncode != 0:
            return json.dumps({
                "status": "failed",
                "message": f"Flutter compilation failed for {proj['name']}.",
                "stdout": process.stdout,
                "stderr": process.stderr
            }, indent=2)
            
        # 4. Copy build/web directory to the production website demos directory
        src_web_dir = os.path.join(local_path, "build", "web")
        if not os.path.exists(src_web_dir):
            return f"Error: Compiled web folder not found at '{src_web_dir}' after successful build command."
            
        db_path = db.get_database_path()
        website_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
        dest_demo_dir = os.path.join(website_dir, "demos", repo_name.lower())
        
        os.makedirs(dest_demo_dir, exist_ok=True)
        # Clear existing contents if any to do a clean overwrite
        if os.path.exists(dest_demo_dir):
            shutil.rmtree(dest_demo_dir)
        shutil.copytree(src_web_dir, dest_demo_dir)
        
        # 5. Save the relative demo path to the database
        demo_rel_path = f"demos/{repo_name.lower()}/index.html"
        db.update_project_demo_path(project_key, demo_rel_path)
        
        # 6. Rebuild the website pages to compile the "TRY WEB DEMO" buttons
        generate_pages.generate_pages()
        
        return json.dumps({
            "status": "success",
            "message": f"Flutter web demo compiled and deployed successfully to {dest_demo_dir}.",
            "demo_path": demo_rel_path,
            "stdout": process.stdout
        }, indent=2)
        
    except Exception as e:
        return f"Error building and deploying demo: {str(e)}\n{traceback.format_exc()}"

@mcp.tool()
def generate_store_listing(project_key: str, store_type: str) -> str:
    """
    Generate store listing metadata for a project.
    store_type: 'play_store' or 'microsoft_store'
    """
    try:
        proj = db.get_project_by_key(project_key)
        if not proj:
            return f"Error: Project with key '{project_key}' not found."
            
        listing = {
            "name": proj["name"],
            "short_description": (proj["about"][:80] + "...") if proj["about"] else "",
            "full_description": proj["about"] or "",
            "capabilities": proj["capabilities"] or "",
            "assets": []
        }
        
        # Populate assets associated with this project
        for asset in proj.get("assets", []):
            listing["assets"].append({
                "type": asset["asset_type"],
                "file_path": f"assets/media/{asset['asset_key']}{os.path.splitext(asset['original_name'])[1]}",
                "label": asset["label"]
            })
            
        return json.dumps({
            "store": store_type.upper(),
            "project_key": project_key,
            "metadata": listing
        }, indent=2)
    except Exception as e:
        return f"Error generating store listing: {str(e)}"

@mcp.tool()
def rebuild_portfolio() -> str:
    """
    Run the compiler to rebuild index.html and all project subpages based on the latest database values.
    """
    try:
        generate_pages.generate_pages()
        return "Success: Rebuilt portfolio index.html and all project subpages successfully."
    except Exception as e:
        return f"Error rebuilding portfolio: {str(e)}"

if __name__ == "__main__":
    mcp.run()

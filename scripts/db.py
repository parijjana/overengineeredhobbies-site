import sqlite3
import os
import hashlib
import uuid
import json

SCHEMA_FILE = "scripts/schema.sql"

def get_database_path():
    # Load config.json if it exists to locate production directory
    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            prod_dir = config.get("paths", {}).get("prod_website_directory")
            if prod_dir and os.path.exists(prod_dir):
                return os.path.join(prod_dir, "portfolio.db")
        except Exception:
            pass
    return "portfolio.db"

def get_connection():
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), SCHEMA_FILE)
    if not os.path.exists(schema_path):
        schema_path = SCHEMA_FILE
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

def generate_key(prefix, cursor=None):
    # Generates a clean unique short alphanumeric identifier
    # Prefix should be 'PRJ' or 'FEAT' (Rule 9)
    if cursor:
        if prefix == 'PRJ':
            cursor.execute("SELECT COUNT(*) FROM projects")
            count = cursor.fetchone()[0]
            return f"PRJ{count + 1:03d}"
        elif prefix == 'FEAT':
            cursor.execute("SELECT COUNT(*) FROM features")
            count = cursor.fetchone()[0]
            return f"FEAT{count + 1:05d}"
            
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if prefix == 'PRJ':
            cursor.execute("SELECT COUNT(*) FROM projects")
            count = cursor.fetchone()[0]
            return f"PRJ{count + 1:03d}"
        elif prefix == 'FEAT':
            cursor.execute("SELECT COUNT(*) FROM features")
            count = cursor.fetchone()[0]
            return f"FEAT{count + 1:05d}"
    finally:
        conn.close()
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

def calculate_sha256(file_path):
    # Generates stable cryptographic content-based identifier (Rule 11)
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def register_project(name, repo_name, local_path):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Check if already exists
        cursor.execute("SELECT project_key FROM projects WHERE repo_name = ?", (repo_name.lower(),))
        row = cursor.fetchone()
        if row:
            return row[0]
            
        project_key = generate_key('PRJ', cursor=cursor)
        cursor.execute(
            """INSERT INTO projects (project_key, name, repo_name, local_path) 
               VALUES (?, ?, ?, ?)""",
            (project_key, name, repo_name.lower(), local_path)
        )
        conn.commit()
        return project_key
    finally:
        conn.close()

def get_project_by_key(project_key):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE project_key = ?", (project_key,))
        proj = cursor.fetchone()
        if not proj:
            return None
            
        project_data = dict(proj)
        
        # Load features
        cursor.execute("SELECT * FROM features WHERE project_key = ?", (project_key,))
        project_data["features"] = [dict(row) for row in cursor.fetchall()]
        
        # Load assets
        cursor.execute("SELECT * FROM assets WHERE project_key = ?", (project_key,))
        project_data["assets"] = [dict(row) for row in cursor.fetchall()]
        
        return project_data
    finally:
        conn.close()

def get_all_projects():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        projects = []
        for row in cursor.fetchall():
            proj_dict = dict(row)
            # Load features
            cursor.execute("SELECT * FROM features WHERE project_key = ?", (proj_dict["project_key"],))
            proj_dict["features"] = [dict(f) for f in cursor.fetchall()]
            # Load assets
            cursor.execute("SELECT * FROM assets WHERE project_key = ?", (proj_dict["project_key"],))
            proj_dict["assets"] = [dict(a) for a in cursor.fetchall()]
            projects.append(proj_dict)
        return projects
    finally:
        conn.close()

def update_project_profile(project_key, about=None, stack=None, github_url=None, playstore_url=None, demo_path=None, philosophy=None, architecture=None, capabilities=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        
        fields = {
            "about": about,
            "stack": stack,
            "github_url": github_url,
            "playstore_url": playstore_url,
            "demo_path": demo_path,
            "philosophy": philosophy,
            "architecture": architecture,
            "capabilities": capabilities,
            "updated_at": "CURRENT_TIMESTAMP"
        }
        
        for k, v in fields.items():
            if v is not None:
                if k == "updated_at":
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                else:
                    updates.append(f"{k} = ?")
                    params.append(v)
                    
        if not updates:
            return
            
        params.append(project_key)
        cursor.execute(f"UPDATE projects SET {', '.join(updates)} WHERE project_key = ?", params)
        conn.commit()
    finally:
        conn.close()

def update_project_features(project_key, features_list):
    # Replaces all roadmap features for the project
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM features WHERE project_key = ?", (project_key,))
        
        for feat in features_list:
            feat_key = generate_key('FEAT', cursor=cursor)
            cursor.execute(
                """INSERT INTO features (feature_key, project_key, name, status, completed_date) 
                   VALUES (?, ?, ?, ?, ?)""",
                (feat_key, project_key, feat["name"], feat["status"], feat.get("completed_date") or feat.get("date"))
            )
        conn.commit()
    finally:
        conn.close()

def store_project_asset(project_key, asset_type, source_file_path, label=None):
    if not os.path.exists(source_file_path):
        raise FileNotFoundError(f"Source file {source_file_path} not found.")
        
    asset_hash = calculate_sha256(source_file_path)
    ext = os.path.splitext(source_file_path)[1].lower()
    
    # Store under assets/media/<hash>.<ext> relative to the resolved database path
    db_path = get_database_path()
    website_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
    dest_dir = os.path.join(website_dir, "assets", "media")
    os.makedirs(dest_dir, exist_ok=True)
    dest_filename = f"{asset_hash}{ext}"
    dest_path = os.path.join(dest_dir, dest_filename)
    
    # Copy file if not exists
    if not os.path.exists(dest_path):
        import shutil
        shutil.copy2(source_file_path, dest_path)
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Verify project exists
        cursor.execute("SELECT name FROM projects WHERE project_key = ?", (project_key,))
        if not cursor.fetchone():
            raise ValueError(f"Project with key {project_key} does not exist.")
            
        # Register or update asset metadata in DB
        cursor.execute(
            """INSERT OR REPLACE INTO assets (asset_key, project_key, asset_type, original_name, mime_type, label) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (asset_hash, project_key, asset_type, os.path.basename(source_file_path), f"image/{ext.replace('.', '')}", label)
        )
        conn.commit()
        return asset_hash, f"assets/media/{dest_filename}"
    finally:
        conn.close()

def update_project_demo_path(project_key, demo_path):
    update_project_profile(project_key, demo_path=demo_path)


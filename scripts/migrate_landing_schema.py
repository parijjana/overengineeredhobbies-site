"""Bring portfolio.db up to the content model the 2026-08-03 landing page needs.

GENERATOR_PLAN.md §1 — "The content model is a generation behind" — names this as
the entire reason index.html is hand-maintained: portfolio.db carries
about/philosophy/architecture/capabilities, shaped for the OLD project-page design,
while the landing page needs status, platforms, problem/approach/outcome, store
links and legal URLs.

This adds those, plus two cheap items the plan already asked for:
  Step 2 - projects.slug, so page filenames stop deriving from repo_name
  Step 3 - projects.claims_verified_at, the hook for a staleness check

What this does NOT do, deliberately:
  - It does not touch index.html, and does not make it generated. Step 0 of the
    plan promotes SKIP_INDEX to documented design; the landing page stays
    hand-written. This DB is the source of truth for the content, not its renderer.
  - It does not rewrite the generator. Plan: "Do not rewrite the generator."
  - It does not drop about/philosophy/architecture/capabilities - the project
    pages still render from those.

Idempotent: safe to re-run.

Usage:  python3 scripts/migrate_landing_schema.py [--db portfolio.db]
"""

import argparse
import os
import sqlite3

# --- Card content, transcribed verbatim from the live index.html -------------
# Prose stays authored, not derived. Inline HTML (<code>, <strong>, &nbsp;) is
# preserved as-is, matching how `capabilities` already stores <br>.

SITE_KEY = "PRJ008"

CARDS = {
    "PRJ005": dict(  # KALKRA
        slug="kalkra", display_name="KALKRA",
        platforms="macOS · iOS · Windows",
        status_kind="live", status_label="Live on the Mac App Store",
        claim="A mental-arithmetic trainer that reads how fast you actually solve, "
              "and re-tunes its difficulty in real time.",
        problem="Fixed-difficulty drill apps are either boring or discouraging, "
                "because they never learn the player's actual ceiling.",
        approach="A calibration engine that measures solve latency per operation type "
                 "and adjusts live. Fully offline and single-player — no accounts, no "
                 "network, no telemetry in store builds.",
        outcome="Live on the Mac App Store, with a truthful “Data Not Collected” "
                "privacy declaration. iOS is next; Windows and Android follow.",
        landing_order=1, claims_verified_at="2026-08-04",
        tags=["FLUTTER", "GAME ENGINE", "OFFLINE-FIRST"],
        links=[("action", "Mac App Store →", "https://apps.apple.com/app/kalkra/id6790438978", 1),
               ("action", "Live demo", "/demos/kalkra/", 0),
               ("action", "Source", "https://github.com/parijjana/Kalkra", 0),
               ("action", "Project page", "/projects/kalkra.html", 0),
               ("legal", "Privacy", "/projects/kalkra_privacy.html", 0),
               ("legal", "Support", "/projects/kalkra_support.html", 0)],
        shots=[("game", "Kalkra — gameplay", "landscape"),
               ("dashboard", "Kalkra — dashboard", "landscape"),
               ("mode-select", "Kalkra — mode select", "landscape"),
               ("stats", "Kalkra — stats", "landscape"),
               ("mobile-dashboard", "Kalkra — dashboard (mobile)", "portrait"),
               ("mobile-stats", "Kalkra — stats (mobile)", "portrait")],
        shot_dir="kalkra",
    ),
    "PRJ007": dict(  # GASTROTATOR — display name and slug both differ from repo_name
        slug="gastrotator", display_name="GASTROTATOR",
        platforms="Android",
        status_kind="live", status_label="Live on Google Play",
        claim="Turns a twelve-minute cooking video into a structured, editable recipe "
              "with nutritional estimates — the most technically involved thing here, "
              "and the one you can install right now.",
        problem="The recipe in a cooking video is buried in twelve minutes of talking, "
                "in no fixed order, with quantities stated casually or not at all. "
                "Transcribing one by hand costs more than cooking from it.",
        approach="A pipeline: pull the transcript, have Gemini extract ingredients, "
                 "quantities and ordered steps, normalise units to SI, then estimate "
                 "calories and weights. The hard part isn't the model call — it's "
                 "forcing non-deterministic output into a schema stable enough to "
                 "store, edit and trust.",
        outcome="Shipped and live on Google Play. Less visually polished than the "
                "other two; considerably more complex underneath.",
        landing_order=2, claims_verified_at="2026-08-03",
        tags=["FLUTTER", "GEMINI", "SQLITE", "AI PIPELINE"],
        links=[("action", "Google Play →", "https://play.google.com/store/apps/details?id=com.gastrotator.app", 1),
               ("action", "Source", "https://github.com/parijjana/gastrotator_android", 0),
               ("action", "Project page", "/projects/gastrotator.html", 0)],
        shots=[("recipe-detail", "Gastrotator — recipe detail", "landscape"),
               ("home", "Gastrotator — library", "landscape"),
               ("settings", "Gastrotator — settings", "landscape"),
               ("mobile-recipe", "Gastrotator — recipe (phone)", "portrait"),
               ("mobile-home", "Gastrotator — library (phone)", "portrait")],
        shot_dir="gastrotator",
    ),
    "PRJ004": dict(  # PELLUCID
        slug="pellucid", display_name="PELLUCID",
        platforms="macOS · Windows · iOS",
        status_kind="review", status_label="In review",
        claim="A distraction-free writing environment whose interface fades out of the "
              "writer's way — and syncs their manuscript without ever holding it hostage.",
        problem="Writing apps interrupt flow with chrome, and cloud sync usually means "
                "surrendering your files to a proprietary store.",
        approach="A translucent “Whisper UI” that recedes while typing, over plain "
                 "Markdown on disk. Versioned Google&nbsp;Drive sync using only the "
                 "<code>drive.file</code> scope — the app can touch nothing it didn't create.",
        outcome="Submitted to the Mac App Store; iOS and iPad builds green with "
                "keyboard-first interaction and OAuth via ASWebAuthenticationSession.",
        landing_order=3, claims_verified_at="2026-08-03",
        tags=["FLUTTER", "SQLITE", "OAUTH 2.0", "DESKTOP"],
        links=[("action", "Live demo", "/demos/pellucid/", 1),
               ("action", "Source", "https://github.com/parijjana/pellucid", 0),
               ("action", "Project page", "/projects/pellucid.html", 0),
               ("legal", "Privacy", "/projects/pellucid_privacy.html", 0),
               ("legal", "Support", "/projects/pellucid_support.html", 0),
               ("legal", "Terms", "/projects/pellucid_terms.html", 0)],
        shots=[("editor", "Pellucid — editor", "landscape"),
               ("research-notes", "Pellucid — research notes", "landscape"),
               ("snapshots", "Pellucid — snapshots", "landscape"),
               ("table-of-contents", "Pellucid — table of contents", "landscape"),
               ("mobile-editor", "Pellucid — editor (mobile)", "portrait"),
               ("mobile-research-notes", "Pellucid — research notes (mobile)", "portrait")],
        shot_dir="pellucid",
    ),
    "PRJ006": dict(  # AULOS
        slug="aulos", display_name="AULOS",
        platforms="Windows · macOS",
        status_kind="dev", status_label="Research — not for stores",
        claim="The bedrock. At ~44,000 lines it is very nearly as much code as all "
              "three shipped apps combined — and the reason they were quick to build.",
        problem="Music, podcasts and audiobooks each want different controls, different "
                "resume behaviour and a different sense of progress — yet players "
                "usually force one model onto all three. Separately: I needed somewhere "
                "to work out architecture properly, without a release date attached.",
        approach="A pure-Dart domain layer with the data layer behind it, and "
                 "strategy-pattern playback so the UI reconfigures itself per media type "
                 "rather than branching everywhere. Native thread-safety guarding for "
                 "Windows, and async disposal protection throughout.",
        outcome="Deliberately never submitted anywhere. The layering, playback "
                "abstraction and resilience patterns proven here are reused across the "
                "store apps — <strong>they ship fast because this one didn't have to</strong>.",
        landing_order=4, claims_verified_at="2026-08-03",
        tags=["FLUTTER", "DRIFT", "WINRT", "DOMAIN LAYER"],
        links=[("action", "Source", "https://github.com/parijjana/Aulos", 0),
               ("action", "Project page", "/projects/aulos.html", 0)],
        shots=[("01_now_playing_music", "Aulos — now playing, music", "landscape"),
               ("02_now_playing_audiobook", "Aulos — now playing, audiobook", "landscape"),
               ("03_library_album_grid", "Aulos — library", "landscape"),
               ("04_mood_dashboard", "Aulos — mood dashboard", "landscape"),
               ("05_ambient_noise_mixer", "Aulos — ambient noise mixer", "landscape")],
        shot_dir="aulos",
    ),
    SITE_KEY: dict(  # this site — had no projects row at all before now
        slug="overengineeredhobbies-site", display_name="OVERENGINEEREDHOBBIES.DEV",
        platforms="Web",
        status_kind="live", status_label="Live — you're in it",
        claim="This page. A portfolio that is itself a build — generated from a "
              "database, no frameworks, deployed to the edge.",
        problem="A portfolio that lists projects flatly says nothing about judgment — "
                "and hand-maintained project pages rot the moment the work moves on.",
        # NOTE: this Approach text is KNOWN-STALE. GENERATOR_PLAN.md Step 0 flags it:
        # it claims templates generate "the static pages", which is false of the
        # landing page the reader is standing on. Stored verbatim so the DB mirrors
        # what is actually live; claims_verified_at is set to NULL to mark it unverified.
        approach="Project data lives in SQLite; Python templates generate the static "
                 "pages. No framework, no build chain, no client-side rendering. "
                 "Theming is CSS custom properties, so a new palette is fifteen lines.",
        outcome="Live on Cloudflare. The smallest build here by far — included because "
                "the structure of this page is itself the argument.",
        landing_order=5, claims_verified_at=None,
        tags=["PYTHON", "SQLITE", "CLOUDFLARE", "NO FRAMEWORKS"],
        links=[("action", "Source", "https://github.com/parijjana/overengineeredhobbies-site", 0)],
        shots=[("work-paper", "The Work, drafting-paper theme", "landscape"),
               ("method-blueprint", "The Method, blueprint theme", "landscape"),
               ("work-terminal", "The Work, terminal theme", "landscape"),
               ("method-paper", "The Method, drafting-paper theme", "landscape")],
        shot_dir="site",
        has_project_page=0,
        about="The portfolio site itself: a static site generated from SQLite by "
              "Python templates, themed with CSS custom properties and served from "
              "Cloudflare's edge.",
        stack="PYTHON, SQLITE, CLOUDFLARE, NO FRAMEWORKS",
        repo_name="overengineeredhobbies-site",
        github_url="https://github.com/parijjana/overengineeredhobbies-site",
        # local_path is NOT NULL and every existing row stores the Windows-side path
        # (the work happens on two machines). Kept in that convention for consistency.
        local_path=r"D:\Programming\geminicli\overengineeredhobbies-site",
    ),
}

# Projects in the DB that are deliberately NOT landing-page cards.
OFF_LANDING = ["PRJ001", "PRJ003"]  # LORE, CONTEXTHISTORY

NEW_COLUMNS = [
    ("slug", "TEXT"),               # Step 2 - drives filenames; repo_name means only "the GitHub repo"
    ("display_name", "TEXT"),       # card title; GASTROTATOR vs repo GASTROTATOR_ANDROID
    ("appstore_url", "TEXT"),
    ("platforms", "TEXT"),          # "macOS · iOS · Windows"
    ("status_kind", "TEXT"),        # live | review | dev  -> the CSS class on the pill
    ("status_label", "TEXT"),       # "Live on the Mac App Store"
    ("claim", "TEXT"),              # the one-line build-claim
    ("problem", "TEXT"),
    ("approach", "TEXT"),
    ("outcome", "TEXT"),
    ("on_landing", "INTEGER NOT NULL DEFAULT 0"),
    ("landing_order", "INTEGER"),
    ("has_project_page", "INTEGER NOT NULL DEFAULT 1"),
    ("claims_verified_at", "TEXT"),  # Step 3 - NULL means "never verified"
]


def column_names(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def migrate(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    existing = column_names(conn, "projects")
    for name, decl in NEW_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE projects ADD COLUMN {name} {decl}")
            print(f"  + projects.{name}")

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS project_tags (
        project_key TEXT NOT NULL REFERENCES projects(project_key) ON DELETE CASCADE,
        position    INTEGER NOT NULL,
        label       TEXT NOT NULL,
        PRIMARY KEY (project_key, position)
    );

    -- One table for both link rows on a card. group_name 'action' is the main row
    -- (store / demo / source / project page); 'legal' is the smaller privacy row.
    -- is_primary marks the emphasised link - the store link where one exists.
    CREATE TABLE IF NOT EXISTS project_links (
        project_key TEXT NOT NULL REFERENCES projects(project_key) ON DELETE CASCADE,
        group_name  TEXT NOT NULL CHECK (group_name IN ('action','legal')),
        position    INTEGER NOT NULL,
        label       TEXT NOT NULL,
        url         TEXT NOT NULL,
        is_primary  INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (project_key, group_name, position)
    );

    CREATE TABLE IF NOT EXISTS project_shots (
        project_key TEXT NOT NULL REFERENCES projects(project_key) ON DELETE CASCADE,
        position    INTEGER NOT NULL,
        thumb_path  TEXT NOT NULL,
        full_path   TEXT NOT NULL,
        alt         TEXT NOT NULL,
        orientation TEXT NOT NULL CHECK (orientation IN ('landscape','portrait')),
        PRIMARY KEY (project_key, position)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_slug
        ON projects(slug) WHERE slug IS NOT NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_landing_order
        ON projects(landing_order) WHERE on_landing = 1;
    """)

    # The site itself needs a row; it is a build card but has no project page.
    if not conn.execute("SELECT 1 FROM projects WHERE project_key=?", (SITE_KEY,)).fetchone():
        c = CARDS[SITE_KEY]
        conn.execute(
            "INSERT INTO projects (project_key, name, repo_name, local_path, about, stack, github_url) "
            "VALUES (?,?,?,?,?,?,?)",
            (SITE_KEY, c["display_name"], c["repo_name"], c["local_path"],
             c["about"], c["stack"], c["github_url"]),
        )
        print(f"  + projects row {SITE_KEY} (this site)")

    for key, c in CARDS.items():
        conn.execute("""
            UPDATE projects SET
                slug=?, display_name=?, platforms=?, status_kind=?, status_label=?,
                claim=?, problem=?, approach=?, outcome=?,
                on_landing=1, landing_order=?, has_project_page=?, claims_verified_at=?
            WHERE project_key=?""",
            (c["slug"], c["display_name"], c["platforms"], c["status_kind"],
             c["status_label"], c["claim"], c["problem"], c["approach"], c["outcome"],
             c["landing_order"], c.get("has_project_page", 1),
             c["claims_verified_at"], key))

        conn.execute("DELETE FROM project_tags WHERE project_key=?", (key,))
        conn.executemany("INSERT INTO project_tags VALUES (?,?,?)",
                         [(key, i, t) for i, t in enumerate(c["tags"], 1)])

        conn.execute("DELETE FROM project_links WHERE project_key=?", (key,))
        seen = {}
        for group, label, url, primary in c["links"]:
            seen[group] = seen.get(group, 0) + 1
            conn.execute("INSERT INTO project_links VALUES (?,?,?,?,?,?)",
                         (key, group, seen[group], label, url, primary))

        conn.execute("DELETE FROM project_shots WHERE project_key=?", (key,))
        d = c["shot_dir"]
        conn.executemany("INSERT INTO project_shots VALUES (?,?,?,?,?,?)", [
            (key, i, f"/assets/screenshots/{d}/thumb/{n}.jpg",
             f"/assets/screenshots/{d}/full/{n}.jpg", alt, orient)
            for i, (n, alt, orient) in enumerate(c["shots"], 1)])

    for key in OFF_LANDING:
        conn.execute("UPDATE projects SET on_landing=0, landing_order=NULL, "
                     "slug=COALESCE(slug, lower(repo_name)), "
                     "display_name=COALESCE(display_name, name) WHERE project_key=?", (key,))

    # Ordered card feed, and the hero counters derived rather than hand-typed -
    # index.html said "1 Live on Google Play / 2 In store review" for a day after
    # Kalkra was approved, because those numbers were prose.
    conn.executescript("""
    DROP VIEW IF EXISTS v_landing_cards;
    CREATE VIEW v_landing_cards AS
        SELECT landing_order AS build_idx, project_key, display_name, platforms,
               status_kind, status_label, claim, problem, approach, outcome,
               slug, has_project_page, claims_verified_at
        FROM projects WHERE on_landing = 1 ORDER BY landing_order;

    DROP VIEW IF EXISTS v_hero_facts;
    CREATE VIEW v_hero_facts AS
        SELECT
          (SELECT COUNT(*) FROM projects WHERE on_landing=1)
            AS products_owned,
          (SELECT COUNT(*) FROM projects
             WHERE on_landing=1 AND status_kind='live'
               AND (appstore_url IS NOT NULL OR playstore_url IS NOT NULL))
            AS live_in_app_stores,
          (SELECT COUNT(*) FROM projects WHERE on_landing=1 AND status_kind='review')
            AS in_store_review;

    -- Step 3 hook: what has never been checked, or was checked before its last change.
    DROP VIEW IF EXISTS v_unverified_claims;
    CREATE VIEW v_unverified_claims AS
        SELECT project_key, display_name, claims_verified_at, updated_at
        FROM projects
        WHERE on_landing = 1
          AND (claims_verified_at IS NULL
               OR (updated_at IS NOT NULL AND claims_verified_at < substr(updated_at,1,10)));
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "..", "portfolio.db"))
    args = ap.parse_args()
    print(f"migrating {os.path.abspath(args.db)}")
    migrate(args.db)
    print("done")

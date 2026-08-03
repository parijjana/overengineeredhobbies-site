# PROTECTED URLS — do not break these

**These paths are declared inside published app-store listings.** Breaking one
puts a shipped app out of compliance and can stall a review. Verified live
2026-08-03.

Read this before deleting, renaming, moving or un-tracking anything under
`projects/`.

---

## Tier 1 — declared as a field in a store listing

| Path | Declared as | App |
|---|---|---|
| `/projects/pellucid.html` | Marketing URL / Website | Pellucid (Apple) |
| `/projects/pellucid_support.html` | **Support URL** | Pellucid (Apple) |
| `/projects/pellucid_privacy.html` | **Privacy Policy URL** | Pellucid (Apple) |
| `/projects/kalkra.html` | Marketing URL, **Support URL**, Website | Kalkra (Apple) |
| `/projects/kalkra_privacy.html` | **Privacy Policy URL** | Kalkra (Apple) |
| `/projects/kalkra_support.html` | Support URL | Kalkra |

## Tier 2 — linked from a Tier 1 page

| Path | Why it matters |
|---|---|
| `/projects/pellucid_terms.html` | Terms of Service, linked from `pellucid.html` (a Marketing URL Apple holds). Not a store field itself, but breaking it breaks a link on a store-declared page. |

## Off-domain — not in this repo, still store-declared

| URL | Declared as | Served by |
|---|---|---|
| `https://parijjana.github.io/gastrotator_android/privacy_policy.html` | Google Play **Privacy Policy URL** | GitHub Pages, `parijjana/gastrotator_android`, branch `main`, path `/docs` |

Do not disable Pages on that repo, and do not move or rename
`docs/privacy_policy.html` in it.

---

## What is frozen, and what is not

**Frozen:** the path, and the fact that it returns 200.

**Free to change:** styling, layout, theming, and wording — provided the wording
stays *truthful*. Privacy and support pages describe app behaviour; if the app
changes, these must change with it. (On 2026-08-03 the Kalkra project page was
corrected for claiming AES-256, hardware-backed encryption and multiplayer, none
of which the shipped app has.)

**Both forms resolve.** Cloudflare's asset handling 307-redirects
`/projects/x.html` → `/projects/x`, which returns 200. Stores hold the `.html`
form. Do not change `assets` handling in `wrangler.jsonc` — it would alter this
behaviour for every URL above.

---

## The three ways these have actually broken

1. **Never committed.** `.gitignore` line 8 ignores `projects/*.html`. Deploys
   build from the GitHub repo, so an uncommitted page **does not exist in
   production** no matter how correct it looks locally.
   - *Happened:* `pellucid_support.html` existed locally but was never committed
     — the App Store Support URL was 404ing until it was force-added (2026-07-29).
   - *Happened:* `gastrotator_android.html` was never committed; the live homepage
     linked to it and it 404'd (found and fixed 2026-08-03).
   - **If you add a page under `projects/`, `git add -f` it.**

2. **Excluded from serving.** `.assetsignore` controls what Cloudflare uploads.
   Never add `projects/` or any path above to it.
   - *Happened:* `assets/screenshots/*/*.png` was excluded on the assumption the
     PNGs were unused masters; they are the project pages' galleries, and the
     images broke on `kalkra.html` and `pellucid.html` (2026-08-03, reverted
     within minutes).

3. **Regenerated or deleted.** `scripts/generate_pages.py` writes
   `projects/<repo_name>.html` only. The five hand-maintained pages
   (`*_privacy`, `*_support`, `*_terms`) are **never** regenerated — but
   `pellucid.html` and `kalkra.html` **are**, so changes to
   `templates/base_project.html` reach two store-declared pages.

---

## Verify before and after every deploy

```sh
for u in /projects/pellucid.html /projects/pellucid_support.html \
         /projects/pellucid_privacy.html /projects/pellucid_terms.html \
         /projects/kalkra.html /projects/kalkra_privacy.html \
         /projects/kalkra_support.html; do
  printf "%-38s %s\n" "$u" \
    "$(curl -sL -o /dev/null -w '%{http_code}' https://overengineeredhobbies.dev$u)"
done
curl -sL -o /dev/null -w "gastrotator privacy %{http_code}\n" \
  https://parijjana.github.io/gastrotator_android/privacy_policy.html
```

All eight must print `200`. Anything else is a compliance regression — fix or
roll back before doing anything else.

---

## If a URL genuinely must change

1. Update the store listing metadata **first** (App Store Connect / Play Console).
2. Wait for it to be accepted.
3. Only then change the site, keeping the old path as a redirect for a release
   cycle.

**Never do this while an app is in review.** As of 2026-08-03 both Pellucid and
Kalkra are in store review.

A copy of this file lives in the private `project_docs` repo.

"""
YZU Portal File Downloader
---------------------------
Auto-logs in and downloads all course files.
Detects updated files (same name, new AttachmentID) and replaces them.
No prompts — just runs.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

CONFIG_FILE   = Path(__file__).parent / "config.json"
TRACKING_FILE = Path(__file__).parent / "downloaded_files.json"

# ── Your courses ────────────────────────────────────
COURSES = {
    "32440": "Introduction to Algorithms",
    "31221": "Introduction to Operating System",
    "26811": "Information Privacy",
    "28726": "Assembly Language and Computer Organization",
    "26807": "Probability and Statistics",
    "32213": "Machine Learning",
}

# ── File types to download ──────────────────────────
FILE_EXTENSIONS = {
    # Documents
    ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md",
    # Presentations
    ".ppt", ".pptx", ".odp", ".key",
    # Spreadsheets
    ".xls", ".xlsx", ".ods", ".csv",
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    # Code & notebooks
    ".py", ".ipynb", ".java", ".c", ".cpp", ".h",
    ".js", ".ts", ".html", ".css", ".sql", ".sh", ".bat", ".r",
    # Data
    ".json", ".xml", ".yaml", ".yml",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
    # Video
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
    # Audio
    ".mp3", ".wav", ".aac", ".flac", ".ogg",
}

# ── Concurrency ─────────────────────────────────────
MAX_CONCURRENT_DOWNLOADS = 4
MAX_CONCURRENT_COURSES   = 3


# ── Tracking ────────────────────────────────────────
def load_tracking() -> dict:
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_tracking(data: dict):
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def tracking_key(course_name: str, filename: str) -> str:
    return f"{course_name}/{filename}"

def is_updated(tracking: dict, course_name: str, filename: str, attach_id: str) -> bool:
    key = tracking_key(course_name, filename)
    return key in tracking and tracking[key] != attach_id

def mark_downloaded(tracking: dict, course_name: str, filename: str, attach_id: str):
    tracking[tracking_key(course_name, filename)] = attach_id


# ── Config ──────────────────────────────────────────
def load_config():
    if not CONFIG_FILE.exists():
        print("  config.json not found.")
        input("Press Enter to exit...")
        exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def sanitize(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def make_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── GitHub push ─────────────────────────────────────
def run_git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return False, "Git not found."

def push_to_github(base_folder, cfg):
    repo_url = cfg.get("github_repo_url", "").strip()
    branch   = cfg.get("github_branch", "main").strip() or "main"
    if not repo_url:
        return
    print("\n  Pushing to GitHub...")
    run_git(["remote", "set-url", "origin", repo_url], base_folder)
    run_git(["add", "-A"], base_folder)
    _, status = run_git(["status", "--porcelain"], base_folder)
    if not status.strip():
        print("  GitHub already up to date.")
        return
    run_git(["commit", "-m", "Add YZU course files"], base_folder)
    ok, out = run_git(["push", "-u", "origin", branch], base_folder)
    print("  Pushed!" if ok else f"  Push failed: {out}")


# ── Auto-login ──────────────────────────────────────
async def auto_login(page, username, password):
    print("\n  Logging in...")
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(1)
    try:
        await page.locator("#Txt_UserID").fill(username)
        await page.locator("#Txt_Password").fill(password)
        await page.locator("#ibnSubmit").click()
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(1.5)
        print("  [OK] Logged in!")
        try:
            await page.evaluate("__doPostBack('MainBar$ibnChangeVersion', '')")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1)
            print("  [OK] Switched to English!")
        except Exception:
            pass
    except Exception as e:
        print(f"  [!] Login failed: {e}")
        print("  Please log in manually then press Enter.")
        input()


# ── Auto-discover courses from sidebar ──────────────
async def auto_discover_courses(page, base_url) -> dict | None:
    """Scrape PageIDs and course names from the portal left sidebar."""
    print("\n  Auto-discovering courses from portal sidebar...")
    try:
        current_url = page.url
        home_url = f"{base_url}/PortalSocialVB/FMain/DefaultPage.aspx"
        if home_url.lower() not in current_url.lower():
            await page.goto(
                f"{base_url}/PortalSocialVB/FMain/DefaultPage.aspx?Menu=Default&LogExcute=Y",
                wait_until="networkidle",
                timeout=30000
            )

        # Wait for the sidebar container that holds course links
        try:
            await page.wait_for_selector(
                "#MainLeftMenu_divMyPage, td[onclick*='GoToPage']",
                timeout=15000
            )
        except Exception:
            pass  # proceed anyway and try to scrape whatever is there

        # Run in-browser JS — more reliable than Playwright element queries
        # for dynamically rendered ASP.NET content
        raw = await page.evaluate("""
            () => Array.from(document.querySelectorAll('[onclick*="GoToPage"]'))
                .map(el => ({
                    id:   (el.getAttribute('onclick').match(/GoToPage\\('(\\d+)'/) || [])[1],
                    name: el.innerText.trim()
                }))
                .filter(c => c.id && c.name)
        """)

        if not raw:
            # Last resort: regex over raw HTML
            html = await page.content()
            raw = [
                {"id": m.group(1), "name": ""}
                for m in re.finditer(r"GoToPage\('(\d+)'", html)
            ]

        courses = {c["id"]: c["name"] for c in raw if c.get("id")}

        if courses:
            print(f"  [OK] Found {len(courses)} course(s):")
            for name in courses.values():
                print(f"    • {name or '(unnamed)'}")
            return courses

        print("  [!] No courses found in sidebar — falling back to config.")
        return None
    except Exception as e:
        print(f"  [!] Auto-discovery failed: {e} — falling back to config.")
        return None


# ── Cleanup junk files ──────────────────────────────
def cleanup_junk_files(base_folder: Path):
    """Remove UUID temp files and no-extension files left by failed downloads."""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    removed = 0
    for f in base_folder.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix == "" and uuid_pattern.match(f.stem):
            f.unlink()
            removed += 1
        elif f.suffix == "" and len(f.stem) > 20:
            f.unlink()
            removed += 1
    if removed:
        print(f"  Cleaned up {removed} junk file(s)")
    else:
        print(f"  No junk files found")


# ── Smart DOM wait ──────────────────────────────────
async def wait_for_html_condition(page, condition_fn, interval=0.3, timeout=15):
    elapsed = 0
    while elapsed < timeout:
        html = await page.content()
        if condition_fn(html):
            return html
        await asyncio.sleep(interval)
        elapsed += interval
    return await page.content()


# ── Parse all DownloadFile links from raw HTML ──────
def parse_download_links(html: str) -> list[tuple[str, str]]:
    results = []
    seen = set()
    for href in re.findall(r'href=["\']([^"\']*DownloadFile[^"\']*)["\']', html):
        aid = re.search(r'AttachmentID=(\d+)', href)
        afn = re.search(r'AttachmentFileName=([^&"\']+)', href)
        if aid and afn:
            key = (aid.group(1), afn.group(1))
            if key not in seen:
                seen.add(key)
                results.append(key)
    return results


# ── Collect attachments from one post ──────────────
async def collect_post_attachments(page, post_id: str) -> list[tuple[str, str]]:
    try:
        await page.evaluate(f"ShowPostGridUnique({post_id}, 0)")
    except Exception:
        return []

    await wait_for_html_condition(
        page,
        lambda h: f'divPost{post_id}' in h,
        interval=0.2,
        timeout=8
    )

    await asyncio.sleep(0.5)

    results = []
    seen    = set()

    try:
        post_div = await page.query_selector(f"#divPost{post_id}")
        if post_div:
            for link in await post_div.query_selector_all("a[href*='DownloadFile']"):
                href = await link.get_attribute("href") or ""
                aid  = re.search(r'AttachmentID=(\d+)', href)
                afn  = re.search(r'AttachmentFileName=([^&"]+)', href)
                if aid and afn:
                    key = (aid.group(1), afn.group(1))
                    if key not in seen:
                        seen.add(key)
                        results.append(key)
    except Exception:
        pass

    try:
        post_html = await page.evaluate(
            f"document.getElementById('divPost{post_id}')?.innerHTML || ''"
        )
        for key in parse_download_links(post_html):
            if key not in seen:
                seen.add(key)
                results.append(key)
    except Exception:
        pass

    return results


# ── Scan one course ─────────────────────────────────
async def scan_course(page, context, page_id, course_name, base_folder, base_url, dl_sem, tracking):
    print(f"\n  [{course_name}]")
    course_path = make_folder(base_folder / sanitize(course_name))

    try:
        await page.evaluate(f"GoToPage('{page_id}', 'tdPage0')")
        await asyncio.sleep(0.5)
    except Exception:
        pass

    await page.goto(
        f"{base_url}/PortalSocialVB/FPage/FirstToPage.aspx?PageID={page_id}",
        wait_until="networkidle",
        timeout=30000
    )

    html = await wait_for_html_condition(
        page, lambda h: 'ShowPostGridUnique' in h, interval=0.3, timeout=30
    )
    if 'ShowPostGridUnique' not in html:
        print(f"    No posts found — skipping")
        return 0

    all_post_ids = []
    seen_post_ids = set()
    page_index = 1

    while True:
        html = await page.content()
        new_ids = [pid for pid in dict.fromkeys(re.findall(r'ShowPostGridUnique\((\d+)', html))
                   if pid not in seen_post_ids]
        if not new_ids:
            break
        all_post_ids.extend(new_ids)
        seen_post_ids.update(new_ids)
        if f'GoPageIndex({page_index + 1})' not in html:
            break
        page_index += 1
        await page.evaluate(f"GoPageIndex({page_index})")
        await asyncio.sleep(0.3)
        for _ in range(20):
            await asyncio.sleep(0.3)
            if set(re.findall(r'ShowPostGridUnique\((\d+)', await page.content())) - seen_post_ids:
                break

    print(f"    {len(all_post_ids)} posts found — scanning for attachments...")

    all_attachments = {}
    for post_id in all_post_ids:
        for aid, afn in await collect_post_attachments(page, post_id):
            all_attachments[aid] = afn

    try:
        full_html = await page.content()
        sweep_found = 0
        for aid, afn in parse_download_links(full_html):
            if aid not in all_attachments:
                all_attachments[aid] = afn
                sweep_found += 1
        if sweep_found:
            print(f"    [+] Full page sweep caught {sweep_found} extra attachment(s)")
    except Exception:
        pass

    # Deduplicate: same filename can appear with multiple AttachmentIDs
    # (e.g. linked from two posts, or re-uploaded). Keep highest ID only —
    # otherwise the script flip-flops between IDs every run, re-downloading forever.
    deduped: dict[str, tuple[str, str]] = {}
    for aid, afn in all_attachments.items():
        try:
            fname_key = sanitize(urllib.parse.unquote_plus(afn))
        except Exception:
            fname_key = sanitize(afn)
        existing_aid = deduped.get(fname_key, ("0",))[0]
        if int(aid) > int(existing_aid):
            deduped[fname_key] = (aid, afn)
    all_attachments = {aid: afn for aid, afn in deduped.values()}

    print(f"    {len(all_attachments)} total attachment(s) found")

    to_download = []
    for attach_id, raw_filename in all_attachments.items():
        try:
            fname = urllib.parse.unquote_plus(raw_filename)
        except Exception:
            fname = raw_filename

        if Path(fname).suffix.lower() not in FILE_EXTENSIONS:
            continue

        clean_fname = sanitize(fname)
        dest        = course_path / clean_fname

        if not dest.exists() and not (course_path / sanitize(raw_filename)).exists():
            to_download.append((attach_id, fname, clean_fname, dest, False))
        elif is_updated(tracking, sanitize(course_name), clean_fname, attach_id):
            print(f"    [UPDATE DETECTED] {clean_fname}")
            to_download.append((attach_id, fname, clean_fname, dest, True))
        else:
            print(f"    [SKIP] {clean_fname}")

    if not to_download:
        print(f"    Nothing new.")
        return 0

    new_count    = sum(1 for *_, u in to_download if not u)
    update_count = sum(1 for *_, u in to_download if u)
    if new_count:    print(f"    {new_count} new file(s)")
    if update_count: print(f"    {update_count} updated file(s)")

    lock = asyncio.Lock()

    async def do_download(attach_id, fname, clean_fname, dest, is_update):
        ok = await download_attachment(context, page, attach_id, fname, dest, dl_sem)
        label = "[UPDATE]" if is_update else "[DOWN]  "
        print(f"    {label} {'[OK]' if ok else '[FAIL]'} {clean_fname}")
        if ok:
            async with lock:
                mark_downloaded(tracking, sanitize(course_name), clean_fname, attach_id)
        return ok

    results = await asyncio.gather(*[
        do_download(aid, fname, cfname, dest, is_upd)
        for aid, fname, cfname, dest, is_upd in to_download
    ])

    success = sum(1 for r in results if r)
    print(f"    Done — {success}/{len(to_download)} downloaded")
    return success


# ── Download one file ───────────────────────────────
async def download_attachment(context, page, attach_id, filename, dest_path, sem):
    async with sem:
        try:
            encoded      = urllib.parse.quote(filename)
            download_url = (
                f"https://portalx.yzu.edu.tw/PortalSocialVB/DownloadFile.aspx"
                f"?Source=Course&CourseType=2"
                f"&AttachmentID={attach_id}"
                f"&AttachmentFileName={encoded}"
            )
            new_page = await context.new_page()
            try:
                async with new_page.expect_download(timeout=30_000) as dl_info:
                    await new_page.goto(download_url, wait_until="commit")
                dl = await dl_info.value
                await dl.save_as(str(dest_path))
                await new_page.close()
                return True
            except Exception:
                await new_page.close()
                selector = f"a[href*='AttachmentID={attach_id}']"
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    async with page.expect_download(timeout=30_000) as dl_info:
                        await page.locator(selector).first.click()
                    dl = await dl_info.value
                    await dl.save_as(str(dest_path))
                    return True
                except Exception as e2:
                    print(f"      Error: {str(e2)[:80]}")
                    return False
        except Exception as e:
            print(f"      Error: {str(e)[:80]}")
            return False


# ── Main ────────────────────────────────────────────
async def run():
    cfg = load_config()

    # Cross-platform download folder:
    # Use config value if set, otherwise fall back to ~/Downloads/School Files
    raw_folder  = cfg.get("download_folder", "").strip()
    base_folder = Path(raw_folder) if raw_folder else Path.home() / "Downloads" / "School Files"

    base_url = "https://portalx.yzu.edu.tw"
    username = os.getenv("YZU_USERNAME", "")
    password = os.getenv("YZU_PASSWORD", "")

    make_folder(base_folder)
    cleanup_junk_files(base_folder)

    tracking = load_tracking()

    print("\n" + "="*55)
    print("  YZU Portal File Downloader")
    print("="*55)
    print(f"  Saving to  : {base_folder}")
    print(f"  Account    : {username or 'Not set in .env'}")
    print(f"  Courses    : {len(COURSES)} (hardcoded fallback — will auto-discover after login)")
    for name in COURSES.values():
        print(f"    • {name}")
    print("="*55)

    async with async_playwright() as p:
        launch_args = ["--start-maximized"] if sys.platform != "darwin" else []
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(base_folder),
            args=launch_args
        )
        context = await browser.new_context(accept_downloads=True, viewport=None)

        page = await context.new_page()
        await page.goto(f"{base_url}/PortalSocialVB/Login.aspx", wait_until="domcontentloaded")
        if username and password:
            await auto_login(page, username, password)
        else:
            print("  No credentials in .env — log in manually then press Enter.")
            input()

        discovered = await auto_discover_courses(page, base_url)
        courses = discovered if discovered else COURSES

        dl_sem     = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        course_sem = asyncio.Semaphore(MAX_CONCURRENT_COURSES)

        async def scan_with_sem(page_id, course_name):
            async with course_sem:
                p = await context.new_page()
                try:
                    return await scan_course(
                        p, context, page_id, course_name,
                        base_folder, base_url, dl_sem, tracking
                    )
                except Exception as e:
                    print(f"  [ERROR] {course_name}: {e}")
                    return 0
                finally:
                    await p.close()

        await page.close()
        results = await asyncio.gather(*[
            scan_with_sem(pid, name)
            for pid, name in courses.items()
        ])

        save_tracking(tracking)

        total = sum(results)
        print("\n" + "="*55)
        print(f"  Done!  {total} new/updated file(s) downloaded")
        print(f"  Saved to: {base_folder}")
        print("="*55)

        if cfg.get("github_enabled") and total > 0:
            await asyncio.get_running_loop().run_in_executor(
                None, push_to_github, Path(__file__).parent, cfg
            )

        cleanup_junk_files(base_folder)

        input("\nPress Enter to close...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
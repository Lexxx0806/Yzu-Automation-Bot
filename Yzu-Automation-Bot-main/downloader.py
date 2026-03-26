"""
YZU Portal File Downloader
---------------------------
Auto-logs in, finds all 教材 (teaching material) posts across all courses,
and downloads their attached files into organized folders.
"""

import asyncio
import json
import os
import re
import subprocess
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

CONFIG_FILE = Path(__file__).parent / "config.json"

# ── Your YZU courses (PageID -> name) ──────────────
YZU_COURSES = {
    "32440": "Introduction to Algorithms",
    "31221": "Introduction to Operating System",
    "26811": "Information Privacy",
    "28726": "Assembly Language and Computer Organization",
    "26807": "Probability and Statistics",
    "32213": "Machine Learning",
}

FILE_EXTENSIONS = [".pdf", ".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls", ".zip"]

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
    ok2, status = run_git(["status", "--porcelain"], base_folder)
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
    await asyncio.sleep(1.5)
    try:
        await page.locator("#Txt_UserID").fill(username)
        await page.locator("#Txt_Password").fill(password)
        await page.locator("#ibnSubmit").click()
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        print("  [OK] Logged in!")

        # Switch portal to English
        try:
            await page.evaluate("__doPostBack('MainBar$ibnChangeVersion', '')")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1.5)
            print("  [OK] Portal switched to English!")
        except Exception:
            print("  [!] Could not switch to English — continuing anyway")
    except Exception as e:
        print(f"  [!] Login failed: {e}")
        print("  Please log in manually in the browser.")
        input("  Press Enter once logged in...")


# ── Download a single file by AttachmentID ──────────
async def download_attachment(context, page, attach_id, filename, dest_path):
    try:
        # Build the correct download URL
        encoded = urllib.parse.quote(filename)
        download_url = (
            f"https://portalx.yzu.edu.tw/PortalSocialVB/DownloadFile.aspx"
            f"?Source=Course&CourseType=2"
            f"&AttachmentID={attach_id}"
            f"&AttachmentFileName={encoded}"
        )

        # Open in a new page within the SAME context (shares session cookies)
        # and intercept the download before the browser handles it
        new_page = await context.new_page()
        try:
            async with new_page.expect_download(timeout=30_000) as dl_info:
                await new_page.goto(download_url, wait_until="commit")
            dl = await dl_info.value
            await dl.save_as(str(dest_path))
            await new_page.close()
            return True
        except Exception:
            # Fallback: try clicking the actual link on the original page
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


# ── Scan a course page for all posts and their files ─
async def scan_course(page, context, page_id, course_name, base_folder, base_url):
    print(f"\n  [{course_name}] Navigating to course wall...")
    course_path = make_folder(base_folder / sanitize(course_name))

    # Navigate to dashboard first, then click the course from the sidebar
    # This properly triggers the portal's AJAX post loader
    current_url = page.url
    if "DefaultPage" not in current_url and "PostWall" not in current_url:
        await page.goto(
            f"{base_url}/PortalSocialVB/FMain/DefaultPage.aspx",
            wait_until="domcontentloaded"
        )
        await asyncio.sleep(2)

    # Click the course page link from the sidebar (same as clicking manually)
    try:
        await page.evaluate(f"GoToPage('{page_id}', 'tdPage0')")
        await asyncio.sleep(1)
    except Exception:
        pass

    # Navigate directly as fallback
    await page.goto(
        f"{base_url}/PortalSocialVB/FPage/FirstToPage.aspx?PageID={page_id}",
        wait_until="networkidle",
        timeout=30000
    )
    await asyncio.sleep(3)

    # Wait until posts actually appear in the DOM (up to 30 seconds)
    print(f"  Waiting for posts to load...")
    for _ in range(60):
        await asyncio.sleep(0.5)
        html = await page.content()
        if 'ShowPostGridUnique' in html:
            print(f"  Posts loaded!")
            break
    else:
        print(f"  [!] Posts never loaded for {course_name} — skipping")
        return 0

    # ── Collect ALL post IDs across ALL pages ──────────
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
        print(f"    Page {page_index}: {len(new_ids)} posts (total: {len(all_post_ids)})")

        # Check if there's a next page
        has_next = f'GoPageIndex({page_index + 1})' in html
        if not has_next:
            break

        # Go to next page and wait for new posts to load
        page_index += 1
        await page.evaluate(f"GoPageIndex({page_index})")
        await asyncio.sleep(0.5)
        for _ in range(20):
            await asyncio.sleep(0.5)
            new_html = await page.content()
            new_page_ids = set(re.findall(r'ShowPostGridUnique\((\d+)', new_html))
            if new_page_ids - seen_post_ids:
                break

    print(f"  Total posts to scan: {len(all_post_ids)}")

    # ── Scan each post for files ───────────────────────
    success = 0
    for post_id in all_post_ids:
        try:
            await page.evaluate(f"ShowPostGridUnique({post_id}, 0)")
            await asyncio.sleep(2)
        except Exception:
            continue

        # Wait for download links to appear
        try:
            await page.wait_for_selector(
                f"#divPost{post_id} a[href*='DownloadFile']", timeout=3000
            )
        except Exception:
            pass  # Post might not have files, that's fine

        # Scan for download links directly from DOM
        attach_pattern = []
        try:
            post_div = await page.query_selector(f"#divPost{post_id}")
            if post_div:
                dl_links = await post_div.query_selector_all("a[href*='DownloadFile']")
                for dl_link in dl_links:
                    href = await dl_link.get_attribute("href") or ""
                    aid  = re.search(r'AttachmentID=(\d+)', href)
                    afn  = re.search(r'AttachmentFileName=([^&"]+)', href)
                    if aid and afn:
                        attach_pattern.append((aid.group(1), afn.group(1)))
        except Exception:
            pass

        if not attach_pattern:
            continue

        for attach_id, raw_filename in attach_pattern:
            # Decode filename — handle both + and %20 style encoding
            try:
                fname = urllib.parse.unquote_plus(raw_filename)
            except Exception:
                fname = raw_filename

            ext = Path(fname).suffix.lower()
            if ext not in FILE_EXTENSIONS:
                continue

            clean_fname = sanitize(fname)
            dest = course_path / clean_fname

            # Skip if already downloaded (check both encoded and decoded names)
            if dest.exists():
                print(f"    [SKIP] {clean_fname}")
                continue

            # Also check with original encoded name just in case
            alt_dest = course_path / sanitize(raw_filename)
            if alt_dest.exists():
                print(f"    [SKIP] {clean_fname} (already exists)")
                continue

            print(f"    [DOWN] {clean_fname} (AttachmentID={attach_id})")
            ok = await download_attachment(context, page, attach_id, fname, dest)
            if ok:
                print(f"    [OK]   {clean_fname}")
                success += 1
            else:
                print(f"    [FAIL] {clean_fname}")

        await asyncio.sleep(0.3)

    print(f"  [{course_name}] Done — {success} new file(s) downloaded")
    return success


# ── Main ────────────────────────────────────────────
async def run():
    cfg         = load_config()
    base_folder = Path(cfg.get("download_folder", str(Path.home() / "Downloads" / "SchoolFiles")))
    base_url    = "https://portalx.yzu.edu.tw"
    username    = os.getenv("YZU_USERNAME", "")
    password    = os.getenv("YZU_PASSWORD", "")

    make_folder(base_folder)

    print("\n" + "="*55)
    print("  YZU Portal File Downloader")
    print("="*55)
    print(f"  Save to : {base_folder}")
    print(f"  Account : {username or 'Not set in .env'}")
    print(f"  Courses : {len(YZU_COURSES)}")
    print("="*55)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(base_folder),
            args=["--start-maximized"]
        )
        context = await browser.new_context(accept_downloads=True, viewport=None)
        page    = await context.new_page()

        # Login
        await page.goto(f"{base_url}/PortalSocialVB/Login.aspx", wait_until="domcontentloaded")
        if username and password:
            await auto_login(page, username, password)
        else:
            print("  No credentials — log in manually then press Enter.")
            input()

        # Scan all courses
        total = 0
        for page_id, course_name in YZU_COURSES.items():
            try:
                total += await scan_course(page, context, page_id, course_name, base_folder, base_url)
            except Exception as e:
                print(f"  [ERROR] {course_name}: {e}")

        print("\n" + "="*55)
        print(f"  All done! {total} total file(s) downloaded")
        print(f"  Saved to: {base_folder}")
        print("="*55)

        # Push to GitHub
        if cfg.get("github_enabled") and total > 0:
            project_folder = Path(__file__).parent
            await asyncio.get_event_loop().run_in_executor(None, push_to_github, project_folder, cfg)

        input("\nPress Enter to close...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
"""End-to-end Playwright smoke verification against the built Vite bundle."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "apps" / "web"


def _wait_for_server(url: str, timeout_s: float = 20.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"Preview server did not start at {url}")


def main() -> int:
    proc = subprocess.Popen(
        ["npm.cmd", "run", "preview", "--", "--port", "4173", "--host", "127.0.0.1"],
        cwd=str(WEB_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        url = "http://127.0.0.1:4173/"
        _wait_for_server(url)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, width, height in [
                ("desktop", 1366, 768),
                ("ipad", 1024, 768),
                ("mobile", 390, 844),
            ]:
                page = browser.new_page(viewport={"width": width, "height": height})
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.on(
                    "console",
                    lambda msg: errors.append(msg.text) if msg.type == "error" else None,
                )

                page.goto(url, wait_until="networkidle")
                page.wait_for_selector(".hint-strip >> text=Normal Baseline (Center Model)")
                page.wait_for_selector("text=Diagnostic Decision")
                body_text = page.inner_text("body")
                assert "LIVE" not in body_text.split(), f"Forbidden LIVE text on {name}"
                assert "Location not evaluated" in body_text
                assert "Integrity Failure" not in body_text

                # Verify horizontal overflow <= 2px
                overflow = page.evaluate(
                    "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                )
                assert overflow <= 2, f"Horizontal overflow {overflow}px on {name}"

                if name == "desktop":
                    # Switch scenario to Leak G4 and jump to onset
                    page.select_option("#scenario-select", "SCEN_CENTER_TRANSIENT_LEAKG4")
                    page.wait_for_selector(".hint-strip >> text=Transient Leak (G4)")
                    page.wait_for_selector("button:has-text('Onset (400.0s)')")
                    page.click("button:has-text('Onset (400.0s)')")
                    assert "t = 400.0s" in page.inner_text("body")

                    # Check Benchmarks view
                    page.click("button.nav-tab:has-text('Benchmarks')")
                    page.wait_for_selector("text=NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL")
                    assert "27,993" in page.inner_text("body")

                    # Check Methods & Limits view
                    page.click("button.nav-tab:has-text('Methods & Limits')")
                    page.wait_for_selector("text=Explicitly Prohibited Claims")

                assert not errors, f"Console/page errors on {name}: {errors}"
                page.close()
                print(f"E2E PASS [{name} {width}x{height}]")
            browser.close()
        return 0
    finally:
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(main())

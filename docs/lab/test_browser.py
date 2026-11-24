"""Optional Chromium and Firefox smoke tests with Playwright."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent


def run(browser_type, executable, url, screenshots):
    browser = browser_type.launch(executable_path=executable)
    try:
        page = browser.new_page(viewport={"width": 1440, "height": 1050}, accept_downloads=True)
        errors = []
        unexpected_requests = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: unexpected_requests.append(request.url)
            if request.url.startswith(("http:", "https:"))
            and not (request.is_navigation_request() and request.url == url)
            else None,
        )
        response = page.goto(url)
        if url.startswith(("http:", "https:")):
            assert response and response.ok, response
        assert page.title() == "NEXUS | Evaluation Lab"
        status = page.get_by_role("status")
        metrics = page.locator("#metrics")
        preset = page.get_by_label("Example scenario")
        threshold = page.get_by_label("Minimum pass rate (%)")
        cases = page.get_by_label("Test cases JSON")
        predictions = page.get_by_label("Agent predictions JSON")
        evaluate = page.get_by_role("button", name="Run evaluation")
        export = page.get_by_role("button", name="Export report JSON")
        diagnostics = page.get_by_role("link", name="See case diagnostics")

        assert "Rejected" in status.inner_text() and "CLOSED" in metrics.inner_text()
        assert status.bounding_box()["y"] < cases.bounding_box()["y"]
        assert export.bounding_box()["y"] < cases.bounding_box()["y"]
        if screenshots:
            page.screenshot(path=screenshots / "nexus-lab-desktop.png")

        evaluate.focus()
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.id") == "try-zero"
        page.keyboard.press("Enter")
        assert threshold.input_value() == "0"
        assert "Rejected" in status.inner_text() and "CLOSED" in metrics.inner_text()
        threshold.fill("50")
        assert export.is_disabled() and not diagnostics.is_visible()
        evaluate.click()
        assert "Rejected" in status.inner_text() and diagnostics.is_visible()

        preset.select_option("accepted")
        assert "Accepted" in status.inner_text() and "3 / 3" in metrics.inner_text()
        with page.expect_download() as download:
            export.click()
        saved = json.loads(Path(download.value.path()).read_text(encoding="utf-8"))
        assert saved["accepted"] is True and saved["passed"] == 3

        preset.select_option("noncritical")
        assert "Rejected" in status.inner_text()
        threshold.fill("60")
        evaluate.click()
        assert "Accepted" in status.inner_text()

        preset.select_option("unexpected")
        threshold.fill("0")
        evaluate.click()
        assert "Rejected" in status.inner_text()
        assert "unknown-01" in page.locator("#extra").inner_text()

        preset.select_option("invalid")
        assert "Invalid input" in status.inner_text()
        assert "duplicate JSON key" in status.inner_text()
        assert export.is_disabled() and not diagnostics.is_visible()
        assert metrics.inner_text() == "" and not page.locator("#raw").is_visible()

        preset.select_option("accepted")
        predictions.fill("{")
        assert export.is_disabled() and not diagnostics.is_visible()
        evaluate.click()
        assert "Invalid input" in status.inner_text() and export.is_disabled()
        page.get_by_role("button", name="Reset example").click()
        assert "Accepted" in status.inner_text()
        threshold.fill("")
        evaluate.click()
        assert "Invalid input" in status.inner_text() and export.is_disabled()

        preset.select_option("critical")
        for width in (320, 390):
            page.set_viewport_size({"width": width, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        page.evaluate("scrollTo(0, 0)")
        verdict = status.locator("strong").bounding_box()
        assert verdict["y"] + verdict["height"] <= 844
        if screenshots:
            page.screenshot(path=screenshots / "nexus-lab-mobile.png")
        diagnostics.focus()
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.id") == "cases"
        assert cases.evaluate(
            "(element) => element.matches(':focus-visible') && "
            "getComputedStyle(element).outlineOffset === '-3px'"
        )
        if screenshots:
            page.screenshot(path=screenshots / "nexus-lab-mobile-editor.png")
        assert not errors, errors
        assert not unexpected_requests, unexpected_requests
        print(
            f"{browser_type.name} {browser.version}: five presets, 0% gate, export, "
            "stale and invalid input, keyboard focus, 320/390px layout; "
            "zero JavaScript exceptions and zero unexpected HTTP(S) requests."
        )
    finally:
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", choices=("chromium", "firefox"), default="chromium")
    parser.add_argument("--executable", help="Optional custom browser executable")
    parser.add_argument("--url", default=(LAB / "index.html").as_uri())
    parser.add_argument("--screenshots", type=Path, help="Optional screenshot directory")
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(exist_ok=True, parents=True)
    with sync_playwright() as playwright:
        run(getattr(playwright, args.browser), args.executable, args.url, args.screenshots)


if __name__ == "__main__":
    main()

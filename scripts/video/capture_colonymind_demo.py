"""Capture the deployed ColonyMind UI as a rules-compliant 170-second demo.

The script does not mock application state. It drives the public deployment,
records the real browser surface, and adds only explanatory title/caption
overlays. Learning and audit results remain application-owned.
"""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "prompts" / "colonymind-build-week-video.prompt.json"
OUTPUT_DIR = ROOT / "output" / "video"
TEMP_DIR = ROOT / "tmp" / "video-capture"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
LIVE_URL = "https://openaidev.automationfreelancer.com"


def seconds(value: str) -> int:
    minutes, secs = value.split(":")
    return int(minutes) * 60 + int(secs)


def install_overlay(page: Page) -> None:
    page.evaluate(
        """
        () => {
          const style = document.createElement('style');
          style.dataset.videoProduction = 'true';
          style.textContent = `
            html { scroll-behavior: smooth !important; }
            body { cursor: none !important; }
            #cm-video-overlay {
              position: fixed; inset: 0; z-index: 2147483647;
              pointer-events: none; font-family: Inter, Manrope, Arial, sans-serif;
              color: #f7fcff;
            }
            #cm-video-kicker {
              position: absolute; top: 42px; left: 54px;
              max-width: 1450px; padding: 13px 20px 12px;
              background: rgba(4, 17, 30, .82);
              border: 1px solid rgba(57, 212, 255, .55);
              border-left: 5px solid #39d4ff; border-radius: 10px;
              box-shadow: 0 10px 45px rgba(0,0,0,.28);
              font-size: 30px; font-weight: 800; letter-spacing: .045em;
              text-transform: uppercase;
            }
            #cm-video-caption {
              position: absolute; left: 50%; bottom: 38px;
              transform: translateX(-50%); width: min(1560px, 88vw);
              box-sizing: border-box; padding: 15px 24px 16px;
              background: rgba(3, 14, 26, .88);
              border: 1px solid rgba(136, 119, 255, .5);
              border-radius: 12px; text-align: center;
              font-size: 27px; line-height: 1.28; font-weight: 650;
              text-shadow: 0 2px 8px #000;
            }
            #cm-video-corner {
              position: absolute; top: 45px; right: 54px;
              color: #55e6a5; font-family: Consolas, monospace;
              font-size: 16px; letter-spacing: .12em;
            }
            #cm-video-fullcard {
              display: none; position: absolute; inset: 0;
              align-items: center; justify-content: center;
              padding: 100px; box-sizing: border-box;
              background: radial-gradient(circle at 50% 45%, rgba(17,57,91,.95), rgba(3,12,23,.985) 65%);
            }
            #cm-video-fullcard > div { max-width: 1450px; text-align: center; }
            #cm-video-fullcard h2 { margin: 0 0 22px; color: #39d4ff; font-size: 70px; line-height: 1.03; }
            #cm-video-fullcard p { margin: 10px auto; max-width: 1250px; color: #d9f6ff; font-size: 31px; line-height: 1.35; }
            #cm-video-fullcard .accent { color: #55e6a5; font-family: Consolas, monospace; font-size: 22px; }
          `;
          document.head.appendChild(style);
          const overlay = document.createElement('div');
          overlay.id = 'cm-video-overlay';
          overlay.innerHTML = `
            <div id="cm-video-kicker"></div>
            <div id="cm-video-corner">COLONYMIND / LIVE ENGINE</div>
            <div id="cm-video-caption"></div>
            <div id="cm-video-fullcard"><div><h2></h2><p></p><p class="accent"></p></div></div>`;
          document.body.appendChild(overlay);
        }
        """
    )


def set_scene(page: Page, title: str, caption: str) -> None:
    page.evaluate(
        """([title, caption]) => {
          document.querySelector('#cm-video-kicker').textContent = title;
          document.querySelector('#cm-video-caption').textContent = caption;
          document.querySelector('#cm-video-kicker').style.display = 'block';
          document.querySelector('#cm-video-caption').style.display = 'block';
          document.querySelector('#cm-video-corner').style.display = 'block';
          document.querySelector('#cm-video-fullcard').style.display = 'none';
        }""",
        [title, caption],
    )


def set_fullcard(page: Page, title: str, body: str, accent: str) -> None:
    page.evaluate(
        """([title, body, accent]) => {
          const card = document.querySelector('#cm-video-fullcard');
          card.querySelector('h2').textContent = title;
          card.querySelector('p:not(.accent)').textContent = body;
          card.querySelector('.accent').textContent = accent;
          card.style.display = 'flex';
          document.querySelector('#cm-video-kicker').style.display = 'none';
          document.querySelector('#cm-video-caption').style.display = 'none';
          document.querySelector('#cm-video-corner').style.display = 'none';
        }""",
        [title, body, accent],
    )


def scroll_to(page: Page, text: str) -> None:
    locator = page.get_by_text(text, exact=False).first
    locator.scroll_into_view_if_needed(timeout=10_000)
    page.wait_for_timeout(700)


def wait_until(start: float, target_seconds: int) -> None:
    remaining = start + target_seconds - time.monotonic()
    if remaining > 0:
        time.sleep(remaining)


def draw_circle(page: Page) -> None:
    canvas = page.locator('canvas[aria-label="Draw a circle, triangle, or square"]')
    box = canvas.bounding_box()
    if not box:
        return
    import math

    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    radius = min(box["width"], box["height"]) * 0.31
    for index in range(41):
        angle = (index / 40) * math.tau
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        if index == 0:
            page.mouse.move(x, y)
            page.mouse.down()
        else:
            page.mouse.move(x, y, steps=2)
    page.mouse.up()


def main() -> None:
    spec = json.loads(PROMPT.read_text(encoding="utf-8"))
    shots = spec["shot_plan"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE))
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=str(TEMP_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.goto(LIVE_URL, wait_until="networkidle", timeout=120_000)
        page.evaluate("window.scrollTo(0, 0)")
        install_overlay(page)
        video = page.video
        start = time.monotonic()

        set_scene(page, shots[0]["overlay"], shots[0]["voiceover"])
        wait_until(start, seconds(shots[0]["timecode"].split("-")[1]))

        set_scene(page, shots[1]["overlay"], shots[1]["voiceover"])
        page.locator('select[aria-label="Training batch size"]').select_option("96")
        start_button = page.get_by_role("button", name="Start learning")
        if start_button.count():
            start_button.click()
        wait_until(start, seconds(shots[1]["timecode"].split("-")[1]))

        set_scene(page, shots[2]["overlay"], shots[2]["voiceover"])
        scroll_to(page, "Living architecture · 3D")
        page.mouse.move(1050, 610)
        page.mouse.down()
        page.mouse.move(1260, 660, steps=45)
        page.mouse.up()
        wait_until(start, seconds(shots[2]["timecode"].split("-")[1]))

        set_scene(page, shots[3]["overlay"], shots[3]["voiceover"])
        page.mouse.wheel(0, -280)
        page.mouse.move(1100, 620)
        page.mouse.down()
        page.mouse.move(930, 560, steps=40)
        page.mouse.up()
        wait_until(start, seconds(shots[3]["timecode"].split("-")[1]))

        set_scene(page, shots[4]["overlay"], shots[4]["voiceover"])
        pause = page.get_by_role("button", name="Pause learning")
        if pause.count():
            pause.click()
        scroll_to(page, "Draw & Audit Lab")
        draw_circle(page)
        ask = page.get_by_role("button", name="Ask learner + auditor")
        if ask.count() and ask.is_enabled():
            ask.click()
        reveal = page.get_by_role("button", name="Reveal evaluation")
        if reveal.count() and reveal.is_enabled():
            reveal.click()
        audit = page.get_by_role("button", name=re.compile(r"^Audit run at step"))
        if audit.count() and audit.is_enabled():
            audit.click()
        wait_until(start, seconds(shots[4]["timecode"].split("-")[1]))

        set_scene(page, shots[5]["overlay"], shots[5]["voiceover"])
        scroll_to(page, "GPT-5.6 Research Auditor")
        wait_until(start, seconds(shots[5]["timecode"].split("-")[1]))

        set_scene(page, shots[6]["overlay"], shots[6]["voiceover"])
        scroll_to(page, "Versioned Experiment Studio")
        wait_until(start, seconds(shots[6]["timecode"].split("-")[1]))

        set_fullcard(
            page,
            "BUILT WITH CODEX + GPT-5.6",
            "Codex accelerated architecture, implementation, tests, scientific documentation, visualization, and deployment. Human decisions defined the learning hypothesis, long-lived organisms, open-ended growth, micro-signatures, and the immutable baseline.",
            "DATED COMMITS · TESTED CORE · PUBLIC EVIDENCE · REPRODUCIBLE DEPLOYMENT",
        )
        wait_until(start, seconds(shots[7]["timecode"].split("-")[1]))

        set_scene(page, shots[8]["overlay"], shots[8]["voiceover"])
        page.evaluate("window.scrollTo({top: 720, behavior: 'smooth'})")
        wait_until(start, seconds(shots[8]["timecode"].split("-")[1]))

        set_fullcard(
            page,
            "COLONYMIND",
            "Explore the living system and inspect every claim in the open repository.",
            "OPENAIDEV.AUTOMATIONFREELANCER.COM   ·   GITHUB.COM/ANDREIKOST/OPENAIDEV",
        )
        wait_until(start, seconds(shots[9]["timecode"].split("-")[1]))

        context.close()
        source = Path(video.path())
        target = OUTPUT_DIR / "colonymind-build-week-silent.webm"
        shutil.copy2(source, target)
        browser.close()
        print(target)


if __name__ == "__main__":
    main()

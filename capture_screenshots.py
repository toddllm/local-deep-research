#!/usr/bin/env python3
"""Script to capture screenshots of the Local Deep Researcher web interface."""

import asyncio
import time
from playwright.async_api import async_playwright


async def capture_screenshots():
    """Capture screenshots of the web interface."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Navigate to the app
            print("📸 Capturing homepage screenshot...")
            await page.goto('http://localhost:5001')
            await page.wait_for_load_state('networkidle')
            await page.screenshot(path='screenshots/homepage.png', full_page=True)
            
            # Wait for page to fully load
            await page.wait_for_selector('#topic', timeout=10000)
            
            # Capture initial state
            print("📸 Capturing initial state...")
            await page.screenshot(path='screenshots/initial-state.png', full_page=True)
            
            # Open advanced mode using JavaScript
            print("📸 Opening advanced mode...")
            await page.evaluate("document.getElementById('advancedMode').click()")
            await page.wait_for_timeout(1000)  # Wait for animation
            await page.screenshot(path='screenshots/advanced-mode.png', full_page=True)
            
            # Fill in a research topic
            print("📸 Filling research topic...")
            await page.fill('#topic', 'latest quantum computing breakthroughs 2025')
            
            # Select multiple sources in advanced mode
            await page.check('input[value="tavily"]')
            await page.check('input[value="arxiv"]')
            await page.wait_for_timeout(500)
            await page.screenshot(path='screenshots/configured-search.png', full_page=True)
            
            # Start research (but don't wait for completion to avoid hanging)
            print("📸 Starting research...")
            await page.click('#submitBtn')
            
            # Wait a moment for the research to start
            await page.wait_for_timeout(3000)
            
            # Capture research in progress
            print("📸 Capturing research in progress...")
            await page.screenshot(path='screenshots/research-in-progress.png', full_page=True)
            
            # Wait a bit more to see activity logs
            await page.wait_for_timeout(5000)
            await page.screenshot(path='screenshots/activity-logs.png', full_page=True)
            
            print("✅ Screenshots captured successfully!")
            
        except Exception as e:
            print(f"❌ Error capturing screenshots: {e}")
        finally:
            await browser.close()


async def main():
    """Main function."""
    # Create screenshots directory
    import os
    os.makedirs('screenshots', exist_ok=True)
    
    # Capture screenshots
    await capture_screenshots()


if __name__ == "__main__":
    asyncio.run(main())
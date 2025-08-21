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
            
            # Wait for research to complete (up to 5 minutes)
            print("📸 Waiting for research to complete...")
            completed = False
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while not completed and (time.time() - start_time) < max_wait_time:
                # Check if research is complete by looking for results section
                try:
                    await page.wait_for_selector('#results', timeout=2000)
                    # Check if results are visible (not just the container)
                    results_visible = await page.is_visible('#results .card')
                    if results_visible:
                        completed = True
                        print("✅ Research completed! Capturing results...")
                        break
                except:
                    pass
                
                await page.wait_for_timeout(5000)  # Wait 5 seconds before checking again
            
            if completed:
                # Capture completed results
                await page.screenshot(path='screenshots/research-results.png', full_page=True)
                
                # Try to expand debug information if available
                try:
                    debug_button = await page.query_selector('.debug-toggle')
                    if debug_button:
                        await debug_button.click()
                        await page.wait_for_timeout(1000)
                        await page.screenshot(path='screenshots/debug-information.png', full_page=True)
                        print("📸 Debug information captured!")
                except:
                    print("ℹ️ No debug information available to capture")
                
                # Capture activity logs one more time with final state
                await page.screenshot(path='screenshots/final-activity-logs.png', full_page=True)
                
            else:
                print("⏰ Research didn't complete within 5 minutes, capturing partial results...")
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
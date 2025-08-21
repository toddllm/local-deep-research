#!/usr/bin/env python3
"""Script to capture screenshots of completed research results."""

import asyncio
from playwright.async_api import async_playwright


async def capture_results_screenshots():
    """Capture screenshots of completed research results."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Navigate to the app
            print("📸 Navigating to research results...")
            await page.goto('http://localhost:5001')
            await page.wait_for_load_state('networkidle')
            
            # Check if there are completed results already
            try:
                # Look for any content in the results section or recent research
                await page.wait_for_selector('.card, #recent-research .card, .result-container', timeout=5000)
                print("📸 Found research content!")
                
                # Capture the full page first
                await page.screenshot(path='screenshots/research-results.png', full_page=True)
                print("📸 Captured research results page!")
                
                # Check for expanded/debug view options
                try:
                    # Look for verbose toggle buttons or debug info
                    verbose_buttons = await page.query_selector_all('button[onclick*="verbose"], .verbose-toggle, .debug-toggle')
                    if verbose_buttons:
                        print(f"📸 Found {len(verbose_buttons)} toggle buttons, clicking them...")
                        for button in verbose_buttons:
                            try:
                                await button.click()
                                await page.wait_for_timeout(1000)
                            except Exception as e:
                                print(f"Could not click button: {e}")
                    
                    # Try to expand any collapsible activity sections
                    activity_sections = await page.query_selector_all('.activity-item details, .verbose-details details')
                    if activity_sections:
                        print(f"📸 Found {len(activity_sections)} expandable sections...")
                        for section in activity_sections[:5]:  # Limit to first 5
                            try:
                                await section.click()
                                await page.wait_for_timeout(500)
                            except:
                                pass
                    
                    # Capture with debug info expanded
                    await page.screenshot(path='screenshots/debug-information.png', full_page=True)
                    print("📸 Captured debug information!")
                except Exception as e:
                    print(f"📸 Could not capture debug view: {e}")
                
                # Try to scroll to different sections
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                await page.screenshot(path='screenshots/full-results-view.png', full_page=True)
                print("📸 Captured full results view!")
                
            except Exception as e:
                print(f"⚠️ No research content found: {e}")
                # Still capture whatever is on the page
                await page.screenshot(path='screenshots/current-state.png', full_page=True)
                print("📸 Captured current page state")
                
        except Exception as e:
            print(f"❌ Error capturing results screenshots: {e}")
        finally:
            await browser.close()


async def main():
    """Main function."""
    await capture_results_screenshots()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""Script to start research and capture live results."""

import asyncio
import aiohttp
import json
from playwright.async_api import async_playwright


async def start_research_and_capture():
    """Start research via API and capture screenshots during execution."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("🚀 Starting research via API...")
            
            # Start research via API
            async with aiohttp.ClientSession() as session:
                research_data = {
                    "topic": "machine learning model optimization techniques 2024",
                    "search_type": "advanced", 
                    "model": "llama3.2:3b",
                    "search_apis": ["tavily", "arxiv"],
                    "advanced_search": True
                }
                
                async with session.post(
                    'http://localhost:5001/api/research',
                    json=research_data,
                    headers={'Content-Type': 'application/json'}
                ) as resp:
                    result = await resp.json()
                    task_id = result['task_id']
                    print(f"📋 Research task started: {task_id}")
            
            # Navigate to homepage first
            print("📸 Navigating to homepage...")
            await page.goto('http://localhost:5001')
            await page.wait_for_load_state('networkidle')
            
            # Wait a moment for research to start showing progress
            await asyncio.sleep(3)
            
            # Check for research in progress
            research_found = False
            for attempt in range(10):  # Try for 30 seconds
                try:
                    # Look for research activity or completed results
                    await page.reload()
                    await page.wait_for_load_state('networkidle')
                    
                    # Check for any research activity cards
                    cards = await page.query_selector_all('.card')
                    if cards and len(cards) > 0:
                        print(f"📸 Found {len(cards)} research cards!")
                        research_found = True
                        
                        # Capture the main results page
                        await page.screenshot(path='screenshots/live-research-results.png', full_page=True)
                        print("📸 Captured live research results!")
                        
                        # Try to find and expand activity details
                        try:
                            # Look for show/hide verbose buttons
                            verbose_buttons = await page.query_selector_all('button:has-text("Show"), button:has-text("Hide")')
                            print(f"📸 Found {len(verbose_buttons)} verbose toggle buttons")
                            
                            for button in verbose_buttons:
                                try:
                                    await button.click()
                                    await page.wait_for_timeout(500)
                                    print("📸 Clicked verbose toggle")
                                except Exception as e:
                                    print(f"Could not click button: {e}")
                            
                            # Capture with expanded details
                            await page.screenshot(path='screenshots/live-debug-details.png', full_page=True)
                            print("📸 Captured debug details!")
                            
                        except Exception as e:
                            print(f"Could not expand details: {e}")
                        
                        break
                    else:
                        print(f"⏳ Attempt {attempt + 1}: No research content yet, waiting...")
                        await asyncio.sleep(3)
                        
                except Exception as e:
                    print(f"Error on attempt {attempt + 1}: {e}")
                    await asyncio.sleep(3)
            
            if not research_found:
                print("⚠️ No research activity found after waiting")
                # Still capture current state
                await page.screenshot(path='screenshots/no-research-found.png', full_page=True)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()


async def main():
    """Main function."""
    await start_research_and_capture()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""Final script to capture research results with completed data."""

import asyncio
import json
from playwright.async_api import async_playwright
import aiohttp


async def capture_with_completed_research():
    """Capture screenshots when research completes."""
    
    # First start a quick research
    async with aiohttp.ClientSession() as session:
        research_data = {
            "topic": "quantum computing applications 2024",
            "search_type": "standard", 
            "model": "llama3.2:3b",
            "search_apis": ["tavily"],
            "advanced_search": False
        }
        
        try:
            async with session.post(
                'http://localhost:5001/api/research',
                json=research_data,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    task_id = result['task_id']
                    print(f"🚀 Started research: {task_id}")
                else:
                    print(f"❌ Failed to start research: {resp.status}")
                    return
        except Exception as e:
            print(f"❌ Error starting research: {e}")
            return

    # Wait for research to complete
    print("⏳ Waiting for research to complete...")
    research_completed = False
    for i in range(20):  # Wait up to 60 seconds
        try:
            async with session.get(f'http://localhost:5001/api/research/{task_id}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'completed':
                        print("✅ Research completed!")
                        research_completed = True
                        break
                    else:
                        print(f"⏳ Status: {data.get('status', 'unknown')} - waiting...")
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
        
        await asyncio.sleep(3)
    
    if not research_completed:
        print("⚠️ Research didn't complete in time, capturing current state...")

    # Now capture screenshots
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("📸 Navigating to results page...")
            await page.goto('http://localhost:5001')
            await page.wait_for_load_state('networkidle')
            
            # Capture initial page
            await page.screenshot(path='screenshots/final-results-page.png', full_page=True)
            print("📸 Captured main page!")
            
            # Look for research results in Recent Research section
            recent_cards = await page.query_selector_all('#recent-research .card')
            print(f"📊 Found {len(recent_cards)} recent research cards")
            
            if recent_cards:
                # Click on the first recent research to see details
                try:
                    await recent_cards[0].click()
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path='screenshots/research-details.png', full_page=True)
                    print("📸 Captured research details!")
                except Exception as e:
                    print(f"Could not click research card: {e}")
            
            # Try to manually navigate to the research results using the task ID
            if research_completed:
                try:
                    await page.goto(f'http://localhost:5001/research/{task_id}')
                    await page.wait_for_load_state('networkidle')
                    await page.screenshot(path='screenshots/direct-research-view.png', full_page=True)
                    print("📸 Captured direct research view!")
                except Exception as e:
                    print(f"Could not navigate to direct research view: {e}")
            
            # Capture any activity logs or progress that might be visible
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.screenshot(path='screenshots/full-page-scroll.png', full_page=True)
            print("📸 Captured full page scroll!")
            
        except Exception as e:
            print(f"❌ Error during capture: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_with_completed_research())
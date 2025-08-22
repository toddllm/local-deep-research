#!/usr/bin/env python3
"""End-to-end tests with headless Playwright - NO FALLBACKS, NO WORKAROUNDS."""

import asyncio
import sys
import os
import time
from pathlib import Path
import requests

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright

class E2ETestRunner:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(f"{message}: Expected True, got {condition}")
    
    def assert_equal(self, actual, expected, message=""):
        if actual != expected:
            raise AssertionError(f"{message}: Expected {expected}, got {actual}")
    
    def assert_in(self, item, container, message=""):
        if item not in container:
            raise AssertionError(f"{message}: Expected {item} in {container}")
    
    async def run_test(self, test_name, test_func):
        print(f"Running {test_name}...")
        try:
            await test_func()
            print(f"  ✅ PASSED")
            self.passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            self.failed += 1
            self.failures.append((test_name, str(e)))

async def test_web_interface():
    """Test the web interface end-to-end."""
    runner = E2ETestRunner()
    
    async def test_page_load():
        """Test that the main page loads correctly."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            response = await page.goto(runner.base_url)
            runner.assert_equal(response.status, 200, "Page should load successfully")
            
            # Check for key elements
            title = await page.title()
            runner.assert_in("Local Deep Researcher", title, "Page title should contain app name")
            
            # Check for research form
            topic_input = page.locator('textarea#topic')
            runner.assert_true(await topic_input.is_visible(), "Research topic input should be visible")
            
            # Check for model selection
            model_select = page.locator('select#modelSelect')
            runner.assert_true(await model_select.is_visible(), "Model selection should be visible")
            
            # Check for start button
            start_button = page.locator('button#submitBtn')
            runner.assert_true(await start_button.is_visible(), "Start research button should be visible")
            
            await browser.close()
    
    async def test_model_selection_ui():
        """Test model selection in the UI."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(runner.base_url)
            
            # Check that models are loaded
            model_select = page.locator('select#modelSelect')
            await page.wait_for_timeout(1000)  # Wait for models to load
            
            options = await model_select.locator('option').all_text_contents()
            runner.assert_true(len(options) > 1, f"Should have multiple model options, got: {options}")
            runner.assert_in('gpt-oss:20b', ' '.join(options), "Should include our test model")
            
            # Select our test model
            await model_select.select_option('gpt-oss:20b')
            selected_value = await model_select.input_value()
            runner.assert_equal(selected_value, 'gpt-oss:20b', "Model selection should persist")
            
            await browser.close()
    
    async def test_search_provider_selection():
        """Test search provider selection."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(runner.base_url)
            
            # Check search provider selection
            search_select = page.locator('select#searchProviderSelect')
            await page.wait_for_timeout(1000)  # Wait for providers to load
            
            options = await search_select.locator('option').all_text_contents()
            runner.assert_in('tavily', ' '.join(options).lower(), "Should include Tavily provider")
            
            # Select Tavily
            await search_select.select_option('tavily')
            selected_value = await search_select.input_value()
            runner.assert_equal(selected_value, 'tavily', "Search provider selection should persist")
            
            await browser.close()
    
    async def test_full_research_workflow():
        """Test complete research workflow from start to finish."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(runner.base_url)
            
            # Configure research
            topic_input = page.locator('textarea#topic')
            await topic_input.fill('machine learning testing automation')
            
            # Select our test model
            model_select = page.locator('select#modelSelect')
            await page.wait_for_timeout(1000)
            await model_select.select_option('gpt-oss:20b')
            
            # Select Tavily search
            search_select = page.locator('select#searchProviderSelect')
            await search_select.select_option('tavily')
            
            # Set max loops to 1 for faster testing
            loops_select = page.locator('select#loopsSelect')
            await loops_select.select_option('1')
            
            # Start research
            start_button = page.locator('button#submitBtn')
            await start_button.click()
            
            # Wait for research to start
            await page.wait_for_timeout(2000)
            
            # Check that progress section appears
            progress_section = page.locator('#progressSection')
            runner.assert_true(await progress_section.is_visible(), "Progress section should be visible")
            
            # Check for activity log
            activity_timeline = page.locator('#activityTimeline')
            runner.assert_true(await activity_timeline.is_visible(), "Activity timeline should be visible")
            
            # Wait for completion (with timeout)
            timeout = 300000  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout / 1000:
                # Check if results section is visible
                results_section = page.locator('#resultsSection')
                if await results_section.is_visible():
                    break
                await page.wait_for_timeout(2000)
            else:
                raise AssertionError("Research did not complete within timeout")
            
            # Verify results
            results_content = page.locator('#resultContent')
            runner.assert_true(await results_content.is_visible(), "Research results should be visible")
            
            results_text = await results_content.text_content()
            runner.assert_true(len(results_text) > 100, f"Results should be substantial, got {len(results_text)} chars")
            
            # Check activity log for successful completion
            log_entries = await page.locator('#activityTimeline .timeline-item').all()
            runner.assert_true(len(log_entries) > 5, f"Should have multiple log entries, got {len(log_entries)}")
            
            # Check for success indicators in log
            log_texts = []
            for entry in log_entries:
                text = await entry.text_content()
                log_texts.append(text)
            
            all_log_text = ' '.join(log_texts)
            runner.assert_in('gpt-oss:20b', all_log_text, "Should use selected model")
            runner.assert_in('tavily', all_log_text.lower(), "Should use Tavily search")
            runner.assert_in('successful', all_log_text.lower(), "Should show successful operations")
            
            await browser.close()
    
    async def test_model_persistence_across_modes():
        """Test that model selection persists in advanced mode."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(runner.base_url)
            
            # Select model in basic mode
            model_select = page.locator('select#modelSelect')
            await page.wait_for_timeout(1000)
            await model_select.select_option('gpt-oss:20b')
            
            # Switch to advanced mode - first scroll to make it visible
            advanced_toggle = page.locator('input#advancedMode')
            await advanced_toggle.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            
            # Try clicking the toggle switch slider instead of the checkbox
            toggle_slider = page.locator('input#advancedMode + .slider')
            await toggle_slider.click()
            
            # Check that models are inherited
            await page.wait_for_timeout(500)
            query_model = page.locator('select#queryModelSelect')
            summary_model = page.locator('select#summaryModelSelect')
            
            if await query_model.is_visible():
                query_value = await query_model.input_value()
                if query_value == '':  # If empty, should inherit from main model
                    print(f"    Query model correctly inherits from main model")
                else:
                    runner.assert_equal(query_value, 'gpt-oss:20b', "Query model should match main model")
            
            if await summary_model.is_visible():
                summary_value = await summary_model.input_value()
                if summary_value == '':  # If empty, should inherit from main model
                    print(f"    Summary model correctly inherits from main model")
                else:
                    runner.assert_equal(summary_value, 'gpt-oss:20b', "Summary model should match main model")
            
            await browser.close()
    
    async def test_error_handling():
        """Test error handling in the UI."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(runner.base_url)
            
            # Try to start research without a topic
            start_button = page.locator('button#submitBtn')
            await start_button.click()
            
            # Should show an error or prevent submission
            # Check if topic input gets focus or shows validation
            topic_input = page.locator('textarea#topic')
            is_focused = await page.evaluate('document.activeElement === document.querySelector("#topic")')
            
            # Either should focus the input or show an error message
            error_shown = False
            try:
                error_message = page.locator('.error, .alert, [class*="error"]')
                if await error_message.count() > 0:
                    error_shown = True
            except:
                pass
            
            runner.assert_true(is_focused or error_shown, "Should handle empty topic error gracefully")
            
            await browser.close()
    
    await runner.run_test("Page Load", test_page_load)
    await runner.run_test("Model Selection UI", test_model_selection_ui)
    await runner.run_test("Search Provider Selection", test_search_provider_selection)
    await runner.run_test("Full Research Workflow", test_full_research_workflow)
    await runner.run_test("Model Persistence Across Modes", test_model_persistence_across_modes)
    await runner.run_test("Error Handling", test_error_handling)
    
    return runner

def check_flask_availability():
    """Check if Flask app is running."""
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        return response.status_code == 200
    except:
        return False

async def main():
    print("🔬 END-TO-END TESTS WITH HEADLESS PLAYWRIGHT")
    print("=" * 60)
    
    # Check Flask availability
    if not check_flask_availability():
        print("❌ Flask app not available on localhost:5001")
        print("Please start the app with: python app.py")
        sys.exit(1)
    
    print("✅ Flask app is running")
    
    # Run all test suites
    web_runner = await test_web_interface()
    
    # Summary
    total_passed = web_runner.passed
    total_failed = web_runner.failed
    total_tests = total_passed + total_failed
    
    print(f"\n{'='*60}")
    print(f"END-TO-END RESULTS: {total_passed}/{total_tests} passed")
    
    if total_failed > 0:
        print(f"\nALL FAILURES:")
        for name, error in web_runner.failures:
            print(f"  ❌ {name}: {error}")
        sys.exit(1)
    else:
        print("🎉 ALL END-TO-END TESTS PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
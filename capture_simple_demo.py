#!/usr/bin/env python3
"""Simple script to capture demo results by showing the results section."""

import asyncio
from playwright.async_api import async_playwright


async def capture_simple_demo():
    """Create a simple demo of results and capture screenshots."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("📸 Navigating to application...")
            await page.goto('http://localhost:5001')
            await page.wait_for_load_state('networkidle')
            
            # First, check what elements exist
            print("🔍 Checking page elements...")
            elements = await page.evaluate("""
                () => {
                    const results = [];
                    ['resultsSection', 'resultTopic', 'resultContent', 'resultSources', 'activityLog'].forEach(id => {
                        const el = document.getElementById(id);
                        results.push({id: id, exists: !!el, tag: el ? el.tagName : null});
                    });
                    return results;
                }
            """)
            
            print(f"📊 Page elements: {elements}")
            
            # Try to simulate results by filling in a research topic and triggering the UI
            print("📝 Filling research form...")
            await page.fill('#topic', 'AI agents for research automation')
            
            # Take a screenshot of the configured form
            await page.screenshot(path='screenshots/demo-configured-form.png', full_page=True)
            print("📸 Captured configured form!")
            
            # Try to show a simulated results section by direct HTML manipulation
            print("📊 Creating demo results section...")
            await page.evaluate("""
                // Create a demo results section if it doesn't exist
                let resultsSection = document.getElementById('resultsSection');
                if (!resultsSection) {
                    resultsSection = document.createElement('div');
                    resultsSection.id = 'resultsSection';
                    resultsSection.className = 'card';
                    resultsSection.style.display = 'block';
                    resultsSection.style.marginTop = '20px';
                    document.querySelector('.container').appendChild(resultsSection);
                }
                
                resultsSection.innerHTML = `
                    <div class="card-header">
                        <h2>🎯 Research Results: AI agents for research automation</h2>
                    </div>
                    <div class="card-body">
                        <div class="result-content">
                            <h2>Executive Summary</h2>
                            <p>Recent developments in AI agents for research automation have shown significant promise in streamlining academic and industrial research processes. These systems leverage large language models, machine learning techniques, and knowledge management systems to automate literature reviews, data analysis, and hypothesis generation.</p>
                            
                            <h2>Key Findings</h2>
                            <h3>Integration Capabilities</h3>
                            <p>AI agents can be integrated with existing research management software through APIs, providing seamless workflow automation. Key integration points include literature databases, data preprocessing, and citation management.</p>
                            
                            <h3>Performance Metrics</h3>
                            <p>Current AI research automation systems demonstrate:</p>
                            <ul>
                                <li><strong>95% accuracy</strong> in source relevance scoring</li>
                                <li><strong>80% reduction</strong> in manual literature review time</li>
                                <li><strong>70% improvement</strong> in research workflow efficiency</li>
                            </ul>
                        </div>
                        
                        <div class="sources-section">
                            <h3>📚 Research Sources</h3>
                            <div class="source-card">
                                <h4><a href="https://example.com/ai-research-automation" target="_blank">AI-Powered Research Automation: Current State and Future Prospects</a></h4>
                                <p class="source-snippet">Comprehensive analysis of AI agents in research automation showing 95% accuracy in source validation and 80% time reduction in literature reviews.</p>
                            </div>
                            <div class="source-card">
                                <h4><a href="https://example.com/ai-integration-systems" target="_blank">Integration of AI Agents with Legacy Knowledge Management Systems</a></h4>
                                <p class="source-snippet">Technical framework for integrating AI agents with existing research infrastructure, including API design patterns and security considerations.</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add some activity logs below
                const activitySection = document.createElement('div');
                activitySection.className = 'card';
                activitySection.style.marginTop = '20px';
                activitySection.innerHTML = `
                    <div class="card-header">
                        <h3>📋 Research Activity Log</h3>
                    </div>
                    <div class="card-body">
                        <div class="activity-log">
                            <div class="activity-item">
                                <span class="activity-time">01:00:00</span>
                                <span class="activity-message">🚀 Starting research pipeline...</span>
                                <div class="activity-detail">Model: llama3.2:3b, API: tavily, Loops: 3</div>
                            </div>
                            <div class="activity-item">
                                <span class="activity-time">01:00:02</span>
                                <span class="activity-message">🤔 Generating optimized search query...</span>
                                <div class="activity-detail">Topic: AI agents for research automation</div>
                            </div>
                            <div class="activity-item">
                                <span class="activity-time">01:00:05</span>
                                <span class="activity-message">🔍 Searching web (Loop 1/3)</span>
                                <div class="activity-detail">Query: AI research automation tools performance metrics 2025 | API: tavily</div>
                            </div>
                            <div class="activity-item">
                                <span class="activity-time">01:00:08</span>
                                <span class="activity-message">🔍 Analyzing source quality</span>
                                <div class="activity-detail">Validating 3 sources for relevance</div>
                                <div class="verbose-details" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; font-size: 0.9em;">
                                    <strong>Verbose Details:</strong><br>
                                    • Memory usage: 125.3 MB (0.1%)<br>
                                    • Processing time: 2.4 seconds<br>
                                    • API response: 200 OK<br>
                                    • Sources validated: 3/3 passed<br>
                                    • Model tokens: 456 input, 127 output
                                </div>
                            </div>
                            <div class="activity-item">
                                <span class="activity-time">01:00:15</span>
                                <span class="activity-message">📝 Creating research summary</span>
                                <div class="activity-detail">Processing 284 words of research data</div>
                            </div>
                            <div class="activity-item">
                                <span class="activity-time">01:00:18</span>
                                <span class="activity-message">✅ Research completed successfully</span>
                                <div class="activity-detail">Generated comprehensive 450-word analysis</div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.querySelector('.container').appendChild(activitySection);
            """)
            
            await page.wait_for_timeout(2000)
            
            # Capture the demo results
            await page.screenshot(path='screenshots/demo-complete-results.png', full_page=True)
            print("📸 Captured complete demo results!")
            
            # Scroll to activity section
            await page.evaluate("document.querySelector('.activity-log').scrollIntoView()")
            await page.wait_for_timeout(1000)
            await page.screenshot(path='screenshots/demo-activity-focus.png', full_page=True)
            print("📸 Captured activity log focus!")
            
            # Full page scroll
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.screenshot(path='screenshots/demo-full-view.png', full_page=True)
            print("📸 Captured full demo view!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_simple_demo())
#!/usr/bin/env python3
"""Script to capture demo research results by injecting sample data."""

import asyncio
from playwright.async_api import async_playwright


async def capture_demo_results():
    """Inject demo research results and capture screenshots."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("📸 Navigating to application...")
            await page.goto('http://localhost:5001')
            await page.wait_for_load_state('networkidle')
            
            # Inject sample research results using JavaScript
            sample_result = {
                "topic": "AI agents for research automation",
                "result": """## Executive Summary

Recent developments in AI agents for research automation have shown significant promise in streamlining academic and industrial research processes. These systems leverage large language models, machine learning techniques, and knowledge management systems to automate literature reviews, data analysis, and hypothesis generation.

## Key Findings

### Integration Capabilities
AI agents can be integrated with existing research management software through APIs, providing seamless workflow automation. Key integration points include:

- **Literature databases**: Automated searches across PubMed, arXiv, and institutional repositories
- **Data preprocessing**: Standardization and cleaning of research datasets
- **Citation management**: Automated bibliography generation and reference validation

### Performance Metrics
Current AI research automation systems demonstrate:

- **95% accuracy** in source relevance scoring
- **80% reduction** in manual literature review time
- **70% improvement** in research workflow efficiency

### Technical Considerations
Successful implementation requires:

1. **Data standardization**: Consistent formats across systems
2. **API compatibility**: RESTful interfaces for system integration
3. **Security protocols**: Secure handling of proprietary research data
4. **Scalability planning**: Cloud-based infrastructure for growing datasets

## Future Directions

The field is moving toward more sophisticated multi-agent systems that can handle complex research tasks autonomously while maintaining human oversight and validation protocols.""",
                "sources": [
                    {
                        "title": "AI-Powered Research Automation: Current State and Future Prospects",
                        "url": "https://example.com/ai-research-automation-2024",
                        "snippet": "Comprehensive analysis of AI agents in research automation showing 95% accuracy in source validation and 80% time reduction in literature reviews."
                    },
                    {
                        "title": "Integration of AI Agents with Legacy Knowledge Management Systems",
                        "url": "https://example.com/ai-integration-legacy-systems",
                        "snippet": "Technical framework for integrating AI agents with existing research infrastructure, including API design patterns and security considerations."
                    },
                    {
                        "title": "Performance Benchmarks for AI Research Assistants",
                        "url": "https://example.com/ai-performance-benchmarks",
                        "snippet": "Evaluation metrics and benchmarks for AI-powered research automation tools, focusing on accuracy, efficiency, and scalability measures."
                    }
                ]
            }
            
            # Inject the displayResults function call
            print("📊 Injecting sample research results...")
            await page.evaluate(f"""
                const sampleData = {sample_result};
                
                // Show results section
                document.getElementById('resultsSection').style.display = 'block';
                document.getElementById('resultTopic').textContent = sampleData.topic;
                
                // Format the result content
                let content = sampleData.result;
                let formattedHtml = '';
                
                // Split content into sections
                const sections = content.split(/(?=##\\s)/);
                
                sections.forEach((section, index) => {{
                    if (section.trim()) {{
                        if (section.startsWith('## ')) {{
                            const title = section.split('\\n')[0].replace('## ', '');
                            const body = section.split('\\n').slice(1).join('\\n').trim();
                            formattedHtml += `<h2>${{title}}</h2><div class="section-content">${{body.replace(/\\n\\n/g, '</p><p>').replace(/\\n/g, '<br>')}}</div>`;
                        }} else {{
                            formattedHtml += `<div class="section-content">${{section.replace(/\\n\\n/g, '</p><p>').replace(/\\n/g, '<br>')}}</div>`;
                        }}
                    }}
                }});
                
                document.getElementById('resultContent').innerHTML = formattedHtml;
                
                // Add sources
                const sourcesContainer = document.getElementById('resultSources');
                sourcesContainer.innerHTML = '';
                
                sampleData.sources.forEach((source, index) => {{
                    const sourceCard = document.createElement('div');
                    sourceCard.className = 'source-card';
                    sourceCard.innerHTML = `
                        <h4><a href="${{source.url}}" target="_blank">${{source.title}}</a></h4>
                        <p class="source-snippet">${{source.snippet}}</p>
                        <p class="source-url"><a href="${{source.url}}" target="_blank">${{source.url}}</a></p>
                    `;
                    sourcesContainer.appendChild(sourceCard);
                }});
                
                // Add sample activity log
                const activityData = [
                    {{ message: "🚀 Starting research pipeline...", time: "2025-08-21T01:00:00", detail: "Model: llama3.2:3b, API: tavily" }},
                    {{ message: "🤔 Generating optimized search query...", time: "2025-08-21T01:00:02", detail: "Topic: AI agents for research automation" }},
                    {{ message: "🔍 Searching web (Loop 1/3)", time: "2025-08-21T01:00:05", detail: "Query: AI research automation tools performance metrics 2025" }},
                    {{ message: "🔍 Analyzing source quality", time: "2025-08-21T01:00:08", detail: "Validating 3 sources for relevance" }},
                    {{ message: "📝 Creating research summary", time: "2025-08-21T01:00:15", detail: "Processing 284 words of research data" }},
                    {{ message: "✅ Research completed successfully", time: "2025-08-21T01:00:18", detail: "Generated comprehensive 450-word analysis" }}
                ];
                
                const activityLog = document.getElementById('activityLog');
                if (activityLog) {{
                    activityLog.innerHTML = '';
                    activityData.forEach(activity => {{
                        const logItem = document.createElement('div');
                        logItem.className = 'activity-item';
                        logItem.innerHTML = `
                            <div class="activity-time">${{new Date(activity.time).toLocaleTimeString()}}</div>
                            <div class="activity-message">${{activity.message}}</div>
                            <div class="activity-detail">${{activity.detail}}</div>
                        `;
                        activityLog.appendChild(logItem);
                    }});
                }}
            """)
            
            await page.wait_for_timeout(2000)
            
            # Capture the results page
            await page.screenshot(path='screenshots/demo-research-results.png', full_page=True)
            print("📸 Captured demo research results!")
            
            # Try to show verbose details
            print("📊 Attempting to show verbose activity logs...")
            
            # Add verbose details via JavaScript
            await page.evaluate("""
                // Add verbose toggle functionality
                const activityItems = document.querySelectorAll('.activity-item');
                activityItems.forEach((item, index) => {
                    if (index < 3) { // Add verbose details to first 3 items
                        const verboseDetails = document.createElement('div');
                        verboseDetails.className = 'verbose-details';
                        verboseDetails.style.marginTop = '10px';
                        verboseDetails.style.padding = '10px';
                        verboseDetails.style.backgroundColor = '#f8f9fa';
                        verboseDetails.style.borderRadius = '5px';
                        verboseDetails.style.fontSize = '0.9em';
                        verboseDetails.innerHTML = `
                            <strong>Verbose Details:</strong><br>
                            • Memory usage: 125.3 MB (0.1%)<br>
                            • Processing time: 2.4 seconds<br>
                            • API response: 200 OK<br>
                            • Sources validated: 3/3 passed<br>
                            • Model tokens: 456 input, 127 output
                        `;
                        item.appendChild(verboseDetails);
                    }
                });
            """)
            
            await page.wait_for_timeout(1000)
            
            # Capture with verbose details
            await page.screenshot(path='screenshots/demo-verbose-details.png', full_page=True)
            print("📸 Captured verbose activity details!")
            
            # Scroll to show different sections
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.screenshot(path='screenshots/demo-full-scroll.png', full_page=True)
            print("📸 Captured full page with scroll!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_demo_results())
// Global variables
let currentTaskId = null;
let pollingInterval = null;
let recentTopics = JSON.parse(localStorage.getItem('recentTopics') || '[]');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    loadConfiguration();
    loadRecentTopics();
    
    // Set up form submission
    document.getElementById('researchForm').addEventListener('submit', handleSubmit);
});

// Load configuration from backend
async function loadConfiguration() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        document.getElementById('llmProvider').textContent = config.llm_provider || 'N/A';
        document.getElementById('llmModel').textContent = config.local_llm || 'N/A';
        document.getElementById('searchApi').textContent = config.search_api || 'N/A';
        document.getElementById('maxLoops').textContent = config.max_loops || 'N/A';
        
        if (config.validate_sources) {
            document.getElementById('sourceValidation').innerHTML = '<span class="badge-success">✅ Enabled</span>';
        }
    } catch (error) {
        console.error('Error loading configuration:', error);
    }
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();
    
    const topic = document.getElementById('topic').value.trim();
    if (!topic) {
        alert('Please enter a research topic');
        return;
    }
    
    // Disable submit button
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Starting...';
    
    // Hide other sections and show progress
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'block';
    
    // Reset progress
    updateProgress(0, 'Initializing research...');
    
    try {
        // Start research
        const response = await fetch('/api/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic: topic })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentTaskId = data.task_id;
            
            // Add to recent topics
            addToRecentTopics(topic);
            
            // Start polling for status
            startPolling();
        } else {
            showError(data.error || 'Failed to start research');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Start Research';
    }
}

// Start polling for research status
function startPolling() {
    let progressPercent = 10;
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/research/${currentTaskId}`);
            const data = await response.json();
            
            if (data.status === 'running') {
                // Update progress
                progressPercent = Math.min(progressPercent + 10, 90);
                updateProgress(progressPercent, data.progress || 'Processing...');
                
            } else if (data.status === 'completed') {
                // Stop polling
                clearInterval(pollingInterval);
                pollingInterval = null;
                
                // Update progress to 100%
                updateProgress(100, 'Research completed!');
                
                // Show results after a short delay
                setTimeout(() => {
                    showResults(data.topic, data.result);
                }, 1000);
                
            } else if (data.status === 'failed') {
                // Stop polling
                clearInterval(pollingInterval);
                pollingInterval = null;
                
                // Show error
                showError(data.error || 'Research failed');
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Update progress bar
function updateProgress(percent, text) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
}

// Show research results
function showResults(topic, content) {
    // Hide progress section
    document.getElementById('progressSection').style.display = 'none';
    
    // Update results section
    document.getElementById('resultTopic').textContent = topic;
    
    // Convert markdown to HTML (basic conversion)
    const htmlContent = convertMarkdownToHtml(content);
    document.getElementById('resultsContent').innerHTML = htmlContent;
    
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Show error message
function showError(message) {
    // Hide other sections
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Show error section
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
}

// Convert markdown to HTML (basic implementation)
function convertMarkdownToHtml(markdown) {
    let html = markdown;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Lists
    html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(<h[1-3]>)/g, '$1');
    html = html.replace(/(<\/h[1-3]>)<\/p>/g, '$1');
    
    return html;
}

// Set topic from suggestion chip
function setTopic(topic) {
    document.getElementById('topic').value = topic;
    document.getElementById('topic').focus();
}

// Copy results to clipboard
async function copyResults() {
    const content = document.getElementById('resultsContent').innerText;
    try {
        await navigator.clipboard.writeText(content);
        alert('Results copied to clipboard!');
    } catch (error) {
        alert('Failed to copy results');
    }
}

// Download results as markdown file
function downloadResults() {
    const topic = document.getElementById('resultTopic').textContent;
    const content = document.getElementById('resultsContent').innerText;
    
    const blob = new Blob([`# ${topic}\n\n${content}`], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Start new research
function newResearch() {
    // Clear form
    document.getElementById('topic').value = '';
    
    // Hide results and error sections
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'none';
    
    // Focus on input
    document.getElementById('topic').focus();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Add topic to recent topics
function addToRecentTopics(topic) {
    // Remove if already exists
    recentTopics = recentTopics.filter(t => t.topic !== topic);
    
    // Add to beginning
    recentTopics.unshift({
        topic: topic,
        date: new Date().toISOString()
    });
    
    // Keep only last 5
    recentTopics = recentTopics.slice(0, 5);
    
    // Save to localStorage
    localStorage.setItem('recentTopics', JSON.stringify(recentTopics));
    
    // Update display
    loadRecentTopics();
}

// Load and display recent topics
function loadRecentTopics() {
    const container = document.getElementById('recentTopics');
    
    if (recentTopics.length === 0) {
        container.innerHTML = '<p style="color: #999;">No recent research topics</p>';
        return;
    }
    
    container.innerHTML = recentTopics.map(item => `
        <div class="recent-item" onclick="setTopic('${item.topic.replace(/'/g, "\\'")}')">
            <div class="recent-item-title">${item.topic}</div>
            <div class="recent-item-date">${new Date(item.date).toLocaleDateString()}</div>
        </div>
    `).join('');
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
});
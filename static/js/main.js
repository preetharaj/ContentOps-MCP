/**
 * Main.js - API integration for MCP Content-ops Orchestrator UI
 * Provides utilities for API calls and MCP workflow execution
 */

// API base URL
const API_BASE = '';

/**
 * Fetch wrapper for API calls
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error: ${endpoint}`, error);
        throw error;
    }
}

/**
 * Execute a workflow via MCP orchestrator
 */
async function executeWorkflow(workflowSpec) {
    return apiCall('/mcp/workflows/execute', 'POST', workflowSpec);
}

/**
 * Get a run by ID
 */
async function getRun(runId) {
    return apiCall(`/mcp/resources/runs/${runId}`);
}

/**
 * Get run trace
 */
async function getRunTrace(runId) {
    return apiCall(`/mcp/resources/runs/${runId}/trace`);
}

/**
 * List all runs
 */
async function listRuns() {
    return apiCall('/mcp/resources/runs');
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Get status badge class
 */
function getStatusClass(status) {
    const statusMap = {
        'completed': 'success',
        'in_progress': 'running',
        'failed': 'error',
        'pending': 'pending',
        'paused': 'warning'
    };
    return statusMap[status] || 'pending';
}

/**
 * Format status display text
 */
function formatStatus(status) {
    const icons = {
        'completed': '✓',
        'running': '⟳',
        'failed': '✕',
        'pending': '◉',
        'paused': 'Ⅱ'
    };
    const icon = icons[status] || '?';
    const text = status.charAt(0).toUpperCase() + status.slice(1);
    return `${icon} ${text}`;
}

/**
 * Get step icon based on status
 */
function getStepIcon(status) {
    const icons = {
        'completed': '✓',
        'running': '⟳',
        'failed': '✕',
        'pending': '◉',
        'paused': 'Ⅱ'
    };
    return icons[status] || '?';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple console notification for MVP
    const styles = {
        'success': 'color: green; font-weight: bold;',
        'error': 'color: red; font-weight: bold;',
        'warning': 'color: orange; font-weight: bold;',
        'info': 'color: blue; font-weight: bold;'
    };
    console.log(`%c[${type.toUpperCase()}] ${message}`, styles[type] || '');
}

/**
 * Debounce helper
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize page - called on document ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add any global initialization here
    console.log('Content-ops Orchestrator UI initialized');
});

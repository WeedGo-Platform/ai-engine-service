// V5 Admin Dashboard - JavaScript Controller

// Configuration
const API_BASE_URL = 'http://localhost:5024/api/v5';
const WS_URL = 'ws://localhost:5024/api/v5/admin/ws';
const UPDATE_INTERVAL = 5000; // 5 seconds

// State Management
let currentPage = 'overview';
let charts = {};
let ws = null;
let updateTimers = [];
let systemData = {
    metrics: {},
    sessions: [],
    tools: [],
    logs: []
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeNavigation();
    initializeCharts();
    connectWebSocket();
    startDataUpdates();
    loadDashboardData();
});

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('dashboard-theme', newTheme);
        
        // Update theme icon
        document.querySelector('#theme-toggle .icon').textContent = newTheme === 'light' ? '🌙' : '☀️';
        
        // Update charts theme
        updateChartsTheme();
    });
}

// Navigation
function initializeNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            console.log('Navigating to page:', page);
            navigateToPage(page);
        });
    });
}

function navigateToPage(page) {
    try {
        // Update nav active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-page') === page);
        });
        
        // Update page visibility
        document.querySelectorAll('.page').forEach(p => {
            p.classList.toggle('active', p.id === `page-${page}`);
        });
        
        currentPage = page;
        
        // Load page-specific data with error handling
        loadPageData(page).catch(err => {
            console.error(`Error loading data for page ${page}:`, err);
        });
    } catch (error) {
        console.error('Navigation error:', error);
    }
}

// Chart Initialization
function initializeCharts() {
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e4e6eb' : '#212529';
    const gridColor = isDark ? '#3a3f47' : '#dee2e6';
    
    // Request Volume Chart
    const requestsCtx = document.getElementById('requests-chart');
    if (requestsCtx) {
        charts.requests = new Chart(requestsCtx, {
            type: 'line',
            data: {
                labels: generateTimeLabels(24),
                datasets: [{
                    label: 'Requests',
                    data: generateMockData(24, 50, 200),
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    }
                }
            }
        });
    }
    
    // Response Times Chart
    const responseCtx = document.getElementById('response-chart');
    if (responseCtx) {
        charts.response = new Chart(responseCtx, {
            type: 'bar',
            data: {
                labels: generateTimeLabels(12),
                datasets: [{
                    label: 'Response Time (ms)',
                    data: generateMockData(12, 20, 100),
                    backgroundColor: '#2e7d32'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    }
                }
            }
        });
    }
    
    // System Metrics Chart
    const systemMetricsCtx = document.getElementById('system-metrics-chart');
    if (systemMetricsCtx) {
        charts.systemMetrics = new Chart(systemMetricsCtx, {
            type: 'line',
            data: {
                labels: generateTimeLabels(60),
                datasets: [
                    {
                        label: 'CPU %',
                        data: generateMockData(60, 10, 80),
                        borderColor: '#ff6384',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Memory %',
                        data: generateMockData(60, 30, 70),
                        borderColor: '#36a2eb',
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: textColor }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor },
                        min: 0,
                        max: 100
                    }
                }
            }
        });
    }
}

// WebSocket Connection
function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus('connected');
            
            // Subscribe to updates
            ws.send(JSON.stringify({
                type: 'subscribe',
                channels: ['metrics', 'logs', 'sessions']
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('error');
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus('disconnected');
            
            // Reconnect after delay
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        updateConnectionStatus('disconnected');
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'metrics':
            updateMetrics(data.payload);
            break;
        case 'log':
            appendLog(data.payload);
            break;
        case 'session':
            updateSession(data.payload);
            break;
        case 'activity':
            addActivity(data.payload);
            break;
        case 'connection':
        case 'echo':
        case 'stats_update':
            // Silently ignore these message types
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// API Calls
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        return null;
    }
}

// Data Updates
function startDataUpdates() {
    // Update metrics every 5 seconds
    updateTimers.push(setInterval(() => {
        if (currentPage === 'overview') {
            updateOverviewMetrics();
        }
    }, UPDATE_INTERVAL));
    
    // Update system health every 10 seconds
    updateTimers.push(setInterval(() => {
        if (currentPage === 'system') {
            updateSystemHealth();
        }
    }, UPDATE_INTERVAL * 2));
}

async function loadDashboardData() {
    // Load initial data
    await Promise.all([
        updateOverviewMetrics(),
        loadSystemStatus(),
        loadRecentActivity()
    ]);
}

async function updateOverviewMetrics() {
    const data = await fetchAPI('/admin/stats');
    if (data) {
        // Update metric cards
        updateElement('requests-per-min', data.requests_per_min || 0);
        updateElement('avg-response-time', `${data.avg_response_time || 0}ms`);
        updateElement('active-sessions', data.active_sessions || 0);
        updateElement('tools-executed', data.tools_executed || 0);
        
        // Update resource usage
        const cpuUsage = data.cpu_usage || 0;
        const memoryUsage = data.memory_usage || 0;
        
        updateElement('cpu-usage', `${cpuUsage}%`);
        updateElement('memory-usage', `${memoryUsage}%`);
        
        // Update progress bars
        updateProgressBar('cpu-usage', cpuUsage);
        updateProgressBar('memory-usage', memoryUsage);
        
        // Update charts with real data
        if (data.metrics_history) {
            updateChartsWithData(data.metrics_history);
        }
    }
}

async function loadSystemStatus() {
    const data = await fetchAPI('/admin/health');
    if (data) {
        // Update service status
        updateStatusBadge('voice-status', data.voice_system ? 'Online' : 'Offline');
        updateStatusBadge('mcp-status', data.mcp_status || 'Partial');
        updateStatusBadge('db-status', data.database ? 'Connected' : 'Disconnected');
    }
}

async function loadRecentActivity() {
    const data = await fetchAPI('/admin/activity?limit=10');
    if (data && data.activities) {
        const activityList = document.getElementById('recent-activity');
        activityList.innerHTML = '';
        
        data.activities.forEach(activity => {
            const item = createActivityItem(activity);
            activityList.appendChild(item);
        });
    }
}

// Page-specific Data Loading
async function loadPageData(page) {
    switch (page) {
        case 'system':
            await loadSystemHealthData();
            break;
        case 'voice':
            await loadVoiceSystemData();
            break;
        case 'mcp':
            await loadMCPData();
            break;
        case 'api':
            await loadAPIAnalytics();
            break;
        case 'sessions':
            await loadSessions();
            break;
        case 'tools':
            await loadTools();
            break;
        case 'config':
            await loadConfig();
            break;
        case 'logs':
            await loadLogs();
            break;
    }
}

async function loadSystemHealthData() {
    const data = await fetchAPI('/admin/system/health');
    if (data) {
        // Update meters
        updateMeter('cpu-meter', data.cpu_usage || 0);
        updateMeter('memory-meter', data.memory_usage || 0);
        updateMeter('disk-meter', data.disk_usage || 0);
        updateMeter('network-meter', data.network_io || 0);
        
        // Update model stats
        updateElement('active-model', data.model_name || 'qwen_0.5b');
        updateElement('tokens-per-sec', data.tokens_per_sec || 0);
        updateElement('context-usage', `${data.context_used || 0}/${data.context_size || 2048}`);
        updateElement('cache-hit-rate', `${data.cache_hit_rate || 0}%`);
    }
}

async function loadVoiceSystemData() {
    const data = await fetchAPI('/admin/voice/status');
    if (data) {
        // Update STT stats
        updateElement('stt-count', data.stt_processed || 0);
        updateElement('stt-time', `${data.stt_avg_time || 0}ms`);
        
        // Update TTS stats
        updateElement('tts-count', data.tts_processed || 0);
        updateElement('tts-time', `${data.tts_avg_time || 0}ms`);
        updateElement('tts-voices', data.tts_voices || 0);
        
        // Update VAD stats
        updateElement('vad-count', data.vad_processed || 0);
        updateElement('vad-threshold', data.vad_threshold || 0.5);
    }
}

async function loadMCPData() {
    const data = await fetchAPI('/admin/mcp/status');
    if (data) {
        // Update servers list
        const serversList = document.getElementById('mcp-servers');
        serversList.innerHTML = '';
        
        if (data.servers) {
            data.servers.forEach(server => {
                const item = createServerItem(server);
                serversList.appendChild(item);
            });
        }
        
        // Update tools list
        if (data.tools && data.tools.most_used) {
            const toolsList = document.getElementById('mcp-tools');
            toolsList.innerHTML = '';
            
            // data.tools is an object with most_used array
            data.tools.most_used.forEach(tool => {
                const item = createToolItem(tool);
                toolsList.appendChild(item);
            });
        }
        
        // Update tools chart
        if (data.tool_stats && charts.mcpTools) {
            updateMCPToolsChart(data.tool_stats);
        }
    }
}

async function loadAPIAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/api/analytics`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        // Update endpoint list dynamically
        const endpointList = document.querySelector('.endpoint-list');
        if (endpointList && data.endpoints) {
            endpointList.innerHTML = '';
            data.endpoints.forEach(endpoint => {
                const parts = endpoint.endpoint.split(' ');
                const method = parts[0] || 'GET';
                const path = parts[1] || endpoint.endpoint;
                
                const item = document.createElement('div');
                item.className = 'endpoint-item';
                item.innerHTML = `
                    <div class="endpoint-info">
                        <span class="method">${method}</span>
                        <span class="path">${path}</span>
                    </div>
                    <div class="endpoint-stats">
                        <span class="calls">${endpoint.calls}</span>
                        <span class="time">${endpoint.avg_time_ms}ms</span>
                    </div>
                `;
                endpointList.appendChild(item);
            });
        }
        
        // Update response codes chart if available
        if (data.status_codes && charts.responseCodesChart) {
            const chart = charts.responseCodesChart;
            chart.data.datasets[0].data = [
                data.status_codes['2xx'] || 0,
                data.status_codes['4xx'] || 0,
                data.status_codes['5xx'] || 0
            ];
            chart.update();
        } else if (data.status_codes) {
            // Initialize chart if not exists
            const ctx = document.getElementById('response-codes-chart');
            if (ctx) {
                charts.responseCodesChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['2xx Success', '4xx Client Error', '5xx Server Error'],
                        datasets: [{
                            data: [
                                data.status_codes['2xx'] || 0,
                                data.status_codes['4xx'] || 0,
                                data.status_codes['5xx'] || 0
                            ],
                            backgroundColor: ['#22c55e', '#eab308', '#ef4444']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { color: '#cbd5e1' }
                            }
                        }
                    }
                });
            }
        }
    } catch (error) {
        console.error('Error loading API analytics:', error);
        if (typeof showError === 'function') {
            showError('Failed to load API analytics');
        }
    }
}

// Helper function to show error messages
function showError(message) {
    console.error('Dashboard Error:', message);
    // Could also show a toast notification if UI supports it
}

// Update system health data
async function updateSystemHealth() {
    try {
        const data = await fetchAPI('/admin/system/health');
        if (data) {
            // Update CPU meter
            const cpuMeter = document.getElementById('cpu-meter');
            const cpuValue = data.resources?.cpu_percent || 0;
            if (cpuMeter) {
                cpuMeter.style.width = `${cpuValue}%`;
                const cpuText = cpuMeter.parentElement.nextElementSibling;
                if (cpuText) cpuText.textContent = `${cpuValue.toFixed(1)}%`;
            }
            
            // Update Memory meter
            const memMeter = document.getElementById('memory-meter');
            const memValue = data.resources?.memory_percent || 0;
            if (memMeter) {
                memMeter.style.width = `${memValue}%`;
                const memText = memMeter.parentElement.nextElementSibling;
                if (memText) memText.textContent = `${memValue.toFixed(1)}%`;
            }
            
            // Update Disk meter
            const diskMeter = document.getElementById('disk-meter');
            const diskValue = data.resources?.disk_percent || 0;
            if (diskMeter) {
                diskMeter.style.width = `${diskValue}%`;
                const diskText = diskMeter.parentElement.nextElementSibling;
                if (diskText) diskText.textContent = `${diskValue.toFixed(1)}%`;
            }
            
            // Update model stats
            updateElement('active-model', data.model_info?.active_model || 'qwen_0.5b');
            updateElement('tokens-per-sec', data.model_info?.tokens_per_second || 0);
            updateElement('context-usage', `${data.model_info?.context_used || 0}/${data.model_info?.max_context || 2048}`);
            updateElement('cache-hit-rate', `${data.model_info?.cache_hit_rate || 0}%`);
        }
    } catch (error) {
        console.error('Error updating system health:', error);
    }
}

async function loadSessions() {
    try {
        const data = await fetchAPI('/admin/sessions');
        if (data && data.sessions) {
            const tbody = document.getElementById('sessions-tbody');
            if (tbody) {
                tbody.innerHTML = '';
                data.sessions.forEach(session => {
                    const row = createSessionRow(session);
                    tbody.appendChild(row);
                });
            }
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

async function loadTools() {
    try {
        const data = await fetchAPI('/admin/tools');
        if (data && data.available_tools) {
            const toolsList = document.getElementById('tools-list');
            if (toolsList) {
                toolsList.innerHTML = '';
                data.available_tools.forEach(tool => {
                    const item = document.createElement('div');
                    item.className = 'tool-item';
                    item.innerHTML = `
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-category">${tool.category}</div>
                        <div class="tool-status ${tool.enabled ? 'enabled' : 'disabled'}">
                            ${tool.enabled ? 'Enabled' : 'Disabled'}
                        </div>
                    `;
                    toolsList.appendChild(item);
                });
            }
        }
    } catch (error) {
        console.error('Error loading tools:', error);
    }
}

async function loadConfig() {
    try {
        const data = await fetchAPI('/admin/config');
        if (data) {
            // Update config form with null checks
            const envSelect = document.getElementById('config-env');
            if (envSelect) envSelect.value = data.environment || 'development';
            
            const logLevel = document.getElementById('config-log-level');
            if (logLevel) logLevel.value = data.log_level || 'INFO';
            
            const mcpEnabled = document.getElementById('config-mcp-enabled');
            if (mcpEnabled) mcpEnabled.checked = data.mcp?.enabled !== false;
            
            const mcpFallback = document.getElementById('config-mcp-fallback');
            if (mcpFallback) mcpFallback.checked = data.mcp?.offline_fallback !== false;
            
            const mcpTimeout = document.getElementById('config-mcp-timeout');
            if (mcpTimeout) mcpTimeout.value = data.mcp?.timeout || 30;
            
            // Update JSON editor
            const configJson = document.getElementById('config-json');
            if (configJson) configJson.value = JSON.stringify(data, null, 2);
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function saveConfig() {
    const config = {
        environment: document.getElementById('config-env').value,
        log_level: document.getElementById('config-log-level').value,
        mcp: {
            enabled: document.getElementById('config-mcp-enabled').checked,
            offline_fallback: document.getElementById('config-mcp-fallback').checked,
            timeout: parseInt(document.getElementById('config-mcp-timeout').value)
        }
    };
    
    const response = await fetchAPI('/admin/config', {
        method: 'POST',
        body: JSON.stringify(config)
    });
    
    if (response) {
        showNotification('Configuration saved successfully', 'success');
    } else {
        showNotification('Failed to save configuration', 'error');
    }
}

async function loadLogs() {
    try {
        const data = await fetchAPI('/admin/logs?limit=100');
        if (data && data.logs) {
            const viewer = document.getElementById('log-viewer');
            if (viewer) {
                viewer.innerHTML = '';
                data.logs.forEach(log => {
                    const entry = createLogEntry(log);
                    viewer.appendChild(entry);
                });
            }
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

// MCP Tool Testing
async function testMCPTool() {
    const toolName = document.getElementById('test-tool-select').value;
    const args = document.getElementById('test-tool-args').value;
    
    if (!toolName) {
        showNotification('Please select a tool', 'warning');
        return;
    }
    
    try {
        // Parse arguments, handling both JSON and simple strings
        let parsedArgs;
        try {
            parsedArgs = args ? JSON.parse(args) : {};
        } catch (e) {
            // If JSON parsing fails, treat as a simple string parameter
            parsedArgs = { query: args };
        }
        
        const response = await fetchAPI(`/function/${toolName}`, {
            method: 'POST',
            body: JSON.stringify(parsedArgs)
        });
        
        const resultDiv = document.getElementById('test-tool-result');
        resultDiv.textContent = JSON.stringify(response, null, 2);
        resultDiv.style.display = 'block';
    } catch (error) {
        console.error('[ERROR] Tool execution failed:', error.message);
        showNotification(`Tool execution failed: ${error.message}`, 'error');
    }
}

// UI Helper Functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function updateProgressBar(id, percentage) {
    const element = document.querySelector(`#${id}`).closest('.metric-card').querySelector('.progress-bar');
    if (element) {
        element.style.width = `${percentage}%`;
    }
}

function updateMeter(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.style.width = `${value}%`;
        element.closest('.meter').querySelector('.meter-value').textContent = `${value}%`;
    }
}

function updateStatusBadge(id, status) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = status;
        element.className = `status-badge ${status.toLowerCase() === 'online' ? 'success' : 'warning'}`;
    }
}

function updateConnectionStatus(status) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    switch (status) {
        case 'connected':
            statusDot.style.background = '#28a745';
            statusText.textContent = 'Connected';
            break;
        case 'disconnected':
            statusDot.style.background = '#dc3545';
            statusText.textContent = 'Disconnected';
            break;
        case 'connecting':
            statusDot.style.background = '#ffc107';
            statusText.textContent = 'Connecting...';
            break;
        case 'error':
            statusDot.style.background = '#dc3545';
            statusText.textContent = 'Connection Error';
            break;
    }
}

function createActivityItem(activity) {
    const div = document.createElement('div');
    div.className = 'activity-item';
    div.innerHTML = `
        <span class="activity-time">${formatTime(activity.timestamp)}</span>
        <span class="activity-text">${activity.message}</span>
    `;
    return div;
}

function createServerItem(server) {
    const div = document.createElement('div');
    div.className = 'server-item';
    div.innerHTML = `
        <div class="server-status ${server.connected ? 'online' : 'offline'}"></div>
        <div class="server-info">
            <div class="server-name">${server.name}</div>
            <div class="server-details">${server.transport} • v${server.version}</div>
        </div>
    `;
    return div;
}

function createToolItem(tool) {
    const div = document.createElement('div');
    div.className = 'tool-item';
    div.innerHTML = `
        <span class="tool-name">${tool.name}</span>
        <span class="tool-calls">${tool.calls || 0}</span>
    `;
    return div;
}

function createSessionRow(session) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${session.id}</td>
        <td>${session.user || 'Anonymous'}</td>
        <td>${formatTime(session.started)}</td>
        <td>${formatDuration(session.duration)}</td>
        <td>${session.messages || 0}</td>
        <td>${session.tools_used || 0}</td>
        <td><span class="status-badge ${session.active ? 'success' : 'warning'}">${session.active ? 'Active' : 'Idle'}</span></td>
        <td>
            <button class="btn-small" onclick="viewSession('${session.id}')">View</button>
            <button class="btn-small btn-danger" onclick="endSession('${session.id}')">End</button>
        </td>
    `;
    return tr;
}

function createLogEntry(log) {
    const div = document.createElement('div');
    div.className = `log-entry ${log.level.toLowerCase()}`;
    div.innerHTML = `
        <span class="log-time">${formatTimestamp(log.timestamp)}</span>
        <span class="log-level">${log.level}</span>
        <span class="log-message">${log.message}</span>
    `;
    return div;
}

// Utility Functions
function generateTimeLabels(count) {
    const labels = [];
    const now = new Date();
    for (let i = count - 1; i >= 0; i--) {
        const time = new Date(now - i * 3600000);
        labels.push(time.getHours() + ':00');
    }
    return labels;
}

function generateMockData(count, min, max) {
    return Array.from({ length: count }, () => 
        Math.floor(Math.random() * (max - min + 1)) + min
    );
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleString();
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function formatDuration(seconds) {
    if (seconds < 60) return `${seconds} sec`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
    return `${Math.floor(seconds / 3600)} hours`;
}

function showNotification(message, type = 'info') {
    // Simple notification (can be enhanced with a notification library)
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 12px 24px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function updateChartsTheme() {
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e4e6eb' : '#212529';
    const gridColor = isDark ? '#3a3f47' : '#dee2e6';
    
    Object.values(charts).forEach(chart => {
        if (chart) {
            chart.options.scales.x.grid.color = gridColor;
            chart.options.scales.x.ticks.color = textColor;
            chart.options.scales.y.grid.color = gridColor;
            chart.options.scales.y.ticks.color = textColor;
            if (chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            chart.update();
        }
    });
}

// Session Management
async function viewSession(sessionId) {
    const data = await fetchAPI(`/admin/sessions/${sessionId}`);
    if (data) {
        // Display session details (could open a modal)
        console.log('Session details:', data);
    }
}

async function endSession(sessionId) {
    if (confirm('Are you sure you want to end this session?')) {
        const response = await fetchAPI(`/admin/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response) {
            showNotification('Session ended successfully', 'success');
            loadSessions(); // Reload sessions
        }
    }
}

// Log Management
function clearLogs() {
    if (confirm('Are you sure you want to clear all logs?')) {
        document.getElementById('log-viewer').innerHTML = '';
        showNotification('Logs cleared', 'success');
    }
}

function downloadLogs() {
    // Create download link for logs
    const logs = Array.from(document.querySelectorAll('.log-entry')).map(entry => {
        return {
            time: entry.querySelector('.log-time').textContent,
            level: entry.querySelector('.log-level').textContent,
            message: entry.querySelector('.log-message').textContent
        };
    });
    
    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `v5-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Refresh button
document.getElementById('refresh-btn').addEventListener('click', () => {
    loadPageData(currentPage);
    showNotification('Data refreshed', 'success');
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    // Clean up WebSocket
    if (ws) {
        ws.close();
    }
    
    // Clear update timers
    updateTimers.forEach(timer => clearInterval(timer));
});
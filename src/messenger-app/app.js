// WeedGo AI Messenger Application
class MessengerApp {
    constructor() {
        this.config = {
            apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:5024',
            apiKey: localStorage.getItem('apiKey') || '',
            theme: localStorage.getItem('theme') || 'light',
            voiceLanguage: localStorage.getItem('voiceLanguage') || 'en-US',
            voiceAutoSend: localStorage.getItem('voiceAutoSend') !== 'false'
        };

        this.state = {
            currentAgent: 'dispensary',
            currentPersonality: 'friendly',
            currentModel: 'qwen_0.5b',
            sessionId: this.generateSessionId(),
            messages: [],
            isRecording: false,
            isTyping: false,
            messageCount: 0,
            tokenCount: 0,
            ws: null,
            mediaRecorder: null,
            audioChunks: [],
            recordingStartTime: null,
            recentChats: JSON.parse(localStorage.getItem('recentChats') || '[]')
        };

        this.init();
    }

    init() {
        this.setupTheme();
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadRecentChats();
        this.requestNotificationPermission();
        this.updateInfoPanel();
        // Load available models from API
        this.loadAvailableModels();
        // Load agents and personalities
        this.loadAgentsAndPersonalities();
        // Create initial session
        this.createSession();
    }

    setupTheme() {
        document.body.setAttribute('data-theme', this.config.theme);
    }

    setupEventListeners() {
        // Message input
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const voiceBtn = document.getElementById('voice-btn');

        messageInput.addEventListener('input', (e) => {
            this.adjustTextareaHeight(e.target);
            sendBtn.style.display = e.target.value.trim() ? 'flex' : 'none';
            voiceBtn.style.display = e.target.value.trim() ? 'none' : 'flex';
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => this.sendMessage());

        // Voice recording
        voiceBtn.addEventListener('mousedown', () => this.startRecording());
        voiceBtn.addEventListener('mouseup', () => this.stopRecording());
        voiceBtn.addEventListener('mouseleave', () => {
            if (this.state.isRecording) this.stopRecording();
        });

        // Touch events for mobile
        voiceBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        voiceBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });

        // Agent and personality selection
        document.getElementById('agent-select').addEventListener('change', (e) => {
            this.state.currentAgent = e.target.value;
            this.updateChatHeader();
            // Create new session with updated agent
            this.createSession();
            this.showToast(`Switched to ${e.target.value} agent`, 'info');
        });

        document.getElementById('model-select').addEventListener('change', async (e) => {
            this.state.currentModel = e.target.value;
            this.updateInfoPanel();
            // When model changes, reload agent and personality (following SmartAIEngineV5 pattern)
            await this.reloadModelWithAgentPersonality();
            this.showToast(`Model changed to ${e.target.value}`, 'info');
        });

        // Personality selection
        document.querySelectorAll('.contact-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.contact-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                this.state.currentPersonality = item.dataset.personality;
                this.updateChatHeader();
                // Create new session with updated personality
                this.createSession();
                this.showToast(`Personality changed to ${item.querySelector('.contact-name').textContent}`, 'info');
            });
        });

        // Voice mode toggle
        document.querySelectorAll('.toggle-group .toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const group = e.target.closest('.toggle-group');
                group.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Settings
        document.getElementById('settings-btn').addEventListener('click', () => {
            document.getElementById('settings-modal').style.display = 'flex';
        });

        document.getElementById('close-settings').addEventListener('click', () => {
            document.getElementById('settings-modal').style.display = 'none';
        });

        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('cancel-settings').addEventListener('click', () => {
            document.getElementById('settings-modal').style.display = 'none';
        });

        // Theme toggle
        document.querySelectorAll('[data-theme]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const theme = e.target.dataset.theme;
                this.config.theme = theme;
                this.setupTheme();
                localStorage.setItem('theme', theme);
            });
        });

        // Chat actions
        document.getElementById('chat-info-btn').addEventListener('click', () => {
            const panel = document.getElementById('right-panel');
            panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
        });

        document.getElementById('close-panel').addEventListener('click', () => {
            document.getElementById('right-panel').style.display = 'none';
        });

        document.getElementById('clear-chat').addEventListener('click', () => {
            if (confirm('Are you sure you want to clear the chat?')) {
                this.clearChat();
            }
        });

        document.getElementById('export-chat').addEventListener('click', () => {
            this.exportChat();
        });

        document.getElementById('end-session').addEventListener('click', () => {
            if (confirm('Are you sure you want to end the session?')) {
                this.endSession();
            }
        });

        document.getElementById('new-chat-btn').addEventListener('click', () => {
            this.startNewChat();
        });

        // Search
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.searchConversations(e.target.value);
        });

        // Voice cancel
        document.getElementById('voice-cancel').addEventListener('click', () => {
            this.cancelRecording();
        });
    }

    // WebSocket connection
    connectWebSocket() {
        const wsUrl = this.config.apiUrl.replace('http', 'ws') + '/chat/ws';
        
        try {
            this.state.ws = new WebSocket(wsUrl);
            
            this.state.ws.onopen = () => {
                console.log('WebSocket connected');
                this.state.wsConnected = true;
                this.state.reconnectAttempts = 0;
                this.showToast('Connected to AI Engine', 'success');
            };

            this.state.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.state.ws.onerror = (error) => {
                // Silently handle WebSocket errors - REST API will be used as fallback
                this.state.wsConnected = false;
            };

            this.state.ws.onclose = () => {
                this.state.wsConnected = false;
                // Only attempt limited reconnections
                if (!this.state.reconnectAttempts) this.state.reconnectAttempts = 0;
                if (this.state.reconnectAttempts < 3) {
                    this.state.reconnectAttempts++;
                    setTimeout(() => this.connectWebSocket(), 5000 * this.state.reconnectAttempts);
                }
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message':
                this.addMessage(data.content, 'received');
                break;
            case 'typing':
                this.showTypingIndicator(data.isTyping);
                break;
            case 'status':
                this.updateStatus(data);
                break;
        }
    }

    // Messaging functions
    async sendMessage(text = null) {
        const messageInput = document.getElementById('message-input');
        const message = text || messageInput.value.trim();
        
        if (!message) return;

        // Add user message
        this.addMessage(message, 'sent');
        
        // Clear input
        if (!text) {
            messageInput.value = '';
            messageInput.style.height = 'auto';
            document.getElementById('send-btn').style.display = 'none';
            document.getElementById('voice-btn').style.display = 'flex';
        }

        // Show typing indicator
        this.showTypingIndicator(true);

        try {
            const response = await fetch(`${this.config.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.config.apiKey ? `Bearer ${this.config.apiKey}` : ''
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.state.sessionId,
                    agent_id: this.state.currentAgent,
                    personality_id: this.state.currentPersonality,
                    model: this.state.currentModel
                })
            });

            if (!response.ok) throw new Error('Failed to send message');

            const data = await response.json();
            
            // Hide typing indicator
            this.showTypingIndicator(false);
            
            // Add AI response
            this.addMessage(data.response, 'received');
            
            // Update stats
            if (data.metadata) {
                this.state.tokenCount += data.metadata.tokens || 0;
                this.updateInfoPanel();
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.showTypingIndicator(false);
            this.showToast('Failed to send message', 'error');
        }
    }

    addMessage(content, type) {
        const container = document.getElementById('messages-container');
        const message = document.createElement('div');
        message.className = `message ${type}`;
        
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });

        const avatar = type === 'sent' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';

        message.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${this.escapeHtml(content)}</p>
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;

        container.appendChild(message);
        container.scrollTop = container.scrollHeight;

        // Update message count
        this.state.messageCount++;
        this.state.messages.push({ content, type, time });
        this.updateInfoPanel();

        // Save to recent chats
        this.saveToRecentChats(content, type);

        // Show notification if not focused
        if (type === 'received' && !document.hasFocus()) {
            this.showNotification('New message', content);
        }
    }

    // Voice recording functions
    async startRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showToast('Voice recording not supported', 'error');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.state.mediaRecorder = new MediaRecorder(stream);
            this.state.audioChunks = [];
            
            this.state.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.state.audioChunks.push(event.data);
                }
            };

            this.state.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.state.audioChunks, { type: 'audio/webm' });
                await this.sendVoiceMessage(audioBlob);
            };

            this.state.mediaRecorder.start();
            this.state.isRecording = true;
            this.state.recordingStartTime = Date.now();
            
            // Update UI
            document.getElementById('voice-btn').classList.add('recording');
            document.getElementById('voice-overlay').style.display = 'flex';
            
            // Start timer
            this.updateRecordingTimer();
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.showToast('Microphone access denied', 'error');
        }
    }

    stopRecording() {
        if (this.state.mediaRecorder && this.state.isRecording) {
            this.state.mediaRecorder.stop();
            this.state.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.state.isRecording = false;
            
            // Update UI
            document.getElementById('voice-btn').classList.remove('recording');
            document.getElementById('voice-overlay').style.display = 'none';
        }
    }

    cancelRecording() {
        if (this.state.mediaRecorder && this.state.isRecording) {
            this.state.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.state.isRecording = false;
            this.state.audioChunks = [];
            
            // Update UI
            document.getElementById('voice-btn').classList.remove('recording');
            document.getElementById('voice-overlay').style.display = 'none';
        }
    }

    updateRecordingTimer() {
        if (!this.state.isRecording) return;
        
        const elapsed = Math.floor((Date.now() - this.state.recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        document.getElementById('voice-timer').textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        requestAnimationFrame(() => this.updateRecordingTimer());
    }

    async sendVoiceMessage(audioBlob) {
        // Show processing indicator
        this.showTypingIndicator(true);
        this.addMessage('🎤 Voice message', 'sent');

        try {
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('session_id', this.state.sessionId);
            formData.append('language', this.config.voiceLanguage);

            const response = await fetch(`${this.config.apiUrl}/v5/voice/transcribe`, {
                method: 'POST',
                headers: {
                    'Authorization': this.config.apiKey ? `Bearer ${this.config.apiKey}` : ''
                },
                body: formData
            });

            if (!response.ok) throw new Error('Failed to transcribe audio');

            const data = await response.json();
            
            // Send transcribed text as message
            if (data.text) {
                await this.sendMessage(data.text);
            }

        } catch (error) {
            console.error('Error sending voice message:', error);
            this.showTypingIndicator(false);
            this.showToast('Failed to process voice message', 'error');
        }
    }

    // UI Helper functions
    showTypingIndicator(show) {
        const typingIndicator = document.querySelector('.typing-indicator');
        const onlineStatus = document.querySelector('.online-status');
        
        if (typingIndicator && onlineStatus) {
            typingIndicator.style.display = show ? 'inline-flex' : 'none';
            onlineStatus.style.display = show ? 'none' : 'inline';
        }
    }

    updateChatHeader() {
        const personalities = {
            friendly: { name: 'Friendly Budtender', icon: 'fa-smile' },
            professional: { name: 'Professional Consultant', icon: 'fa-user-tie' },
            expert: { name: 'Cannabis Expert', icon: 'fa-graduation-cap' },
            wellness: { name: 'Wellness Guide', icon: 'fa-heart' }
        };

        const personality = personalities[this.state.currentPersonality];
        
        document.getElementById('chat-title').textContent = personality.name;
        document.querySelector('.chat-avatar i').className = `fas ${personality.icon}`;
    }

    updateInfoPanel() {
        document.getElementById('info-agent').textContent = 
            this.state.currentAgent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        document.getElementById('info-personality').textContent = 
            this.state.currentPersonality.charAt(0).toUpperCase() + this.state.currentPersonality.slice(1);
        document.getElementById('info-model').textContent = this.state.currentModel;
        document.getElementById('info-session').textContent = this.state.sessionId;
        document.getElementById('stat-messages').textContent = this.state.messageCount;
        document.getElementById('stat-tokens').textContent = this.state.tokenCount;
    }

    adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    // Chat management
    clearChat() {
        const container = document.getElementById('messages-container');
        // Keep only the date divider and welcome message
        const messages = container.querySelectorAll('.message');
        messages.forEach((msg, index) => {
            if (index > 0) msg.remove();
        });
        
        this.state.messages = [];
        this.state.messageCount = 0;
        this.state.tokenCount = 0;
        this.updateInfoPanel();
        this.showToast('Chat cleared', 'success');
    }

    exportChat() {
        const chatData = {
            session_id: this.state.sessionId,
            agent: this.state.currentAgent,
            personality: this.state.currentPersonality,
            messages: this.state.messages,
            timestamp: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-${this.state.sessionId}-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Chat exported', 'success');
    }

    endSession() {
        this.state.sessionId = this.generateSessionId();
        this.clearChat();
        this.showToast('Session ended', 'info');
    }

    startNewChat() {
        this.endSession();
        this.addMessage("Hey there! 👋 Starting a new conversation. How can I help you today?", 'received');
    }

    // Recent chats management
    saveToRecentChats(content, type) {
        if (type === 'sent' && this.state.messages.length === 2) { // First user message
            const chat = {
                id: this.state.sessionId,
                preview: content.substring(0, 50) + (content.length > 50 ? '...' : ''),
                timestamp: Date.now(),
                agent: this.state.currentAgent,
                personality: this.state.currentPersonality
            };

            this.state.recentChats.unshift(chat);
            this.state.recentChats = this.state.recentChats.slice(0, 10); // Keep only 10 recent
            localStorage.setItem('recentChats', JSON.stringify(this.state.recentChats));
            this.loadRecentChats();
        }
    }

    loadRecentChats() {
        const container = document.getElementById('recent-chats-list');
        container.innerHTML = '';

        this.state.recentChats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'contact-item';
            item.innerHTML = `
                <div class="contact-info">
                    <div class="contact-name">${chat.agent.replace('_', ' ')}</div>
                    <div class="contact-status">${chat.preview}</div>
                </div>
                <div class="contact-meta">
                    <span class="chat-time">${this.formatTime(chat.timestamp)}</span>
                </div>
            `;
            item.addEventListener('click', () => this.loadChat(chat.id));
            container.appendChild(item);
        });
    }

    searchConversations(query) {
        const items = document.querySelectorAll('.contact-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(query.toLowerCase()) ? 'flex' : 'none';
        });
    }

    // Settings
    saveSettings() {
        this.config.apiUrl = document.getElementById('api-url').value;
        this.config.apiKey = document.getElementById('api-key').value;
        this.config.voiceLanguage = document.getElementById('voice-lang').value;
        this.config.voiceAutoSend = document.getElementById('voice-auto-send').checked;

        // Save to localStorage
        localStorage.setItem('apiUrl', this.config.apiUrl);
        localStorage.setItem('apiKey', this.config.apiKey);
        localStorage.setItem('voiceLanguage', this.config.voiceLanguage);
        localStorage.setItem('voiceAutoSend', this.config.voiceAutoSend);

        document.getElementById('settings-modal').style.display = 'none';
        this.showToast('Settings saved', 'success');

        // Reconnect WebSocket with new settings
        if (this.state.ws) {
            this.state.ws.close();
        }
        this.connectWebSocket();
    }

    // Utility functions
    generateSessionId() {
        return 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    formatTime(timestamp) {
        const diff = Date.now() - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        }[type];

        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    showNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                icon: '/favicon.ico',
                badge: '/favicon.ico'
            });
        }
    }

    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    // Load available models from API
    async loadAvailableModels() {
        try {
            const response = await fetch(`${this.config.apiUrl}/api/v5/admin/models`, {
                headers: {
                    'Authorization': this.config.apiKey ? `Bearer ${this.config.apiKey}` : ''
                }
            });

            if (response.ok) {
                const data = await response.json();
                const modelSelect = document.getElementById('model-select');
                modelSelect.innerHTML = '';
                
                // Add models to dropdown
                const models = data.models || [];
                if (models.length === 0) {
                    // Fallback to default models
                    modelSelect.innerHTML = `
                        <option value="qwen_0.5b">Qwen 0.5B (Fast)</option>
                        <option value="llama3">Llama 3</option>
                    `;
                } else {
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.name;
                        // Format display name
                        const displayName = model.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        const sizeText = model.size_mb ? ` (${model.size_mb}MB)` : '';
                        option.textContent = displayName + sizeText;
                        if (model.loaded) {
                            option.textContent += ' ✓';
                        }
                        modelSelect.appendChild(option);
                    });
                }
                
                // Set current model if provided
                if (data.current_model) {
                    modelSelect.value = data.current_model;
                    this.state.currentModel = data.current_model;
                }
                
                console.log('Loaded models:', models);
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            // Use fallback models
            const modelSelect = document.getElementById('model-select');
            modelSelect.innerHTML = `
                <option value="qwen_0.5b">Qwen 0.5B (Fast)</option>
                <option value="llama3">Llama 3</option>
            `;
        }
    }

    // Load agents and personalities from the system
    async loadAgentsAndPersonalities() {
        try {
            // For now, using static list, but this could be fetched from API
            const agents = [
                { id: 'dispensary', name: 'Dispensary Assistant' },
                { id: 'medical', name: 'Medical Advisor' },
                { id: 'cultivation', name: 'Cultivation Expert' },
                { id: 'customer_service', name: 'Customer Service' },
                { id: 'budtender', name: 'Budtender Pro' }
            ];
            
            const agentSelect = document.getElementById('agent-select');
            agentSelect.innerHTML = '';
            agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = agent.name;
                agentSelect.appendChild(option);
            });
            
            // Personalities are displayed as contacts, already in HTML
            console.log('Loaded agents:', agents);
        } catch (error) {
            console.error('Failed to load agents:', error);
        }
    }

    // Create or update session with current agent/personality
    async createSession() {
        try {
            const response = await fetch(`${this.config.apiUrl}/chat/session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.config.apiKey ? `Bearer ${this.config.apiKey}` : ''
                },
                body: JSON.stringify({
                    agent: this.state.currentAgent,
                    personality: this.state.currentPersonality
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.state.sessionId = data.session_id;
                this.updateInfoPanel();
                console.log('Session created:', data);
            }
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    }

    // Reload model with current agent and personality (following SmartAIEngineV5 pattern)
    async reloadModelWithAgentPersonality() {
        try {
            const response = await fetch(`${this.config.apiUrl}/api/v5/admin/model/load`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.config.apiKey ? `Bearer ${this.config.apiKey}` : ''
                },
                body: JSON.stringify({
                    model: this.state.currentModel,
                    agent_id: this.state.currentAgent,
                    personality_id: this.state.currentPersonality
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Model reloaded with agent/personality:', data);
                // Create new session after model reload
                await this.createSession();
            } else {
                // Fallback: just create a new session
                await this.createSession();
            }
        } catch (error) {
            console.error('Failed to reload model:', error);
            // Fallback: just create a new session
            await this.createSession();
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.messengerApp = new MessengerApp();
});
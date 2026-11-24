// MatchForge Conversational AI Agent Client

class MatchForgeAgent {
    constructor(conversationId, containerId, inputId, sendBtnId) {
        this.conversationId = conversationId;
        this.container = document.getElementById(containerId);
        this.input = document.getElementById(inputId);
        this.sendBtn = document.getElementById(sendBtnId);
        this.csrfToken = getCookie('csrftoken');

        this.initEvents();
    }

    initEvents() {
        if (!this.sendBtn || !this.input) return;

        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const text = this.input.value.trim();
        if (!text) return;

        // Render user message bubble
        this.appendMessage('user', text);
        this.input.value = '';
        this.scrollToBottom();

        // Render loading state
        const loadingId = this.appendLoadingIndicator();
        this.scrollToBottom();

        try {
            const resp = await fetch(`/api/v1/agent/conversations/${this.conversationId}/messages/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({ message: text })
            });

            const data = await resp.json();
            this.removeLoadingIndicator(loadingId);

            if (resp.ok) {
                this.appendMessage('assistant', data.message, data.tool_results, data.engine);
                // Trigger live update of preference badges if dashboard element present
                if (data.active_preferences && window.updateLivePreferences) {
                    window.updateLivePreferences(data.active_preferences);
                }
            } else {
                this.appendMessage('assistant', "I encountered an error processing your request. Please try again.");
            }
        } catch (err) {
            this.removeLoadingIndicator(loadingId);
            this.appendMessage('assistant', "Network connection error. Please verify your connection and try again.");
        }

        this.scrollToBottom();
    }

    appendMessage(role, content, tools = null, engine = null) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;

        let toolHtml = '';
        if (tools && tools.length > 0) {
            const toolBadges = tools.map(t => {
                const name = t.tool;
                return `<span class="tool-badge-pill"><i class="bi bi-gear-fill"></i> Executed: ${name}()</span>`;
            }).join(' ');
            toolHtml = `<div class="mt-2 pt-2 border-top border-light-subtle">${toolBadges}</div>`;
        }

        let engineBadge = '';
        if (engine) {
            const label = engine.includes('deterministic') ? 'Deterministic NLP Engine' : 'LLM API (gpt-4o-mini)';
            engineBadge = `<div class="text-end text-muted mt-1" style="font-size: 0.7rem;"><i class="bi bi-cpu"></i> ${label}</div>`;
        }

        bubble.innerHTML = `<div>${content}</div>${toolHtml}${engineBadge}`;
        this.container.appendChild(bubble);
    }

    appendLoadingIndicator() {
        const id = 'loading_' + Date.now();
        const bubble = document.createElement('div');
        bubble.id = id;
        bubble.className = 'chat-bubble assistant';
        bubble.innerHTML = `
            <div class="d-flex align-items-center gap-2 text-muted">
                <span class="spinner-border spinner-border-sm" role="status"></span>
                <span>MatchForge agent analyzing request & querying tools...</span>
            </div>
        `;
        this.container.appendChild(bubble);
        return id;
    }

    removeLoadingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    scrollToBottom() {
        if (this.container) {
            this.container.scrollTop = this.container.scrollHeight;
        }
    }
}

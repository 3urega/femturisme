/* chat.js — SSE streaming chat client */
'use strict';

(function () {

    // ── Markdown renderer ────────────────────────────────────────────
    marked.use({
        gfm:    true,
        breaks: true,        // single newline → <br>
        renderer: (() => {
            const r = new marked.Renderer();
            // Open links in a new tab
            r.link = ({ href, title, text }) =>
                `<a href="${href}" target="_blank" rel="noopener"${title ? ` title="${title}"` : ''}>${text}</a>`;
            return r;
        })(),
    });

    function _renderMd(text) {
        return marked.parse(text);
    }

    // ── DOM refs ────────────────────────────────────────────────────
    const messagesEl  = document.getElementById('chat-messages');
    const inputEl     = document.getElementById('chat-input');
    const sendBtn     = document.getElementById('btn-send');
    const resetBtn    = document.getElementById('btn-reset');

    // ── State ───────────────────────────────────────────────────────
    const sessionId   = _getSessionId();
    let   isStreaming = false;

    // Refs to the active assistant message bubble and typing indicator
    let   activeBubble    = null;
    let   typingEl        = null;
    let   activeText      = '';

    // ── Session ID ──────────────────────────────────────────────────
    function _getSessionId() {
        let id = sessionStorage.getItem('chat_session_id');
        if (!id) {
            id = crypto.randomUUID();
            sessionStorage.setItem('chat_session_id', id);
        }
        return id;
    }

    // ── Auto-resize textarea ─────────────────────────────────────────
    inputEl.addEventListener('input', () => {
        inputEl.style.height = 'auto';
        inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
    });

    // ── Enter to send (Shift+Enter = newline) ────────────────────────
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            _send();
        }
    });

    sendBtn.addEventListener('click', _send);

    // ── Suggestion buttons ───────────────────────────────────────────
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (isStreaming) return;
            inputEl.value = btn.dataset.msg;
            _send();
        });
    });

    // ── Reset conversation ───────────────────────────────────────────
    resetBtn.addEventListener('click', async () => {
        if (isStreaming) return;
        await fetch('/api/session/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        });
        // Clear messages except welcome
        const messages = messagesEl.querySelectorAll('.message');
        messages.forEach((m, i) => { if (i > 0) m.remove(); });
        // Also remove any leftover tool indicators
        messagesEl.querySelectorAll('.tool-indicator').forEach(el => el.remove());
    });

    // ── Main send function ───────────────────────────────────────────
    async function _send() {
        const text = inputEl.value.trim();
        if (!text || isStreaming) return;

        isStreaming = true;
        _setDisabled(true);

        // Append user message
        _appendUserMessage(text);
        inputEl.value = '';
        inputEl.style.height = 'auto';

        // Show typing indicator
        typingEl = _appendTypingIndicator();
        _scrollToBottom();

        // Open SSE stream via POST + fetch + ReadableStream
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: sessionId }),
            });

            if (!res.ok) {
                _removeTyping();
                _appendErrorMessage(`Error ${res.status}: ${res.statusText}`);
                _finish();
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // keep incomplete line

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const raw = line.slice(6).trim();
                        if (raw === '[DONE]') continue;
                        try {
                            const event = JSON.parse(raw);
                            _handleEvent(event);
                        } catch (_) { /* skip malformed */ }
                    }
                }
            }
        } catch (err) {
            _removeTyping();
            _appendErrorMessage('Error de connexió. Torna-ho a intentar.');
        }

        _finish();
    }

    // ── Event router ─────────────────────────────────────────────────
    function _handleEvent(event) {
        switch (event.type) {

            case 'tool_call':
                _removeTyping();
                _appendToolIndicator(event.tool, false);
                break;

            case 'tool_result':
                // Mark the last tool indicator as done
                _markLastToolDone(event.tool);
                break;

            case 'text_chunk':
                _removeTyping();
                if (!activeBubble) {
                    activeBubble = _createAssistantBubble();
                }
                activeText += event.content;
                activeBubble.innerHTML = _renderMd(activeText);
                _scrollToBottom();
                break;

            case 'done':
                // Final clean render once the full text is in
                if (activeBubble && activeText) {
                    activeBubble.innerHTML = _renderMd(activeText);
                }
                activeBubble = null;
                activeText   = '';
                break;

            case 'error':
                _removeTyping();
                _appendErrorMessage(event.message || 'Error desconegut.');
                break;
        }
    }

    // ── DOM builders ──────────────────────────────────────────────────

    function _appendUserMessage(text) {
        const row = document.createElement('div');
        row.className = 'message message-user';
        row.innerHTML = `
            <div class="message-avatar"><i class="fas fa-user"></i></div>
            <div class="message-body">
                <div class="message-bubble">${_escHtml(text)}</div>
            </div>`;
        messagesEl.appendChild(row);
        _scrollToBottom();
    }

    function _appendTypingIndicator() {
        const el = document.createElement('div');
        el.className = 'typing-indicator';
        el.innerHTML = `<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>`;
        messagesEl.appendChild(el);
        _scrollToBottom();
        return el;
    }

    function _removeTyping() {
        if (typingEl) { typingEl.remove(); typingEl = null; }
    }

    function _createAssistantBubble() {
        const row = document.createElement('div');
        row.className = 'message message-assistant';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-mountain"></i>';

        const body = document.createElement('div');
        body.className = 'message-body';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        body.appendChild(bubble);

        row.appendChild(avatar);
        row.appendChild(body);
        messagesEl.appendChild(row);
        return bubble;
    }

    function _appendToolIndicator(toolName, done) {
        const el = document.createElement('div');
        el.className = 'tool-indicator' + (done ? ' tool-done' : '');
        el.dataset.tool = toolName;
        el.innerHTML = `<i class="fas fa-${done ? 'check-circle' : 'spinner fa-spin'}"></i> ${_toolLabel(toolName)}`;
        messagesEl.appendChild(el);
        _scrollToBottom();
    }

    function _markLastToolDone(toolName) {
        // Find the last indicator for this tool
        const indicators = [...messagesEl.querySelectorAll(`.tool-indicator[data-tool="${toolName}"]`)];
        const last = indicators[indicators.length - 1];
        if (last) {
            last.classList.add('tool-done');
            last.innerHTML = `<i class="fas fa-check-circle"></i> ${_toolLabel(toolName)}`;
        }
    }

    function _appendErrorMessage(msg) {
        const el = document.createElement('div');
        el.className = 'message message-assistant';
        el.innerHTML = `
            <div class="message-avatar" style="background:#ef4444"><i class="fas fa-exclamation"></i></div>
            <div class="message-body">
                <div class="message-bubble" style="border-color:#7f1d1d;color:#fca5a5">${_escHtml(msg)}</div>
            </div>`;
        messagesEl.appendChild(el);
        _scrollToBottom();
    }

    // ── Helpers ───────────────────────────────────────────────────────

    function _toolLabel(name) {
        const labels = {
            search_establishments:  'Cercant establiments…',
            search_destinations:    'Cercant destinacions…',
            search_articles:        'Cercant articles…',
            search_experiences:     'Cercant experiències…',
            search_events:          'Cercant events…',
            search_routes:          'Cercant rutes…',
            search_local_knowledge: 'Consultant informació local…',
        };
        return labels[name] || `Executant ${name}…`;
    }

    function _escHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function _scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function _setDisabled(disabled) {
        sendBtn.disabled  = disabled;
        inputEl.disabled  = disabled;
    }

    function _finish() {
        isStreaming = false;
        _setDisabled(false);
        _removeTyping();
        inputEl.focus();
    }

})();

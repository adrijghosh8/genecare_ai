const chatForm = document.querySelector('#chatForm');
const chatInput = document.querySelector('#chatInput');
const chatThread = document.querySelector('#chatThread');

function appendMessage(role, text) {
    const message = document.createElement('div');
    message.className = `message ${role === 'You' ? 'user-message' : 'assistant-message'}`;

    const label = document.createElement('span');
    label.textContent = role;

    const paragraph = document.createElement('p');
    paragraph.textContent = text;

    message.append(label, paragraph);
    chatThread.appendChild(message);
    chatThread.scrollTop = chatThread.scrollHeight;
}

function updateMiniHistory(title, createdAt) {
    const historyPanel = document.querySelector('.history-panel');
    if (!historyPanel) {
        return;
    }

    let miniHistory = historyPanel.querySelector('.mini-history');
    const emptyState = historyPanel.querySelector('.empty-state');

    if (!miniHistory) {
        miniHistory = document.createElement('div');
        miniHistory.className = 'mini-history';
        historyPanel.insertBefore(miniHistory, historyPanel.querySelector('.text-link'));
    }

    if (emptyState) {
        emptyState.remove();
    }

    const item = document.createElement('article');
    const time = document.createElement('span');
    const text = document.createElement('strong');

    time.textContent = createdAt;
    text.textContent = title;
    item.append(time, text);
    miniHistory.prepend(item);
}

if (chatForm) {
    chatThread.scrollTop = chatThread.scrollHeight;

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const message = chatInput.value.trim();
        if (!message) {
            return;
        }

        appendMessage('You', message);
        chatInput.value = '';
        chatInput.focus();

        const submitButton = chatForm.querySelector('button');
        submitButton.disabled = true;
        submitButton.textContent = 'Thinking...';

        try {
            const response = await fetch('/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unable to send message.');
            }

            appendMessage('AI Doctor', data.reply);
            updateMiniHistory(message, data.created_at);
        } catch (error) {
            appendMessage('AI Doctor', 'I could not send that message. Please try again.');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Send Message';
        }
    });
}

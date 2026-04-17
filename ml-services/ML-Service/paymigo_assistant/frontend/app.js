const API_BASE_URL = window.location.origin;

const messagesEl = document.getElementById('messages');
const formEl = document.getElementById('chatForm');
const inputEl = document.getElementById('chatInput');
const resetBtn = document.getElementById('resetBtn');

let history = [
  {
    role: 'migo',
    content: "Hi! I'm Migo 👋 I can help you with claims, plans, and payouts. What would you like to explore?",
  },
];

const renderMessages = () => {
  messagesEl.innerHTML = history.map((message) => {
    const messageClass = message.role === 'user' ? 'message user' : 'message migo';
    const actionsHtml = Array.isArray(message.actions) ? message.actions.map(action => `
      <button class="action-card" onclick="window.open('${action.target}', '_self')">${action.label} →</button>
    `).join('') : '';
    const suggestionsHtml = Array.isArray(message.suggestions) ? message.suggestions.map(suggestion => `
      <button class="suggestion-card" type="button" onclick="handleSuggestion('${suggestion.replace(/'/g, "\\'")}')">${suggestion}</button>
    `).join('') : '';

    return `
      <div class="${messageClass}">
        <div>${message.content}</div>
        ${actionsHtml ? `<div class="suggestion-row">${actionsHtml}</div>` : ''}
        ${suggestionsHtml ? `<div class="suggestion-row">${suggestionsHtml}</div>` : ''}
      </div>
    `;
  }).join('');
  messagesEl.scrollTop = messagesEl.scrollHeight;
};

const addTypingIndicator = () => {
  const typingNode = document.createElement('div');
  typingNode.className = 'message migo';
  typingNode.innerHTML = '<div style="display:flex;gap:8px"><span class="loading-dot"></span><span class="loading-dot"></span><span class="loading-dot"></span></div>';
  typingNode.id = 'typing-indicator';
  messagesEl.appendChild(typingNode);
  messagesEl.scrollTop = messagesEl.scrollHeight;
};

const removeTypingIndicator = () => {
  const node = document.getElementById('typing-indicator');
  if (node) node.remove();
};

const handleSuggestion = async (text) => {
  inputEl.value = text;
  await sendMessage(text);
};

const sendMessage = async (messageText) => {
  const userMessage = { role: 'user', content: messageText };
  history.push(userMessage);
  renderMessages();
  inputEl.value = '';
  addTypingIndicator();

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: messageText, history }),
    });

    if (!response.ok) {
      throw new Error('Server error');
    }

    const data = await response.json();

    removeTypingIndicator();

    history.push({
      role: 'migo',
      content: data.answer || 'I could not understand the response.',
      actions: data.actions || [],
      suggestions: data.suggestions || [],
    });

    renderMessages();
  } catch (error) {
    removeTypingIndicator();
    history.push({
      role: 'migo',
      content: 'Unable to connect. Please ensure the backend is running.',
    });
    renderMessages();
  }
};

formEl.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  await sendMessage(text);
});

resetBtn.addEventListener('click', () => {
  history = [
    {
      role: 'migo',
      content: "Hi! I'm Migo 👋 I can help you with claims, plans, and payouts. What would you like to explore?",
    },
  ];
  renderMessages();
});

window.handleSuggestion = handleSuggestion;
renderMessages();

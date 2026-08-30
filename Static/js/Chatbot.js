function toggleChat() {
  const chatbox = document.getElementById('chatbox');
  chatbox.style.display = chatbox.style.display === 'block' ? 'none' : 'block';
}

function handleKey(event) {
  if (event.key === 'Enter') {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (message) {
      addMessage('You', message);
      respondToMessage(message);
      input.value = '';
    }
  }
}

function addMessage(sender, text) {
  const chatlog = document.getElementById('chatlog');
  const entry = document.createElement('div');
  entry.innerHTML = `<strong>${sender}:</strong> ${text}`;
  chatlog.appendChild(entry);
  chatlog.scrollTop = chatlog.scrollHeight;
}

function respondToMessage(message) {
  fetch('/chatbot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message })
  })
  .then(response => response.json())
  .then(data => {
    setTimeout(() => {
      addMessage('BreatheBot', data.response);
    }, 500);
  })
  .catch(error => {
    console.error('Error:', error);
    addMessage('BreatheBot', "Oops! Something went wrong.");
  });
}

// Tooltip behavior for chatbot icon (hover)
function showTooltip() {
  const tooltip = document.getElementById('chatTooltip');
  if (tooltip) tooltip.style.display = 'block';
}

function hideTooltip() {
  const tooltip = document.getElementById('chatTooltip');
  if (tooltip) tooltip.style.display = 'none';
}

// Show tooltip once on page load (no popup)
window.addEventListener('DOMContentLoaded', function () {
  const tooltip = document.getElementById('chatTooltip');
  if (tooltip) {
    tooltip.style.display = 'block';
    setTimeout(() => {
      tooltip.style.display = 'none';
    }, 5000); // Show for 3 seconds
  }
});

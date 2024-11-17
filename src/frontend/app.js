// frontend/app.js

// Initialize SocketIO (optional for frontend feedback)
const socket = io();

// Event listeners for sending messages
document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (message === '') return;

    displayMessage('User', message);
    input.value = '';

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'prompt': message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            displayMessage('AI Agent', `Error: ${data.error}`);
        } else {
            const action = data.action;
            displayMessage('AI Agent', `Executed Action: ${action}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage('AI Agent', 'Error executing action.');
    });
}

function displayMessage(sender, message) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Listen for SocketIO events (optional, for real-time updates)
socket.on('action_executed', function(data) {
    const action = data.action;
    displayMessage('AI Agent', `Action Executed: ${action}`);
});

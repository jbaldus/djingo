// Global variables and functions that need to be accessed from anywhere
let gameActive = true;
let ws = null;

// Utility functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Game functions
async function clearBoard() {
    console.log('Starting clearBoard function'); // Debug log
    try {
        const board = document.getElementById('bingoBoard');
        if (!board) {
            console.error('Could not find bingoBoard element'); // Debug log
            return;
        }
        
        const playerId = board.dataset.playerId;
        console.log('Clearing board for player:', playerId); // Debug log

        const response = await fetch(`/api/game/${playerId}/clear/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        console.log('Server response status:', response.status); // Debug log

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Server response data:', data); // Debug log
        
        if (data.status === 'cleared') {
            // Reset all cells except free square
            const cells = document.querySelectorAll('.bingo-cell');
            cells.forEach(cell => {
                const position = parseInt(cell.dataset.position);
                if (!cell.classList.contains('free')) {
                    cell.classList.remove('covered');
                }
                cell.textContent = data.board_items[position]
            });
            
            // Close the winner modal
            const modal = document.getElementById('winnerModal');
            if (modal) {
                modal.style.display = 'none';
            }
            
            // Reset game state
            gameActive = true;
            console.log('Board cleared successfully'); // Debug log
        }
    } catch (error) {
        console.error('Error in clearBoard:', error);
        alert('Error clearing board. Check console for details.');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded'); // Debug log
    const board = document.getElementById('bingoBoard');
    const playerId = board.dataset.playerId;
    const cells = document.querySelectorAll('.bingo-cell');

    // Initialize cells
    cells.forEach(cell => {
        if (cell.dataset.covered === 'true') {
            cell.classList.add('covered');
        }
        if (cell.dataset.free === 'true') {
            cell.classList.add('free', 'covered');
        }
    });

    // Handle cell clicks
    board.addEventListener('click', async (e) => {
        if (!gameActive) return;
        
        const cell = e.target.closest('.bingo-cell');
        if (!cell) return;

        const position = parseInt(cell.dataset.position);
        
        try {
            const response = await fetch(`/api/game/${playerId}/mark/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ position })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            
            if (data.status === 'marked') {
                cell.classList.add('covered');
            } else if (data.status === 'already_marked') {
                cell.classList.remove('covered');
            } else if (data.status === 'win') {
                gameActive = false;
                showWinner(data.winner);
            }
        } catch (error) {
            console.error('Error marking position:', error);
        }
    });

    function showWinner(winner) {
        const modal = document.getElementById('winnerModal');
        const message = document.getElementById('winnerMessage');
        message.textContent = `${winner} has won the game!`;
        modal.style.display = 'flex';
        
        // Trigger confetti
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const baseReconnectDelay = 1000; // Start with 1 second delay
    let reconnectTimeout = null;

    function connectWebSocket() {
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/game/${playerId}/`;
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
            // Request initial game state
            ws.send(JSON.stringify({
                type: 'request_game_state'
            }));
            // Start ping interval
            startPingInterval();
        };

        ws.onclose = function(e) {
            console.log('WebSocket closed:', e.code, e.reason);
            clearPingInterval();
            
            // Don't attempt to reconnect if the game is over or the close was intentional
            if (e.code === 4004 || e.code === 4005 || !gameActive) {
                console.log('Not attempting to reconnect - game ended or invalid session');
                return;
            }

            handleReconnect();
        };

        ws.onerror = function(err) {
            console.error('WebSocket error:', err);
            ws.close();
        };

        ws.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            switch(data.type) {
                case 'winner':
                    gameActive = false;
                    showWinner(data.winner);
                    break;
                case 'game_state':
                    updateGameState(data.data);
                    break;
                case 'error':
                    console.error('Server error:', data.message);
                    break;
                case 'pong':
                    // Handle pong response
                    break;
            }
        };
    }

    function handleReconnect() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            showError('Connection lost. Please refresh the page.');
            return;
        }

        const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts);
        console.log(`Attempting to reconnect in ${delay}ms`);
        
        clearTimeout(reconnectTimeout);
        reconnectTimeout = setTimeout(() => {
            reconnectAttempts++;
            connectWebSocket();
        }, delay);
    }

    let pingInterval = null;
    function startPingInterval() {
        pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Send ping every 30 seconds
    }

    function clearPingInterval() {
        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }
    }

    function updateGameState(state) {
        if (!state) return;
        
        gameActive = state.is_active;
        
        // Update covered positions
        const cells = document.querySelectorAll('.bingo-cell');
        cells.forEach(cell => {
            const position = parseInt(cell.dataset.position);
            if (state.covered_positions.includes(position)) {
                cell.classList.add('covered');
            }
        });

        // Update connected players if we have that element
        const playerList = document.getElementById('connectedPlayers');
        if (playerList && state.connected_players) {
            playerList.innerHTML = state.connected_players
                .map(name => `<span class="player-badge">${name}</span>`)
                .join('');
        }

        // Handle winner state
        if (state.winner) {
            gameActive = false;
            showWinner(state.winner);
        }
        // Update events list
        if (state.recent_events) {
            const eventsList = document.getElementById('eventsList');
            if (eventsList) {
                eventsList.innerHTML = state.recent_events.map(event => `
                    <div class="event-item">
                        <span class="event-message">${event.message}</span>
                        <span class="event-time">${timeAgo(new Date(event.created_at))}</span>
                    </div>
                `).join('');
            }
        }
    }

    // Simple time ago function
    function timeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        
        return "just now";
    }

    function updateConnectedPlayers(players) {
        const playerList = document.getElementById('connectedPlayers');
        if (playerList) {
            playerList.innerHTML = players.map(name => 
                `<span class="player-badge">${name}</span>`
            ).join('');
        }
    }

    function showError(message) {
        // Add error message display logic here
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    // Initialize WebSocket connection
    connectWebSocket();

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (ws) {
            ws.close();
        }
        clearPingInterval();
        clearTimeout(reconnectTimeout);
    });
});


// For debugging in console
window.debugGame = {
    clearBoard,
    gameActive,
    checkState: () => {
        console.log('Game State:', {
            gameActive,
            boardElement: document.getElementById('bingoBoard'),
            wsState: ws?.readyState,
            coveredCells: document.querySelectorAll('.bingo-cell.covered').length
        });
    }
};

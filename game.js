// Game configuration
const config = {
  rows: 4,            // Number of dot rows (m)
  cols: 6,            // Number of dot columns (n)
  dotRadius: 7,       // Radius of each dot in pixels
  cellSize: 90,       // Size of each cell in pixels
  lineWidth: 8,       // Width of lines between dots
  gridPaddingTop: 30, // Top padding for the grid
  margin: 20,         // Margin around the grid
  colors: {
    dot: '#2c3e50',   // Color of the dots
    line: '#7f8c8d',  // Color of unclaimed lines
    background: '#ffffff',
    text: '#2c3e50',
    // Player colors (matching the CSS variables)
    players: ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#9b59b6']
  }
};

// Game state
let state = {
  players: ['A', 'B'],
  currentPlayer: 0,
  scores: {},
  edges: new Set(),          // Set of all drawn edges (as strings "r1,c1:r2,c2")
  boxes: new Map(),          // Map of box top-left coordinates to owner (player index or null)
  highlightedEdge: null,     // Currently highlighted edge (for hover effect)
  gameOver: false,
  canvas: null,
  ctx: null,
  canvasSize: { width: 0, height: 0 },
  boardOffset: { x: 0, y: 0 }
};

// Initialize the game
function initGame() {
  // Get canvas and context
  state.canvas = document.getElementById('gameCanvas');
  state.ctx = state.canvas.getContext('2d');
  
  // Initialize scores
  state.players.forEach((_, i) => {
    state.scores[i] = 0;
  });
  
  // Set up the game board
  setupCanvas();
  
  // Set up event listeners
  setupEventListeners();
  
  // Initial render
  drawBoard();
  updateUI();
}

// Set up the canvas size and positioning
function setupCanvas() {
  // Calculate canvas size based on grid dimensions
  const width = config.cols * config.cellSize + config.margin * 2;
  const height = config.rows * config.cellSize + config.margin * 2 + config.gridPaddingTop;
  
  // Set canvas size
  state.canvas.width = width;
  state.canvas.height = height;
  state.canvasSize = { width, height };
  
  // Calculate board offset to center the grid
  state.boardOffset = {
    x: config.margin,
    y: config.margin + config.gridPaddingTop
  };
}

// Set up event listeners
function setupEventListeners() {
  // Canvas click handler
  state.canvas.addEventListener('click', handleCanvasClick);
  
  // Canvas mouse move handler for hover effect
  state.canvas.addEventListener('mousemove', handleMouseMove);
  
  // Restart button
  document.getElementById('restart-btn').addEventListener('click', resetGame);
  
  // Play again button in game over modal
  document.getElementById('play-again').addEventListener('click', resetGame);
  
  // Handle window resize
  window.addEventListener('resize', () => {
    setupCanvas();
    drawBoard();
  });
}

// Handle canvas click
function handleCanvasClick(event) {
  if (state.gameOver) return;
  
  const rect = state.canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  
  // Find the nearest edge to the click
  const edge = findNearestEdge(x, y);
  if (edge) {
    // Check if the edge is already taken
    const edgeKey = `${edge.r1},${edge.c1}:${edge.r2},${edge.c2}`;
    if (!state.edges.has(edgeKey)) {
      // Add the edge
      state.edges.add(edgeKey);
      
      // Check for completed boxes
      const completedBoxes = checkForCompletedBoxes(edge);
      
      if (completedBoxes.length === 0) {
        // No boxes completed, switch player
        state.currentPlayer = (state.currentPlayer + 1) % state.players.length;
      } else {
        // Update scores for completed boxes
        completedBoxes.forEach(box => {
          state.boxes.set(`${box.r},${box.c}`, state.currentPlayer);
          state.scores[state.currentPlayer]++;
        });
        
        // Check for game over
        if (isGameOver()) {
          endGame();
          return;
        }
      }
      
      // Update the UI
      drawBoard();
      updateUI();
    }
  }
}

// Handle mouse move for hover effect
function handleMouseMove(event) {
  if (state.gameOver) return;
  
  const rect = state.canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  
  // Find the nearest edge
  const edge = findNearestEdge(x, y);
  
  // Update highlighted edge if it's not already taken
  if (edge) {
    const edgeKey = `${edge.r1},${edge.c1}:${edge.r2},${edge.c2}`;
    if (!state.edges.has(edgeKey)) {
      state.highlightedEdge = edge;
    } else {
      state.highlightedEdge = null;
    }
  } else {
    state.highlightedEdge = null;
  }
  
  // Redraw the board to show the hover effect
  drawBoard();
}

// Find the nearest edge to the given coordinates
function findNearestEdge(x, y) {
  // Convert screen coordinates to grid coordinates
  const gridX = Math.round((x - state.boardOffset.x) / config.cellSize);
  const gridY = Math.round((y - state.boardOffset.y) / config.cellSize);
  
  // Check if the click is near a horizontal or vertical line between dots
  const cellX = Math.floor((x - state.boardOffset.x + config.cellSize / 2) / config.cellSize);
  const cellY = Math.floor((y - state.boardOffset.y + config.cellSize / 2) / config.cellSize);
  
  // Check if the click is near a horizontal line
  if (Math.abs(y - (state.boardOffset.y + gridY * config.cellSize)) < 15 && 
      gridX >= 0 && gridX < config.cols - 1 && 
      gridY >= 0 && gridY < config.rows) {
    return {
      r1: gridY,
      c1: gridX,
      r2: gridY,
      c2: gridX + 1,
      isHorizontal: true
    };
  }
  
  // Check if the click is near a vertical line
  if (Math.abs(x - (state.boardOffset.x + gridX * config.cellSize)) < 15 && 
      gridY >= 0 && gridY < config.rows - 1 && 
      gridX >= 0 && gridX < config.cols) {
    return {
      r1: gridY,
      c1: gridX,
      r2: gridY + 1,
      c2: gridX,
      isHorizontal: false
    };
  }
  
  return null;
}

// Check if drawing an edge completes any boxes
function checkForCompletedBoxes(edge) {
  const completedBoxes = [];
  
  // Check the two potential boxes that could be completed by this edge
  if (edge.isHorizontal) {
    // Check box above the horizontal line
    if (edge.r1 > 0) {
      const topEdge = `${edge.r1-1},${edge.c1}:${edge.r1-1},${edge.c2}`;
      const leftEdge = `${edge.r1-1},${edge.c1}:${edge.r1},${edge.c1}`;
      const rightEdge = `${edge.r1-1},${edge.c2}:${edge.r1},${edge.c2}`;
      
      if (state.edges.has(topEdge) && state.edges.has(leftEdge) && state.edges.has(rightEdge)) {
        completedBoxes.push({ r: edge.r1 - 1, c: edge.c1 });
      }
    }
    
    // Check box below the horizontal line
    if (edge.r1 < config.rows - 1) {
      const bottomEdge = `${edge.r1+1},${edge.c1}:${edge.r1+1},${edge.c2}`;
      const leftEdge = `${edge.r1},${edge.c1}:${edge.r1+1},${edge.c1}`;
      const rightEdge = `${edge.r1},${edge.c2}:${edge.r1+1},${edge.c2}`;
      
      if (state.edges.has(bottomEdge) && state.edges.has(leftEdge) && state.edges.has(rightEdge)) {
        completedBoxes.push({ r: edge.r1, c: edge.c1 });
      }
    }
  } else {
    // Check box to the left of the vertical line
    if (edge.c1 > 0) {
      const leftEdge = `${edge.r1},${edge.c1-1}:${edge.r2},${edge.c1-1}`;
      const topEdge = `${edge.r1},${edge.c1-1}:${edge.r1},${edge.c1}`;
      const bottomEdge = `${edge.r2},${edge.c1-1}:${edge.r2},${edge.c1}`;
      
      if (state.edges.has(leftEdge) && state.edges.has(topEdge) && state.edges.has(bottomEdge)) {
        completedBoxes.push({ r: edge.r1, c: edge.c1 - 1 });
      }
    }
    
    // Check box to the right of the vertical line
    if (edge.c1 < config.cols - 1) {
      const rightEdge = `${edge.r1},${edge.c1+1}:${edge.r2},${edge.c1+1}`;
      const topEdge = `${edge.r1},${edge.c1}:${edge.r1},${edge.c1+1}`;
      const bottomEdge = `${edge.r2},${edge.c1}:${edge.r2},${edge.c1+1}`;
      
      if (state.edges.has(rightEdge) && state.edges.has(topEdge) && state.edges.has(bottomEdge)) {
        completedBoxes.push({ r: edge.r1, c: edge.c1 });
      }
    }
  }
  
  return completedBoxes;
}

// Check if the game is over (all possible edges are drawn)
function isGameOver() {
  const totalPossibleEdges = (config.rows - 1) * config.cols + config.rows * (config.cols - 1);
  return state.edges.size >= totalPossibleEdges;
}

// End the game and show the winner
function endGame() {
  state.gameOver = true;
  
  // Find the winner
  let maxScore = -1;
  let winner = -1;
  let isTie = false;
  
  state.players.forEach((_, i) => {
    if (state.scores[i] > maxScore) {
      maxScore = state.scores[i];
      winner = i;
      isTie = false;
    } else if (state.scores[i] === maxScore) {
      isTie = true;
    }
  });
  
  // Update the game over modal
  const winnerText = document.getElementById('winner-text');
  if (isTie) {
    winnerText.textContent = "It's a tie!";
  } else {
    winnerText.textContent = `Player ${state.players[winner]} wins with ${maxScore} points!`;
  }
  
  // Show the modal
  document.getElementById('game-over').style.display = 'flex';
}

// Draw the game board
function drawBoard() {
  const ctx = state.ctx;
  
  // Clear the canvas
  ctx.clearRect(0, 0, state.canvas.width, state.canvas.height);
  
  // Draw the background
  ctx.fillStyle = config.colors.background;
  ctx.fillRect(0, 0, state.canvas.width, state.canvas.height);
  
  // Draw completed boxes with player colors
  state.boxes.forEach((playerIdx, boxKey) => {
    const [r, c] = boxKey.split(',').map(Number);
    const x = state.boardOffset.x + c * config.cellSize;
    const y = state.boardOffset.y + r * config.cellSize;
    
    ctx.fillStyle = config.colors.players[playerIdx % config.colors.players.length] + '40'; // 40 = 25% opacity
    ctx.fillRect(x, y, config.cellSize, config.cellSize);
  });
  
  // Draw the grid lines
  ctx.strokeStyle = config.colors.line;
  ctx.lineWidth = config.lineWidth;
  ctx.lineCap = 'round';
  
  // Draw horizontal lines
  for (let r = 0; r < config.rows; r++) {
    for (let c = 0; c < config.cols - 1; c++) {
      const x1 = state.boardOffset.x + c * config.cellSize;
      const x2 = x1 + config.cellSize;
      const y = state.boardOffset.y + r * config.cellSize;
      
      // Check if this edge is drawn
      const edgeKey = `${r},${c}:${r},${c+1}`;
      const isDrawn = state.edges.has(edgeKey);
      
      // Check if this is the highlighted edge
      const isHighlighted = state.highlightedEdge && 
                           state.highlightedEdge.r1 === r && 
                           state.highlightedEdge.c1 === c &&
                           state.highlightedEdge.r2 === r && 
                           state.highlightedEdge.c2 === c + 1;
      
      if (isDrawn) {
        // Find which edges form a box to determine the player color
        let playerColor = config.colors.line;
        
        // Check the boxes on either side of this edge
        if (r > 0) {
          const boxKey = `${r-1},${c}`;
          if (state.boxes.has(boxKey)) {
            playerColor = config.colors.players[state.boxes.get(boxKey) % config.colors.players.length];
          }
        }
        if (r < config.rows - 1) {
          const boxKey = `${r},${c}`;
          if (state.boxes.has(boxKey)) {
            playerColor = config.colors.players[state.boxes.get(boxKey) % config.colors.players.length];
          }
        }
        
        ctx.strokeStyle = playerColor;
        ctx.lineWidth = config.lineWidth;
      } else if (isHighlighted) {
        ctx.strokeStyle = config.colors.players[state.currentPlayer % config.colors.players.length] + '80'; // 80 = 50% opacity
        ctx.lineWidth = config.lineWidth * 1.5;
      } else {
        ctx.strokeStyle = config.colors.line + '40'; // 40 = 25% opacity
        ctx.lineWidth = config.lineWidth * 0.7;
      }
      
      ctx.beginPath();
      ctx.moveTo(x1, y);
      ctx.lineTo(x2, y);
      ctx.stroke();
    }
  }
  
  // Draw vertical lines
  for (let r = 0; r < config.rows - 1; r++) {
    for (let c = 0; c < config.cols; c++) {
      const y1 = state.boardOffset.y + r * config.cellSize;
      const y2 = y1 + config.cellSize;
      const x = state.boardOffset.x + c * config.cellSize;
      
      // Check if this edge is drawn
      const edgeKey = `${r},${c}:${r+1},${c}`;
      const isDrawn = state.edges.has(edgeKey);
      
      // Check if this is the highlighted edge
      const isHighlighted = state.highlightedEdge && 
                           state.highlightedEdge.r1 === r && 
                           state.highlightedEdge.c1 === c &&
                           state.highlightedEdge.r2 === r + 1 && 
                           state.highlightedEdge.c2 === c;
      
      if (isDrawn) {
        // Find which edges form a box to determine the player color
        let playerColor = config.colors.line;
        
        // Check the boxes on either side of this edge
        if (c > 0) {
          const boxKey = `${r},${c-1}`;
          if (state.boxes.has(boxKey)) {
            playerColor = config.colors.players[state.boxes.get(boxKey) % config.colors.players.length];
          }
        }
        if (c < config.cols - 1) {
          const boxKey = `${r},${c}`;
          if (state.boxes.has(boxKey)) {
            playerColor = config.colors.players[state.boxes.get(boxKey) % config.colors.players.length];
          }
        }
        
        ctx.strokeStyle = playerColor;
        ctx.lineWidth = config.lineWidth;
      } else if (isHighlighted) {
        ctx.strokeStyle = config.colors.players[state.currentPlayer % config.colors.players.length] + '80'; // 80 = 50% opacity
        ctx.lineWidth = config.lineWidth * 1.5;
      } else {
        ctx.strokeStyle = config.colors.line + '40'; // 40 = 25% opacity
        ctx.lineWidth = config.lineWidth * 0.7;
      }
      
      ctx.beginPath();
      ctx.moveTo(x, y1);
      ctx.lineTo(x, y2);
      ctx.stroke();
    }
  }
  
  // Draw the dots
  ctx.fillStyle = config.colors.dot;
  for (let r = 0; r < config.rows; r++) {
    for (let c = 0; c < config.cols; c++) {
      const x = state.boardOffset.x + c * config.cellSize;
      const y = state.boardOffset.y + r * config.cellSize;
      
      ctx.beginPath();
      ctx.arc(x, y, config.dotRadius, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  
  // Draw player indicators in the center of each box
  state.boxes.forEach((playerIdx, boxKey) => {
    const [r, c] = boxKey.split(',').map(Number);
    const x = state.boardOffset.x + c * config.cellSize + config.cellSize / 2;
    const y = state.boardOffset.y + r * config.cellSize + config.cellSize / 2;
    
    ctx.fillStyle = config.colors.players[playerIdx % config.colors.players.length];
    ctx.font = `bold ${config.cellSize * 0.6}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(state.players[playerIdx], x, y);
  });
}

// Update the UI elements
function updateUI() {
  // Update scores
  state.players.forEach((player, i) => {
    const scoreElement = document.getElementById(`score-${player.toLowerCase()}`);
    if (scoreElement) {
      scoreElement.textContent = `${player}: ${state.scores[i]}`;
      
      // Highlight the current player
      if (i === state.currentPlayer && !state.gameOver) {
        scoreElement.classList.add('active');
      } else {
        scoreElement.classList.remove('active');
      }
    }
  });
  
  // Update current player display
  const currentPlayerElement = document.getElementById('current-player');
  if (currentPlayerElement) {
    currentPlayerElement.textContent = state.players[state.currentPlayer];
    currentPlayerElement.className = `player-${state.currentPlayer}`;
  }
}

// Reset the game
function resetGame() {
  // Reset game state
  state.edges.clear();
  state.boxes.clear();
  state.currentPlayer = 0;
  state.gameOver = false;
  state.highlightedEdge = null;
  
  // Reset scores
  state.players.forEach((_, i) => {
    state.scores[i] = 0;
  });
  
  // Hide game over modal
  document.getElementById('game-over').style.display = 'none';
  
  // Redraw the board and update UI
  drawBoard();
  updateUI();
}

// Initialize the game when the page loads
window.addEventListener('DOMContentLoaded', initGame);

// Add keyboard shortcuts
document.addEventListener('keydown', (event) => {
  // R key to restart
  if (event.key === 'r' || event.key === 'R') {
    resetGame();
  }
});

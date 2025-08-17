# Dots & Boxes

A web-based implementation of the classic Dots & Boxes game, built with HTML5 Canvas and JavaScript.

## How to Play

1. **Objective**: Complete more boxes than your opponent by connecting dots to form lines and closing boxes.
2. **Gameplay**: 
   - Players take turns drawing a single horizontal or vertical line between two adjacent dots.
   - When a player completes the fourth side of a box, they claim that box and get another turn.
   - The game ends when all possible lines have been drawn.
   - The player with the most boxes wins!

## Controls

- **Mouse**: Click between two dots to draw a line
- **R Key**: Restart the game at any time

## Features

- Clean, responsive UI that works on desktop and mobile
- Hover effects to preview moves
- Score tracking for up to 5 players
- Smooth animations and visual feedback
- Keyboard shortcuts for better accessibility

## Deployment

This game is designed to be deployed to GitHub Pages. To deploy:

1. Make sure your repository is pushed to GitHub
2. Run the deployment script:
   ```bash
   chmod +x deploy-page-git.sh
   ./deploy-page-git.sh
   ```
3. The game will be available at `https://<your-username>.github.io/<repository-name>/`

## Development

To run locally, simply open `index.html` in a modern web browser. No build step is required.

## Customization

You can customize the game by editing `game.js`:

- Change the number of rows and columns in the `config` object
- Modify colors and styling in `style.css`
- Add more players by updating the `players` array in the game state

## License

MIT License - feel free to use this code for your own projects!

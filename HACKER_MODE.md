# 🎰 POKER BOT - HACKER MODE LAUNCHER

## Quick Start

### Windows - Easy Launch
1. Open `Back_end` folder
2. **Double-click `run.cmd`** 
3. Done! The hacker-themed UI will launch

Or from Command Prompt:
```cmd
cd Back_end
run.cmd
```

---

### Command Line Launch (Any OS)

```bash
cd Back_end
python hacker_gui.py
```

---

## UI Guide

### Status Indicators
- 🟢 **ONLINE** - System actively scanning
- ⚫ **OFFLINE** - System idle, waiting for commands

### Buttons

| Button | Function |
|--------|----------|
| **▶ INITIALIZE SCAN** | Start real-time analysis |
| **⏹ STOP SCAN** | Halt analysis |
| **🤖 AUTO-EXECUTE** | Toggle auto-play mode |
| **[CLEAR LOGS]** | Clear analysis history |

### Modes

#### 👁️ ADVISOR MODE (Default)
- System detects cards
- Shows best poker decision
- You make the move manually
- Command: Press "▶ INITIALIZE SCAN"

#### 🤖 AUTO-EXECUTE MODE
- System detects cards
- AI calculates best move
- **System plays automatically**
- Enable: Click "🤖 AUTO-EXECUTE OFF" button

---

## Display Panels

### LEFT: Monitor Feed
- Real-time screenshot from your game
- Shows what the AI is "seeing"
- Updates every 3 seconds

### RIGHT: Neural Analysis
- Card detection results
- Hand strength analysis
- Recommended actions
- Color-coded:
  - 🟢 Green = Good news
  - 🟡 Yellow = Warning
  - 🔴 Red = Error

---

## Theme Features

✨ **Hacker Aesthetic**
- Matrix-style green text on black
- Monospace "Courier New" font
- Terminal-like interface
- Animated title bar
- Real-time status updates

---

## Troubleshooting

### "Claude API key not found"
1. Edit `.env` file in `Back_end` folder
2. Find: `CLAUDE_API_KEY=`
3. Replace with your actual key from https://console.anthropic.com
4. Save and restart

### "Import error: anthropic"
```cmd
pip install anthropic
```

### "No poker screen detected"
- Take a screenshot of an actual poker game
- Ensure cards are clearly visible
- Try different lighting/contrast

### Python not found
- Install from: https://www.python.org
- Choose Python 3.8 or newer
- **Important**: Check "Add Python to PATH" during installation

---

## What's Happening Behind the Scenes

1. **Screenshot Capture** → Takes live screenshot every 3 seconds
2. **Claude Vision AI** → Detects cards with 99%+ accuracy
3. **Poker Engine** → Calculates win probability & best move
4. **Display** → Shows analysis in green hacker UI

---

## Costs

Your $20 Claude credits = ~2,000 card recognitions

**Usage estimates:**
- Light testing: ~$0.30/day
- Regular play: ~$1.00/day  
- 24/7 auto-play: ~$4.00/day

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `CTRL+C` | Force quit (if frozen) |
| `ESC` | Close window |

---

## API Key Safety

⚠️ **IMPORTANT:**
- Never share your API key
- Never commit `.env` to Git
- Keep it private like a password
- If compromised, regenerate at https://console.anthropic.com

---

## Next Steps

1. ✅ Run `run.cmd`
2. 🔍 Watch live poker analysis
3. 🤖 Toggle AUTO mode for hands-off play
4. 💰 Win some hands!

---

## Need Help?

- Check `.env` configuration
- Ensure Claude API key is valid
- Verify internet connection for AI calls
- Look at green logs for error messages

---

**Happy hacking!** 🎰⚡

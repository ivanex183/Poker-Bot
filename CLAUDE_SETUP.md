# Claude Vision AI Card Recognition Setup Guide

## Overview
Your poker bot now uses **Claude Vision API** for intelligent card recognition. This replaces/supplements YOLO detection with state-of-the-art AI.

### Detection Hierarchy
1. **Claude Vision** (primary) - Best accuracy, understands context
2. **YOLO** (fallback) - Fast local processing, no API calls

---

## Setup Steps

### 1. Get Claude API Key
1. Go to [Anthropic Console](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy your API key

### 2. Add to .env
Update your `.env` file:
```
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
ANALYSIS_INTERVAL=3
```

### 3. Install Dependencies
Run in your Back_end directory:
```bash
pip install anthropic==0.28.0
```

---

## Usage

### Auto Mode (Hands-off)
```python
from auto_analyzer import AutomaticPokerAnalyzer
from screenshot_analyzer import PokerTableAnalyzer

analyzer = AutomaticPokerAnalyzer()

# This will use Claude Vision for card detection
for poker_data in analyzer.run_continuous_analysis():
    print(f"Detected: {poker_data['detected_cards']}")
    print(f"Method: {poker_data['method']}")
    print(f"Confidence: {poker_data['confidence']}")
```

### Assistant Mode (Recommendations Only)
```python
from integration import PokerBotIntegration
from screenshot_analyzer import PokerTableAnalyzer

# Claude detects cards, you provide other game state
bot = PokerBotIntegration()

for poker_data in bot.analyzer.run_continuous_analysis():
    # System detects cards with Claude Vision
    print(f"Cards detected: {poker_data}")
```

### Manual Card Recognition Testing
```python
from PIL import Image
from claude_card_recognizer import ClaudeCardRecognizer

recognizer = ClaudeCardRecognizer()

# Test on a screenshot
image = Image.open('poker_screenshot.png')
hole_cards, community_cards, notes = recognizer.recognize_cards(image, verbose=True)

print(f"Your cards: {hole_cards}")
print(f"Community: {community_cards}")
print(f"Analysis: {notes}")
```

---

## What Claude Detects

✅ **Hole cards** (your 2 cards)
✅ **Community cards** (flop, turn, river)
✅ **Card ranks** (A, K, Q, J, 10, 2-9)
✅ **Card suits** (♠ ♥ ♦ ♣)
✅ **Screen validation** (confirms it's a poker screenshot)

---

## How It Works

### Claude Vision Flow
1. You take a screenshot with `mss` (existing code)
2. Screenshot is sent to Claude Vision API (encoded as base64)
3. Claude analyzes and returns:
   - Hole cards you're holding
   - Community cards on the table
   - Confidence assessment
   - Notes on card visibility/clarity

### Response Format
```
CARDS: [A-♠, K-♥]
COMMUNITY: [Q-♣, J-♦, 10-♠]
NOTES: Clear visibility, high contrast, standard poker layout
```

---

## Fallback Strategy

If Claude Vision fails for any reason:
- **Reason**: API timeout, no internet, API error
- **Fallback**: Automatically uses YOLO local detection
- **User sees**: No interruption, system continues analyzing

Example output:
```
[AUTO_ANALYZER] Claude detection failed: Connection timeout
[AUTO_ANALYZER] Falling back to YOLO...
```

---

## Pricing & Costs

Claude Vision pricing (as of April 2026):
- **Input**: $0.003 per 1K tokens (~0.3¢ per image)
- **Output**: $0.015 per 1K tokens

**Estimate**: ~$0.01-0.02 per card recognition call

For continuous play:
- 1 hand per 10 seconds = 6 hands/min = ~$0.06-0.12/hour
- 8-hour session = ~$0.50-1.00

---

## Environment Setup Summary

### .env file should have:
```
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
ANALYSIS_INTERVAL=3
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### requirements.txt includes:
```
anthropic==0.28.0
easyocr==1.7.2
Pillow==11.0.0
python-dotenv==1.0.0
mss==7.0.1
```

---

## Troubleshooting

### "CLAUDE_API_KEY not found"
- Check `.env` file exists in Back_end folder
- Run: `pip install python-dotenv`
- Restart Python interpreter

### "anthropic module not found"
```bash
pip install anthropic==0.28.0
```

### Claude returns "NONE" for cards
- Screenshot may not be a poker table
- Cards might be obscured/blurry
- Try YOLO with verbose mode:
```python
analyzer.card_detector.detect_cards(image, verbose=True)
```

### Too slow / API timeout
- Claude typical response: 2-5 seconds
- Can be slower if: poor internet, many cards visible, complex table layout
- YOLO fallback is instant (runs locally)

---

## Integration with Existing Poker Engine

Your existing poker engine code is **untouched**:

```python
from poker_engine import analyze_situation, win_probability

# Claude detects cards → passes to your poker engine
hole_cards = [('A', '♠'), ('K', '♥')]  # from Claude
community = [('Q', '♣'), ('J', '♦'), ('10', '♠')]

# Your engine handles the rest
probs = win_probability(hole_cards, community, num_opponents=2)
print(probs)  # {'win': 0.75, 'tie': 0.05, 'lose': 0.20}
```

---

## Next Steps

1. **Add API key** to `.env`
2. **Install anthropic**: `pip install anthropic==0.28.0`
3. **Test**: Run `python claude_card_recognizer.py`
4. **Deploy**: Switch on auto mode with `gui.py`

Your bot is now AI-powered! 🤖♠️

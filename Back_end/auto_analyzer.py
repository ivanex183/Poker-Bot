"""
Fully Automatic Poker Bot
Takes screenshots, extracts poker data with AI, and provides recommendations
Uses Claude Vision AI for card recognition
"""

from screenshot_analyzer import PokerTableAnalyzer
from poker_engine import analyze_situation
import re
import time

# Try to import Claude card recognizer
try:
    from claude_card_recognizer import ClaudeCardRecognizer
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False
    print("[AUTO_ANALYZER] Claude card recognizer not available")

# Try to import YOLO card detector as fallback
try:
    from card_detector import CardDetector
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("[AUTO_ANALYZER] YOLO card detector not available")

from PIL import Image

# Site-specific detector for the 247 Free Poker table.
try:
    from site_247freepoker_detector import Site247FreePokerDetector
    HAS_247_FREE_POKER = True
except ImportError:
    HAS_247_FREE_POKER = False
    print("[AUTO_ANALYZER] 247 Free Poker detector not available")

class AutomaticPokerAnalyzer:
    def __init__(self):
        self.analyzer = PokerTableAnalyzer()
        self.last_analysis = None
        self.site_247_detector = Site247FreePokerDetector() if HAS_247_FREE_POKER else None
        
        # Initialize Claude card recognizer (primary method)
        if HAS_CLAUDE:
            try:
                self.claude_recognizer = ClaudeCardRecognizer()
                print("[AUTO_ANALYZER] Claude Vision card recognizer initialized")
            except ValueError as e:
                print(f"[AUTO_ANALYZER] Claude initialization failed: {e}")
                self.claude_recognizer = None
        else:
            self.claude_recognizer = None
        
        # Initialize YOLO card detector as fallback
        if HAS_YOLO:
            self.card_detector = CardDetector()
            print("[AUTO_ANALYZER] YOLO card detector initialized (fallback)")
        else:
            self.card_detector = None
    
    def extract_poker_info_from_image(self, image: Image.Image, vision_data=None):
        """
        Extract poker info from image.

        For 247 Free Poker, use a local layout detector first. If that does not
        find two hole cards, fall back to Claude Vision and then YOLO.
        
        Args:
            image: PIL Image object
            vision_data: optional OCR output from PokerTableAnalyzer
            
        Returns:
            dict with detected_cards, community_cards, etc.
        """
        # Site-specific detection for the screen shown in the user's example.
        if self.site_247_detector:
            try:
                site_result = self.site_247_detector.analyze(image, vision_data=vision_data)
                if site_result.get('is_poker_screen') and len(site_result.get('detected_cards', [])) >= 2:
                    return site_result
            except Exception as e:
                print(f"[AUTO_ANALYZER] 247 Free Poker detection failed: {e}")

        # Try Claude Vision first (primary method)
        if self.claude_recognizer:
            try:
                hole_cards, community_cards, notes = self.claude_recognizer.recognize_cards(image, verbose=False)
                # Try to extract numeric game state (pot, call, opponents, stack)
                try:
                    game_state = self.claude_recognizer.extract_game_state(image, verbose=False)
                except Exception:
                    game_state = {'pot_size': None, 'call_amount': None, 'num_opponents': None, 'stack_size': None}

                return {
                    'detected_cards': self._normalize_cards(hole_cards),
                    'detected_community': self._normalize_cards(community_cards),
                    'is_poker_screen': len(hole_cards) > 0,
                    'method': 'Claude Vision',
                    'confidence': 'high',
                    'analysis_notes': notes,
                    'game_state': self._normalize_game_state(game_state)
                }
            except Exception as e:
                print(f"[AUTO_ANALYZER] Claude detection failed: {e}")
                print("[AUTO_ANALYZER] Falling back to YOLO...")
        
        # Fallback to YOLO if Claude not available or failed
        if self.card_detector:
            try:
                hole_cards = self.card_detector.detect_cards(image, verbose=False)
                community = self.card_detector.detect_community_cards(image)
                
                return {
                    'detected_cards': self._normalize_cards(hole_cards),
                    'detected_community': self._normalize_cards(community),
                    'is_poker_screen': len(hole_cards) > 0,
                    'method': 'YOLO',
                    'confidence': 'medium',
                    'game_state': {}
                }
            except Exception as e:
                print(f"[AUTO_ANALYZER] YOLO detection failed: {e}")
        
        # No detection method available
        return {
            'detected_cards': [], 
            'detected_community': [], 
            'is_poker_screen': False,
            'method': 'None',
            'error': 'No card detection method available'
        }

    def _normalize_cards(self, cards):
        """Convert cards from detector output into poker_engine tuples."""
        normalized = []
        suit_map = {
            'S': '♠', 'SPADE': '♠', 'SPADES': '♠', '♠': '♠',
            'H': '♥', 'HEART': '♥', 'HEARTS': '♥', '♥': '♥',
            'D': '♦', 'DIAMOND': '♦', 'DIAMONDS': '♦', '♦': '♦',
            'C': '♣', 'CLUB': '♣', 'CLUBS': '♣', '♣': '♣',
        }

        for card in cards or []:
            rank = None
            suit = None

            if isinstance(card, tuple) and len(card) >= 2:
                rank = str(card[0]).upper()
                suit = str(card[1]).upper()
            elif isinstance(card, str):
                text = card.upper().strip()
                match = re.match(r'(10|[2-9JQKA])\s*([SHDC♠♥♦♣]?)', text)
                if match:
                    rank = match.group(1)
                    suit = match.group(2) or None

            if not rank:
                continue

            suit = suit_map.get(suit, suit) if suit else None
            if suit is None or suit not in ['♠', '♥', '♦', '♣']:
                suit = self._next_available_suit(normalized)

            normalized.append((rank, suit))

        return normalized

    def _next_available_suit(self, cards):
        used = {suit for _, suit in cards}
        for suit in ['♠', '♥', '♦', '♣']:
            if suit not in used:
                return suit
        return '♠'

    def _money_to_number(self, value, default=None):
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return value

        match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', str(value))
        if not match:
            return default
        try:
            number = float(match.group(1).replace(',', ''))
            return int(number) if number.is_integer() else number
        except ValueError:
            return default

    def _normalize_game_state(self, game_state):
        game_state = game_state or {}
        return {
            'pot_size': self._money_to_number(game_state.get('pot_size') or game_state.get('pot')),
            'call_amount': self._money_to_number(game_state.get('call_amount') or game_state.get('call'), 0),
            'num_opponents': self._money_to_number(game_state.get('num_opponents'), None),
            'stack_size': self._money_to_number(game_state.get('stack_size') or game_state.get('stack')),
        }

    def _format_cards(self, cards):
        suit_letters = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
        formatted = []
        for card in cards or []:
            if isinstance(card, tuple) and len(card) >= 2:
                formatted.append(f"{card[0]}{suit_letters.get(card[1], card[1])}")
            else:
                formatted.append(str(card))
        return "[" + ", ".join(formatted) + "]"
    
    def extract_poker_info_from_text(self, text):
        """
        Intelligent extraction of poker data from OCR text.
        Returns dict with extracted information.
        """
        text_upper = text.upper()
        
        # Try to find cards (patterns like "AK", "QQ", "As Kh")
        cards_data = self._extract_cards_from_text(text)
        
        # Try to find numbers for pot, stack, call amount
        numbers = re.findall(r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b', text_upper)
        numbers_clean = [float(n.replace(',', '')) for n in numbers]
        
        # Look for poker keywords
        has_poker_keywords = any(kw in text_upper for kw in 
            ['FOLD', 'CALL', 'RAISE', 'CHECK', 'BET', 'ALL IN', 'POT', 'FLOP', 'TURN', 'RIVER', 'PREFLOP'])
        
        return {
            'detected_cards': cards_data.get('hole_cards', []),
            'detected_community': cards_data.get('community_cards', []),
            'extracted_numbers': numbers_clean,
            'is_poker_screen': has_poker_keywords,
            'raw_text': text
        }
    
    def _extract_cards_from_text(self, text):
        """Extract poker cards from text."""
        from poker_engine import RANKS
        
        hole_cards = []
        community_cards = []
        
        # Replace common suit notations
        text_normalized = text.upper()
        
        # More comprehensive card pattern for Governor of Poker 3 and other poker sites
        # Matches: "AK", "As Kh", "A♠ K♥", "AHABKC", "A of Spades" etc
        card_patterns = [
            r'([2-9]|10|[JQKA])(?:[shdc♠♥♦♣]| OF \w+)?',  # Standard
            r'(?:THE )?([2-9]|10|[JQKA])[shdc♠♥♦♣]',  # With suit
            r'([2-9]|10|[JQKA])\s+(?:OF\s+)?(?:SPADES|HEARTS|DIAMONDS|CLUBS|♠|♥|♦|♣)',
        ]
        
        all_matches = []
        for pattern in card_patterns:
            matches = re.findall(pattern, text_normalized)
            all_matches.extend([m if isinstance(m, str) else m[0] for m in matches])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in all_matches:
            if match not in seen and match in RANKS:
                unique_matches.append(match)
                seen.add(match)
        
        # Assign suits (default to spades if not detected)
        suits_order = ['♠', '♥', '♦', '♣']
        
        for i, rank in enumerate(unique_matches[:7]):  # Max 7 cards
            if i < len(suits_order):
                suit = suits_order[i % len(suits_order)]
            else:
                suit = '♠'
            
            card = (rank, suit)
            
            # First 2 cards are hole cards, rest are community
            if i < 2:
                hole_cards.append(card)
            else:
                community_cards.append(card)
        
        return {
            'hole_cards': hole_cards,
            'community_cards': community_cards
        }
    
    def smart_infer_poker_data(self, extracted):
        """
        Intelligently infer poker game state from extracted data.
        Makes educated guesses about pot, call amount, opponents.
        """
        numbers = sorted(extracted.get('extracted_numbers', []))
        
        poker_data = {
            'hole_cards': extracted.get('detected_cards', []),
            'community': extracted.get('detected_community', []),
            'pot_size': None,
            'call_amount': None,
            'stack': None,
            'num_opponents': 5,  # Default reasonable estimate
            'confidence': 'low'
        }
        
        # If we have at least 3 numbers, try to infer
        if len(numbers) >= 3:
            # Heuristic: usually pot < stack, call_amount < pot
            poker_data['pot_size'] = numbers[-2] if len(numbers) >= 2 else 0
            poker_data['call_amount'] = 0  # Assume no current bet (can be refined)
            poker_data['stack'] = numbers[-1]  # Largest number = stack
            poker_data['confidence'] = 'medium'
        elif len(numbers) >= 1:
            poker_data['pot_size'] = numbers[0]
            poker_data['stack'] = numbers[0] * 3  # Estimate
            poker_data['confidence'] = 'low'
        
        return poker_data
    
    def run_continuous_auto_analysis(self, show_all=False):
        """
        Run continuous analysis with automatic recommendations.
        Uses Claude Vision to auto-detect: cards, pot, call amount, opponents, stack.
        Only shows output when poker is detected.
        """
        print("\n" + "="*70)
        print("AUTOMATIC POKER BOT - REAL-TIME ANALYSIS")
        print("="*70)
        print("🔍 Analyzing screenshots every 3 seconds...")
        print("📌 Press Ctrl+C to stop\n")
        
        last_hand_id = None
        analysis_count = 0
        
        for screenshot_data in self.analyzer.run_continuous_analysis():
            
            # Get the image from analyzer
            image = screenshot_data.get('raw_image')
            if image is None:
                continue
            
            extracted_image = self.extract_poker_info_from_image(image, vision_data=screenshot_data)
            if extracted_image.get('detected_cards'):
                hole_cards = extracted_image.get('detected_cards', [])
                community_cards = extracted_image.get('detected_community', [])
                game_state = self._normalize_game_state(extracted_image.get('game_state', {}))
                detected_method = extracted_image.get('method', 'Image detector')
            else:
                extracted = self.extract_poker_info_from_text(screenshot_data['text'])
                game_state = self.smart_infer_poker_data(extracted)
                hole_cards = game_state.get('hole_cards', [])
                community_cards = game_state.get('community', [])
                detected_method = "EasyOCR"
            
            # Get game state values (auto-detected or defaults)
            num_opponents = int(game_state.get('num_opponents') or 5)
            pot_size = self._money_to_number(game_state.get('pot_size') or game_state.get('pot'), 0)
            call_amount = self._money_to_number(game_state.get('call_amount') or game_state.get('call'), 0)
            stack = self._money_to_number(game_state.get('stack_size') or game_state.get('stack'), 1000)
            
            # Check if poker screen detected
            is_poker = len(hole_cards) >= 2 and detected_method
            
            if not is_poker and not show_all:
                continue
            
            # Validate hole cards
            if not hole_cards or len(hole_cards) != 2:
                if show_all:
                    print(f"⏭️  Skipping: Could not detect 2 hole cards")
                continue
            
            # Check if this is a new hand (use hole cards as ID)
            hand_id = str(hole_cards) + str(community_cards)
            if hand_id == last_hand_id and not show_all:
                continue  # Same hand, skip
            
            last_hand_id = hand_id
            analysis_count += 1
            
            # Run analysis
            print("\n" + "="*70)
            print(f"🎯 HAND #{analysis_count} - AUTOMATIC ANALYSIS")
            print("="*70)
            
            print(f"📊 AUTO-DETECTED Data:")
            print(f"   Detection Method: {detected_method}")
            print(f"   Hole Cards  : {self._format_cards(hole_cards)}")
            print(f"   Community   : {self._format_cards(community_cards)} ({len(community_cards)} cards)")
            print(f"   Pot Size    : {pot_size} chips (AUTO)")
            print(f"   Call Amount : {call_amount} chips (AUTO)")
            print(f"   Stack Size  : {stack} chips (AUTO)")
            print(f"   Opponents   : {num_opponents} (AUTO)")
            
            print("\n🔄 Running poker analysis...\n")
            
            try:
                # Run poker engine analysis
                analyze_situation(
                    hole_cards=hole_cards,
                    community=community_cards,
                    num_opponents=num_opponents,
                    pot_size=pot_size,
                    call_amount=call_amount,
                    stack=stack
                )
                
                self.last_analysis = {
                    'hole_cards': hole_cards,
                    'community': community_cards,
                    'game_state': game_state,
                    'method': detected_method
                }
                
            except Exception as e:
                print(f"❌ Analysis error: {e}")
            
            print("="*70)
            print(f"⏳ Waiting for next hand...")


if __name__ == "__main__":
    bot = AutomaticPokerAnalyzer()
    
    try:
        # Show mode: show all detections, even partial ones (for debugging)
        show_all = False  # Set to True for debugging
        bot.run_continuous_auto_analysis(show_all=show_all)
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")

"""
Claude Vision-based Card Recognizer
Uses Anthropic's Claude AI to detect and identify poker cards in screenshots
"""

import anthropic
import base64
import os
from typing import List, Tuple
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

class ClaudeCardRecognizer:
    def __init__(self):
        """Initialize Claude Vision card recognizer"""
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found in .env file")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        print("[CLAUDE RECOGNIZER] Claude Vision card recognizer initialized")
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_data = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')
        return image_data
    
    def recognize_cards(self, image: Image.Image, verbose: bool = False) -> Tuple[List[Tuple[str, str]], str]:
        """
        Use Claude Vision to detect poker cards in image.
        
        Args:
            image: PIL Image object from screenshot
            verbose: Print debug info
            
        Returns:
            Tuple of (detected_cards, analysis_notes)
            detected_cards: List of (rank, suit) tuples, e.g., [('A', '♠'), ('K', '♥')]
            analysis_notes: Claude's reasoning about the detection
        """
        try:
            # Convert image to base64
            image_base64 = self.image_to_base64(image)
            
            # Create prompt for card detection
            prompt = """Analyze this poker screenshot and identify all visible playing cards.

IMPORTANT - Return response in this exact format:
CARDS: [rank1-suit1, rank2-suit2, ...]
COMMUNITY: [community cards if visible, or NONE]
NOTES: [brief observation about card positions/visibility]

Where:
- Ranks: 2-10, J, Q, K, A
- Suits: ♠ (spades), ♥ (hearts), ♦ (diamonds), ♣ (clubs)
- Return hole cards (player cards) first, then community cards separately

Example format:
CARDS: [A-♠, K-♥]
COMMUNITY: [Q-♣, J-♦, 10-♠]
NOTES: Clear visibility, high contrast

If this is NOT a poker screenshot, respond with:
CARDS: NONE
COMMUNITY: NONE
NOTES: [reason why not a poker screenshot]
"""
            
            # Call Claude Vision API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            response_text = message.content[0].text
            if verbose:
                print(f"[CLAUDE RECOGNIZER] Claude response:\n{response_text}")
            
            # Parse Claude's response
            cards, community, notes = self._parse_claude_response(response_text)
            
            if verbose:
                print(f"[CLAUDE RECOGNIZER] Detected hole cards: {cards}")
                print(f"[CLAUDE RECOGNIZER] Community cards: {community}")
                print(f"[CLAUDE RECOGNIZER] Notes: {notes}")
            
            return cards, community, notes
        
        except anthropic.APIError as e:
            print(f"[CLAUDE RECOGNIZER] API Error: {e}")
            return [], [], f"API Error: {str(e)}"
        except Exception as e:
            print(f"[CLAUDE RECOGNIZER] Error: {e}")
            return [], [], f"Error: {str(e)}"
    
    def _parse_claude_response(self, response: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]], str]:
        """
        Parse Claude's response to extract cards and notes.
        
        Returns:
            (hole_cards, community_cards, notes)
        """
        lines = response.strip().split('\n')
        hole_cards = []
        community_cards = []
        notes = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('CARDS:'):
                # Parse hole cards
                cards_str = line.replace('CARDS:', '').strip().strip('[]')
                if cards_str.upper() != 'NONE':
                    hole_cards = self._parse_cards_string(cards_str)
            
            elif line.startswith('COMMUNITY:'):
                # Parse community cards
                community_str = line.replace('COMMUNITY:', '').strip().strip('[]')
                if community_str.upper() != 'NONE':
                    community_cards = self._parse_cards_string(community_str)
            
            elif line.startswith('NOTES:'):
                notes = line.replace('NOTES:', '').strip()
        
        return hole_cards, community_cards, notes
    
    def _parse_cards_string(self, cards_str: str) -> List[Tuple[str, str]]:
        """
        Parse card string like "A-♠, K-♥" into [(rank, suit), ...]
        """
        cards = []
        
        # Split by comma
        card_list = cards_str.split(',')
        
        for card in card_list:
            card = card.strip()
            
            # Handle format like "A-♠" or "A♠" or "A of Spades"
            if '-' in card:
                parts = card.split('-')
                rank = parts[0].strip()
                suit = parts[1].strip()
            elif any(suit in card for suit in ['♠', '♥', '♦', '♣']):
                # Find suit symbol
                for suit_symbol in ['♠', '♥', '♦', '♣']:
                    if suit_symbol in card:
                        parts = card.split(suit_symbol)
                        rank = parts[0].strip()
                        suit = suit_symbol
                        break
            else:
                continue
            
            # Validate rank
            if rank.upper() in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']:
                cards.append((rank.upper(), suit))
        
        return cards
    
    def analyze_and_compare(self, image: Image.Image, other_detectors_results: dict = None, verbose: bool = False) -> dict:
        """
        Use Claude Vision and optionally compare with other detection methods.
        
        Args:
            image: PIL Image to analyze
            other_detectors_results: Dict with results from YOLO, EasyOCR, etc.
            verbose: Print details
            
        Returns:
            dict with:
            - claude_cards: Claude's detection
            - claude_community: Community cards from Claude
            - claude_confidence: Confidence score (low/medium/high)
            - comparison: Comparison with other methods if provided
            - recommendation: Which result to trust most
        """
        hole_cards, community_cards, notes = self.recognize_cards(image, verbose=verbose)
        
        # Determine confidence based on notes
        confidence = self._estimate_confidence(notes)
        
        result = {
            'method': 'Claude Vision',
            'hole_cards': hole_cards,
            'community_cards': community_cards,
            'confidence': confidence,
            'notes': notes,
        }
        
        # If other detectors provided, compare results
        if other_detectors_results:
            result['comparison'] = {
                'other_methods': other_detectors_results,
                'agreement': self._check_agreement(hole_cards, other_detectors_results.get('hole_cards', [])),
            }
            
            # Recommendation logic
            if result['agreement']:
                result['recommendation'] = 'HIGH - Multiple methods agree'
            elif confidence == 'high':
                result['recommendation'] = 'MEDIUM - Claude confident, others differ'
            else:
                result['recommendation'] = 'LOW - Methods disagree, review required'
        
        return result
    
    def _estimate_confidence(self, notes: str) -> str:
        """Estimate confidence from Claude's notes"""
        notes_lower = notes.lower()
        
        if any(word in notes_lower for word in ['clear', 'high contrast', 'visible', 'obvious']):
            return 'high'
        elif any(word in notes_lower for word in ['partial', 'unclear', 'blurry', 'obscured']):
            return 'low'
        else:
            return 'medium'
    
    def _check_agreement(self, claude_cards: List[Tuple[str, str]], other_cards: List) -> bool:
        """Check if Claude's detection agrees with other methods"""
        if not other_cards or not claude_cards:
            return False
        
        # Simple check: do we have the same number of cards in same order?
        claude_ranks = [card[0] for card in claude_cards]
        other_ranks = [card[0] if isinstance(card, tuple) else card for card in other_cards]
        
        return claude_ranks == other_ranks


if __name__ == "__main__":
    # Test the recognizer
    recognizer = ClaudeCardRecognizer()
    print("✓ Claude Card Recognizer initialized")
    print("Ready to analyze poker screenshots!")

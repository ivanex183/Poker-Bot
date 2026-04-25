"""
Integration between screenshot analyzer and poker engine.
Runs continuous analysis and feeds data to poker_engine for recommendations.
"""

from screenshot_analyzer import PokerTableAnalyzer
from poker_engine import analyze_situation
import json
import time

class PokerBotIntegration:
    def __init__(self):
        self.analyzer = PokerTableAnalyzer()
        self.last_recommendation = None
    
    def parse_extracted_data(self, poker_data):
        """
        Convert extracted vision data into poker_engine compatible format.
        This is where manual input may be needed if vision can't detect everything.
        """
        
        # Check if we successfully detected a poker screen
        if not poker_data.get('is_poker_screen'):
            return None
        
        try:
            # Extract hole cards - these need manual input or better vision parsing
            hole_cards = self._parse_cards(poker_data.get('detected_cards', []))
            
            # For now, these need manual input or advanced parsing
            community_cards = self._parse_community_cards(poker_data)
            pot_size = self._parse_pot(poker_data)
            stacks = self._parse_stacks(poker_data)
            
            if not hole_cards:
                print("Warning: Could not detect hole cards. Manual input required.")
                return None
            
            return {
                'hole_cards': hole_cards,
                'community_cards': community_cards,
                'pot_size': pot_size,
                'stacks': stacks
            }
        
        except Exception as e:
            print(f"Error parsing extracted data: {e}")
            return None
    
    def _parse_cards(self, detected_cards):
        """Convert detected card text into (rank, suit) tuples."""
        cards = []
        # This is simplified - real implementation would need better suit detection
        # For now, return empty as suit detection requires more sophisticated parsing
        return cards
    
    def _parse_community_cards(self, poker_data):
        """Extract community cards from vision data."""
        # TODO: Implement better community card detection
        return []
    
    def _parse_pot(self, poker_data):
        """Extract pot size from vision data."""
        # TODO: Implement pot detection
        return 0
    
    def _parse_stacks(self, poker_data):
        """Extract player stacks from vision data."""
        # TODO: Implement stack detection
        return {}
    
    def run_with_manual_input(self):
        """
        Run analysis with manual input for critical data.
        Vision API detects some data, user confirms/enters the rest.
        """
        print("\n" + "="*60)
        print("POKER BOT - MANUAL INPUT MODE")
        print("="*60)
        
        for poker_data in self.analyzer.run_continuous_analysis():
            
            # Display what was detected
            if poker_data.get('detected_cards'):
                print(f"\nDetected cards: {poker_data['detected_cards']}")
            
            print(f"\nAnalysis data (press Enter to skip, or 'q' to quit):")
            
            try:
                # Manual input for hole cards
                hole_input = input("Your hole cards (e.g., 'AK', 'QQ', or 'As Kh'): ").strip()
                if hole_input.lower() == 'q':
                    break
                
                if not hole_input:
                    continue
                
                # Parse input
                hole_cards = self._parse_card_input(hole_input)
                
                # Validate hole cards
                if len(hole_cards) != 2:
                    print(f"❌ Error: Need exactly 2 hole cards, got {len(hole_cards)}")
                    print("   Use ENGLISH letters only: A, K, Q, J, 10, 2-9")
                    print("   Examples: 'AK', 'QQ', 'As Ks', '10h 9d'\n")
                    continue
                
                # Get other info
                community_input = input("Community cards (empty if none): ").strip()
                community_cards = self._parse_card_input(community_input) if community_input else []
                
                pot = float(input("Pot size (chips): ") or 0)
                call_amount = float(input("Amount to call (0 if no bet): ") or 0)
                stack = float(input("Your stack size: ") or 0)
                num_opponents = int(input("Number of opponents: ") or 1)
                
                # Run poker engine analysis
                print("\n" + "="*60)
                try:
                    analyze_situation(
                        hole_cards=hole_cards,
                        community=community_cards,
                        num_opponents=num_opponents,
                        pot_size=pot,
                        call_amount=call_amount,
                        stack=stack
                    )
                except Exception as analysis_error:
                    print(f"❌ Analysis error: {analysis_error}")
                print("="*60)
                
                self.last_recommendation = {
                    'hole_cards': hole_cards,
                    'community': community_cards,
                    'timestamp': time.time()
                }
                
                print(f"\nWaiting {self.analyzer.analysis_interval} seconds for next analysis...\n")
            
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    def _parse_card_input(self, card_str):
        """Convert user card input string to (rank, suit) tuples."""
        from poker_engine import RANKS, SUITS
        
        cards = []
        card_str = card_str.upper().strip()
        
        # Handle formats like "AK", "As Kh", "A♠K♥", "AS KH"
        suits_map = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
        
        i = 0
        while i < len(card_str):
            # Skip spaces
            if card_str[i] == ' ':
                i += 1
                continue
            
            # Check for "10" (2 characters)
            if i + 1 < len(card_str) and card_str[i:i+2] == '10':
                rank = '10'
                i += 2
            else:
                rank = card_str[i]
                i += 1
            
            # Validate rank
            if rank not in RANKS:
                continue
            
            # Look for suit
            suit = None
            if i < len(card_str):
                next_char = card_str[i]
                if next_char in suits_map:
                    suit = suits_map[next_char]
                    i += 1
                elif next_char in SUITS:
                    suit = next_char
                    i += 1
                elif next_char.isalpha():
                    # Skip unknown characters
                    i += 1
                    continue
            
            # Default suit if none specified
            if suit is None:
                suit = '♠'
            
            cards.append((rank, suit))
        
        return cards


if __name__ == "__main__":
    bot = PokerBotIntegration()
    bot.run_with_manual_input()

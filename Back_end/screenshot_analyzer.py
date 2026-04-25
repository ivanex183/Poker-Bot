import mss
from PIL import Image
import easyocr
import json
import time
import os
import re
from dotenv import load_dotenv

load_dotenv()

class PokerTableAnalyzer:
    def __init__(self):
        self.analysis_interval = int(os.getenv('ANALYSIS_INTERVAL', 3))
        # Initialize EasyOCR reader for English
        print("Initializing OCR engine (first run may take 30 seconds)...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        
    def capture_screenshot(self, region=None):
        """
        Capture screenshot of the screen or a specific region.
        region: tuple of (x1, y1, x2, y2) or None for full screen
        """
        with mss.mss() as sct:
            if region:
                x1, y1, x2, y2 = region
                monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
            else:
                monitor = sct.monitors[1]  # Primary monitor
            
            screenshot = sct.grab(monitor)
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            return img
    
    def analyze_table_image(self, image):
        """
        Use EasyOCR to extract text from screenshot.
        Returns extracted text and processed data.
        """
        # Convert PIL image to numpy array for EasyOCR
        import numpy as np
        img_array = np.array(image)
        
        # Run EasyOCR
        results = self.reader.readtext(img_array)
        
        # Extract and concatenate all detected text
        extracted_text = '\n'.join([text for (bbox, text, confidence) in results])
        
        return {
            'text': extracted_text,
            'raw_image': image,
            'raw_results': results
        }
    
    def extract_poker_data(self, vision_data):
        """
        Parse Tesseract OCR output to extract poker-relevant information.
        Returns structured poker table data.
        """
        text = vision_data['text'].upper()
        
        poker_data = {
            'hole_cards': [],
            'community_cards': [],
            'pot_size': None,
            'stacks': {},
            'num_players': None,
            'position': None,
            'raw_text': text,
            'confidence': 'medium',
            'is_poker_screen': False
        }
        
        # Extract numbers (for pot, stacks)
        numbers = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text)
        if numbers:
            poker_data['extracted_numbers'] = numbers
        
        # Look for poker keywords
        poker_keywords = ['FOLD', 'CALL', 'RAISE', 'CHECK', 'BET', 'ALL IN', 'POT', 'FLOP', 'TURN', 'RIVER']
        if any(keyword in text for keyword in poker_keywords):
            poker_data['is_poker_screen'] = True
        
        # Extract card ranks and suits (A, K, Q, J, 10, 2-9)
        card_pattern = r'([2-9]|10|[JQKA])[♠♥♦♣]'
        matches = re.findall(card_pattern, text)
        if matches:
            poker_data['detected_cards'] = matches
        
        return poker_data
    
    def run_continuous_analysis(self):
        """
        Run continuous analysis every N seconds.
        Yields structured poker data.
        """
        print("Starting continuous poker table analysis...")
        print(f"Analysis interval: {self.analysis_interval} seconds")
        
        while True:
            try:
                # Capture screenshot
                screenshot = self.capture_screenshot()
                
                # Analyze with Vision API
                vision_data = self.analyze_table_image(screenshot)
                
                # Extract poker-specific data
                poker_data = self.extract_poker_data(vision_data)
                
                yield poker_data
                
                # Wait before next analysis
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                print(f"Error during analysis: {e}")
                time.sleep(self.analysis_interval)


if __name__ == "__main__":
    analyzer = PokerTableAnalyzer()
    
    # Test single screenshot
    print("\nCapturing and analyzing screenshot with EasyOCR...")
    try:
        screenshot = analyzer.capture_screenshot()
        screenshot.save("test_screenshot.png")
        print("✓ Screenshot saved as test_screenshot.png")
        
        vision_data = analyzer.analyze_table_image(screenshot)
        poker_data = analyzer.extract_poker_data(vision_data)
        
        print("\n=== Extracted Data ===")
        print(json.dumps(poker_data, indent=2, default=str))
        
        if poker_data['is_poker_screen']:
            print("\n✓ Poker screen detected!")
        else:
            print("\n✗ Could not detect poker screen (take a screenshot of a poker table)")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"Details: {str(e)}")

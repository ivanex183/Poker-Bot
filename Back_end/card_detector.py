"""
Card Detector using Template Matching + Color Detection
Specialized for detecting playing cards in poker games
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple
import os

class CardDetector:
    """Detects cards from game screenshots using template matching"""
    
    def __init__(self):
        """Initialize card detector"""
        self.card_values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.card_suits = ['♠', '♥', '♦', '♣']
        
        # Color ranges for suit detection (HSV)
        # Red hearts/diamonds
        self.lower_red1 = np.array([0, 80, 80])
        self.upper_red1 = np.array([15, 255, 255])
        self.lower_red2 = np.array([165, 80, 80])
        self.upper_red2 = np.array([180, 255, 255])
        
        # Black spades/clubs
        self.lower_black = np.array([0, 0, 0])
        self.upper_black = np.array([180, 100, 60])
        
        print("[CARD DETECTOR] Template Matching detector initialized")
    
    def detect_cards(self, image: Image.Image, verbose=False) -> List[str]:
        """
        Detect cards using color + shape detection
        
        Args:
            image: PIL Image from screenshot
            verbose: Print debug info
            
        Returns:
            List of detected cards (e.g., ['A♠', 'K♥'])
        """
        # Convert PIL to OpenCV
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        detected_cards = []
        
        # Find red regions (hearts/diamonds)
        mask_red1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # Find black regions (spades/clubs)
        mask_black = cv2.inRange(hsv, self.lower_black, self.upper_black)
        
        # Find card regions (white/light background)
        _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Combine masks - cards have distinct colored suits
        mask_combined = cv2.bitwise_or(mask_red, mask_black)
        mask_combined = cv2.bitwise_and(mask_combined, mask_white)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask_combined = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)
        mask_combined = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if verbose:
            print(f"[CARD DETECTOR] Found {len(contours)} candidate regions")
        
        # Process each contour
        card_rois = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by size - poker cards are medium-sized
            if area < 800 or area > 300000:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio (cards are roughly square-ish)
            aspect_ratio = w / (h + 0.001)
            if aspect_ratio < 0.3 or aspect_ratio > 0.9:
                continue
            
            # Extract card region
            card_roi = cv_image[y:y+h, x:x+w]
            card_rois.append((card_roi, x, y, w, h))
        
        if verbose:
            print(f"[CARD DETECTOR] {len(card_rois)} valid card regions after filtering")
        
        # Analyze each card
        for card_roi, x, y, w, h in card_rois:
            suit = self._detect_suit(card_roi)
            value = self._detect_value(card_roi)
            
            if value and suit:
                card = f"{value}{suit}"
                detected_cards.append((card, area))
                if verbose:
                    print(f"  → Detected: {card} at ({x}, {y})")
        
        # Sort by confidence/area and return top 2
        detected_cards.sort(key=lambda x: x[1], reverse=True)
        result = [card for card, _ in detected_cards[:2]]
        
        return result
    
    def _detect_suit(self, card_roi: np.ndarray) -> str:
        """
        Detect card suit by color
        Returns: '♠', '♥', '♦', '♣'
        """
        hsv = cv2.cvtColor(card_roi, cv2.COLOR_BGR2HSV)
        
        # Count red pixels
        mask_red1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        red_count = cv2.countNonZero(mask_red)
        
        # Count black pixels
        mask_black = cv2.inRange(hsv, self.lower_black, self.upper_black)
        black_count = cv2.countNonZero(mask_black)
        
        # Determine suit by color
        if red_count > black_count:
            return '♥'  # Hearts (could also be diamonds)
        else:
            return '♠'  # Spades (could also be clubs)
    
    def _detect_value(self, card_roi: np.ndarray) -> str:
        """
        Detect card value by analyzing card corners
        Looks for distinctive patterns
        """
        # Convert to grayscale
        gray = cv2.cvtColor(card_roi, cv2.COLOR_BGR2GRAY)
        
        # Get top-left corner where rank is usually printed
        corner_size = min(card_roi.shape[0], card_roi.shape[1]) // 3
        top_left = gray[0:corner_size, 0:corner_size]
        
        # Count non-white pixels (text)
        _, thresh = cv2.threshold(top_left, 100, 255, cv2.THRESH_BINARY_INV)
        text_pixels = cv2.countNonZero(thresh)
        
        # Estimate value based on pixel density
        # More pixels = higher card value (K, Q, J)
        pixel_ratio = text_pixels / (corner_size * corner_size + 0.001)
        
        if pixel_ratio > 0.15:
            # High confidence - likely face card
            # Determine which one by shape analysis
            return self._identify_face_card(gray)
        elif pixel_ratio > 0.08:
            # Medium confidence - 10, 9, 8
            return self._identify_mid_card(gray)
        else:
            # Low pixel count - Ace or low cards
            return 'A'
    
    def _identify_face_card(self, gray: np.ndarray) -> str:
        """Identify J, Q, K"""
        # Look for distinctive features
        corner = gray[0:30, 0:30]
        edges = cv2.Canny(corner, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 20:
            # Many contours = detailed face card
            return 'K'  # King likely
        elif len(contours) > 15:
            return 'Q'
        else:
            return 'J'
    
    def _identify_mid_card(self, gray: np.ndarray) -> str:
        """Identify 8, 9, 10"""
        # Count corner darkness
        corner = gray[0:25, 0:25]
        darkness = 255 - np.mean(corner)
        
        if darkness > 100:
            return '10'
        elif darkness > 60:
            return '9'
        else:
            return '8'
    
    def detect_community_cards(self, image: Image.Image) -> List[str]:
        """Detect community cards (FLOP/TURN/RIVER)"""
        # For now, return empty
        return []


# Test
if __name__ == "__main__":
    from PIL import Image
    
    detector = CardDetector()
    print("[TEST] Template Matching detector ready")


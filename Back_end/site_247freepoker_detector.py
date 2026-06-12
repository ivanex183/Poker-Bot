"""
Site-specific detector for 247 Free Poker.

The 247freepoker.com table has a very stable layout: a dark blue header,
green felt, red stack plates, and the hero cards near the lower center.  This
detector uses those layout anchors before falling back to generic OCR/AI.
"""

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


SPADE = "\u2660"
HEART = "\u2665"
DIAMOND = "\u2666"
CLUB = "\u2663"

RED_SUITS = [HEART, DIAMOND]
BLACK_SUITS = [SPADE, CLUB]
RANKS = ["10", "A", "K", "Q", "J", "9", "8", "7", "6", "5", "4", "3", "2"]


@dataclass
class OcrItem:
    text: str
    confidence: float
    bbox: Tuple[float, float, float, float]


class Site247FreePokerDetector:
    """Detects the 247 Free Poker table and extracts the visible game state."""

    HERO_CARDS_REGION = (0.33, 0.48, 0.55, 0.76)
    HERO_STACK_REGION = (0.37, 0.66, 0.52, 0.81)
    POT_REGION = (0.36, 0.15, 0.56, 0.33)
    ACTION_REGION = (0.34, 0.70, 0.66, 0.96)

    def analyze(self, image: Image.Image, vision_data: Optional[dict] = None, verbose: bool = False) -> dict:
        ocr_items = self._ocr_items(vision_data)
        ocr_text = "\n".join(item.text for item in ocr_items)
        site_score = self._site_score(image, ocr_text)

        if verbose:
            print(f"[247 DETECTOR] site score: {site_score:.2f}")

        if site_score < 1.15:
            return {
                "is_poker_screen": False,
                "method": "247 Free Poker Layout",
                "detected_cards": [],
                "detected_community": [],
                "game_state": {},
                "confidence": "low",
            }

        hole_cards = self._detect_hero_cards(image, ocr_items)
        game_state = self._detect_game_state(image, ocr_items)

        confidence = "high" if len(hole_cards) == 2 else "medium"
        return {
            "is_poker_screen": True,
            "method": "247 Free Poker Layout",
            "detected_cards": hole_cards,
            "detected_community": [],
            "game_state": game_state,
            "confidence": confidence,
            "analysis_notes": "Detected 247 Free Poker table from header/felt layout.",
        }

    def _site_score(self, image: Image.Image, ocr_text: str) -> float:
        arr = np.array(image.convert("RGB"))
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        height, width = arr.shape[:2]

        table = hsv[int(height * 0.09):, :]
        header = hsv[:max(1, int(height * 0.08)), :]

        green_mask = (
            (table[:, :, 0] >= 35)
            & (table[:, :, 0] <= 95)
            & (table[:, :, 1] >= 45)
            & (table[:, :, 2] >= 25)
        )
        blue_mask = (
            (header[:, :, 0] >= 95)
            & (header[:, :, 0] <= 130)
            & (header[:, :, 1] >= 40)
            & (header[:, :, 2] >= 20)
        )

        score = 0.0
        if green_mask.mean() > 0.45:
            score += 0.75
        if blue_mask.mean() > 0.30:
            score += 0.45

        text = re.sub(r"\s+", " ", ocr_text.upper())
        if "247" in text and "POKER" in text:
            score += 0.55
        elif any(word in text for word in ["FREE POKER", "POKER", "FOLD", "CALL", "RAISE"]):
            score += 0.25

        return score

    def _detect_hero_cards(self, image: Image.Image, ocr_items: List[OcrItem]) -> List[Tuple[str, str]]:
        rank_candidates = self._rank_candidates_from_ocr(ocr_items, image.size, self.HERO_CARDS_REGION)
        if len(rank_candidates) < 2:
            rank_candidates = self._rank_candidates_from_templates(image)
        color_suits = self._detect_card_color_suits(image)

        cards = []
        for idx, rank in enumerate(rank_candidates[:2]):
            suit = color_suits[idx] if idx < len(color_suits) else self._fallback_suit(cards)
            cards.append((rank, suit))

        return self._dedupe_cards(cards)

    def _rank_candidates_from_ocr(
        self,
        ocr_items: List[OcrItem],
        size: Tuple[int, int],
        region: Tuple[float, float, float, float],
    ) -> List[str]:
        width, height = size
        x1, y1, x2, y2 = self._abs_region(region, width, height)
        candidates: List[Tuple[float, str]] = []

        for item in ocr_items:
            bx1, by1, bx2, by2 = item.bbox
            cx = (bx1 + bx2) / 2
            cy = (by1 + by2) / 2
            if not (x1 <= cx <= x2 and y1 <= cy <= y2):
                continue

            for rank in self._extract_ranks(item.text):
                candidates.append((cx, rank))

        candidates.sort(key=lambda value: value[0])
        ranks = [rank for _, rank in candidates]

        if len(ranks) >= 2:
            return ranks

        return ranks

    def _rank_candidates_from_templates(self, image: Image.Image) -> List[str]:
        crop = self._crop_region(image, self.HERO_CARDS_REGION)
        arr = np.array(crop.convert("RGB"))
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

        red1 = cv2.inRange(hsv, np.array([0, 60, 60]), np.array([12, 255, 255]))
        red2 = cv2.inRange(hsv, np.array([165, 60, 60]), np.array([180, 255, 255]))
        black = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 130, 95]))
        mask = cv2.bitwise_or(cv2.bitwise_or(red1, red2), black)
        mask = cv2.medianBlur(mask, 3)

        hits = []
        for rank in RANKS:
            for template in self._rank_templates(rank, mask.shape):
                th, tw = template.shape[:2]
                if th >= mask.shape[0] or tw >= mask.shape[1]:
                    continue

                result = cv2.matchTemplate(mask, template, cv2.TM_CCOEFF_NORMED)
                _, score, _, max_loc = cv2.minMaxLoc(result)
                if score >= 0.38:
                    x, y = max_loc
                    hits.append((score, x + tw / 2, y + th / 2, rank))

        hits.sort(reverse=True, key=lambda item: item[0])
        selected = []
        min_dx = mask.shape[1] * 0.12
        for score, cx, cy, rank in hits:
            if cy > mask.shape[0] * 0.70:
                continue
            if any(abs(cx - existing_cx) < min_dx for _, existing_cx, _ in selected):
                continue
            selected.append((score, cx, rank))
            if len(selected) == 2:
                break

        selected.sort(key=lambda item: item[1])
        return [rank for _, _, rank in selected]

    def _rank_templates(self, rank: str, target_shape: Tuple[int, int]) -> Iterable[np.ndarray]:
        target_h, _ = target_shape
        font = cv2.FONT_HERSHEY_SIMPLEX
        scales = [0.8, 1.05, 1.3, 1.6, 1.9, 2.2, 2.6]
        if target_h > 260:
            scales.extend([3.0, 3.4])

        for scale in scales:
            thickness = max(2, int(round(scale * 2)))
            (tw, th), baseline = cv2.getTextSize(rank, font, scale, thickness)
            canvas = np.zeros((th + baseline + 10, tw + 10), dtype=np.uint8)
            cv2.putText(canvas, rank, (5, th + 3), font, scale, 255, thickness, cv2.LINE_AA)
            _, template = cv2.threshold(canvas, 40, 255, cv2.THRESH_BINARY)
            yield template

    def _extract_ranks(self, text: str) -> List[str]:
        clean = text.upper().replace("O", "0")
        clean = re.sub(r"[^A-Z0-9]", " ", clean)
        ranks: List[str] = []

        for token in clean.split():
            if token in RANKS:
                ranks.append(token)
                continue

            token = token.replace("0", "10") if token == "1O" else token
            matches = re.findall(r"10|[AKQJ2-9]", token)
            ranks.extend(match for match in matches if match in RANKS)

        return ranks

    def _detect_card_color_suits(self, image: Image.Image) -> List[str]:
        crop = self._crop_region(image, self.HERO_CARDS_REGION)
        arr = np.array(crop.convert("RGB"))
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

        red_mask_1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
        red_mask_2 = cv2.inRange(hsv, np.array([165, 70, 70]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(red_mask_1, red_mask_2)
        black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 120, 80]))

        colored = cv2.bitwise_or(red_mask, black_mask)
        contours, _ = cv2.findContours(colored, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        blobs = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 30:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if y > arr.shape[0] * 0.75:
                continue
            if w > arr.shape[1] * 0.45 or h > arr.shape[0] * 0.55:
                continue
            mask = red_mask[y:y + h, x:x + w]
            red_pixels = cv2.countNonZero(mask)
            suit_pool = RED_SUITS if red_pixels > max(3, area * 0.35) else BLACK_SUITS
            blobs.append((x, y, area, suit_pool))

        blobs.sort(key=lambda item: (item[0], item[1]))
        suits: List[str] = []
        used_by_color: Dict[str, int] = {"red": 0, "black": 0}

        for _, _, _, suit_pool in blobs:
            color = "red" if suit_pool == RED_SUITS else "black"
            suit = suit_pool[used_by_color[color] % len(suit_pool)]
            used_by_color[color] += 1
            if suit not in suits:
                suits.append(suit)
            if len(suits) == 2:
                break

        return suits

    def _detect_game_state(self, image: Image.Image, ocr_items: List[OcrItem]) -> dict:
        pot = self._money_from_region(ocr_items, image.size, self.POT_REGION)
        stack = self._money_from_region(ocr_items, image.size, self.HERO_STACK_REGION)
        call_amount = self._call_amount_from_ocr(ocr_items, image.size)
        opponents = self._count_opponents_from_stack_plates(image)

        return {
            "pot_size": pot,
            "call_amount": call_amount if call_amount is not None else 0,
            "num_opponents": opponents,
            "stack_size": stack,
        }

    def _money_from_region(
        self,
        ocr_items: List[OcrItem],
        size: Tuple[int, int],
        region: Tuple[float, float, float, float],
    ) -> Optional[float]:
        width, height = size
        x1, y1, x2, y2 = self._abs_region(region, width, height)
        values: List[float] = []

        for item in ocr_items:
            bx1, by1, bx2, by2 = item.bbox
            cx = (bx1 + bx2) / 2
            cy = (by1 + by2) / 2
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                values.extend(self._money_values(item.text))

        return max(values) if values else None

    def _call_amount_from_ocr(self, ocr_items: List[OcrItem], size: Tuple[int, int]) -> Optional[float]:
        width, height = size
        x1, y1, x2, y2 = self._abs_region(self.ACTION_REGION, width, height)

        for item in ocr_items:
            bx1, by1, bx2, by2 = item.bbox
            cx = (bx1 + bx2) / 2
            cy = (by1 + by2) / 2
            if not (x1 <= cx <= x2 and y1 <= cy <= y2):
                continue

            text = item.text.upper()
            if "CALL" in text:
                values = self._money_values(text)
                return values[0] if values else 0
            if "CHECK" in text:
                return 0

        return None

    def _count_opponents_from_stack_plates(self, image: Image.Image) -> int:
        arr = np.array(image.convert("RGB"))
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        height, width = arr.shape[:2]

        red1 = cv2.inRange(hsv, np.array([0, 90, 60]), np.array([12, 255, 230]))
        red2 = cv2.inRange(hsv, np.array([165, 90, 60]), np.array([180, 255, 230]))
        mask = cv2.bitwise_or(red1, red2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < width * 0.035 or h < height * 0.012:
                continue
            if w > width * 0.18 or h > height * 0.08:
                continue
            ratio = w / max(1, h)
            if ratio < 2.3 or ratio > 7.5:
                continue
            if y < height * 0.25:
                continue
            plates.append((x, y, w, h))

        unique = self._merge_close_boxes(plates)
        hero_count = 0
        opponents = 0

        for x, y, w, h in unique:
            cx = (x + w / 2) / width
            cy = (y + h / 2) / height
            is_hero = 0.36 <= cx <= 0.54 and cy >= 0.65
            if is_hero:
                hero_count += 1
            else:
                opponents += 1

        if opponents:
            return max(1, opponents)
        if hero_count:
            return 1
        return 5

    def _merge_close_boxes(self, boxes: Iterable[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        merged: List[Tuple[int, int, int, int]] = []
        for box in sorted(boxes, key=lambda item: (item[1], item[0])):
            x, y, w, h = box
            cx = x + w / 2
            cy = y + h / 2
            found = False
            for idx, existing in enumerate(merged):
                ex, ey, ew, eh = existing
                ecx = ex + ew / 2
                ecy = ey + eh / 2
                if abs(cx - ecx) < max(w, ew) * 0.35 and abs(cy - ecy) < max(h, eh) * 0.8:
                    nx1 = min(x, ex)
                    ny1 = min(y, ey)
                    nx2 = max(x + w, ex + ew)
                    ny2 = max(y + h, ey + eh)
                    merged[idx] = (nx1, ny1, nx2 - nx1, ny2 - ny1)
                    found = True
                    break
            if not found:
                merged.append(box)
        return merged

    def _ocr_items(self, vision_data: Optional[dict]) -> List[OcrItem]:
        if not vision_data:
            return []

        items = []
        for result in vision_data.get("raw_results", []):
            if len(result) != 3:
                continue
            bbox, text, confidence = result
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            items.append(OcrItem(str(text), float(confidence), (min(xs), min(ys), max(xs), max(ys))))

        return items

    def _money_values(self, text: str) -> List[float]:
        values = []
        for match in re.findall(r"\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", text):
            try:
                values.append(float(match.replace(",", "")))
            except ValueError:
                pass
        return values

    def _dedupe_cards(self, cards: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        seen = set()
        result = []
        for rank, suit in cards:
            card = (rank, suit)
            if card not in seen:
                result.append(card)
                seen.add(card)
                continue

            suit_pool = RED_SUITS if suit in RED_SUITS else BLACK_SUITS
            for alternate in suit_pool:
                alternate_card = (rank, alternate)
                if alternate_card not in seen:
                    result.append(alternate_card)
                    seen.add(alternate_card)
                    break

        return result

    def _fallback_suit(self, cards: List[Tuple[str, str]]) -> str:
        used = {suit for _, suit in cards}
        for suit in [SPADE, HEART, DIAMOND, CLUB]:
            if suit not in used:
                return suit
        return SPADE

    def _crop_region(self, image: Image.Image, region: Tuple[float, float, float, float]) -> Image.Image:
        width, height = image.size
        return image.crop(self._abs_region(region, width, height))

    def _abs_region(
        self,
        region: Tuple[float, float, float, float],
        width: int,
        height: int,
    ) -> Tuple[int, int, int, int]:
        x1, y1, x2, y2 = region
        return int(x1 * width), int(y1 * height), int(x2 * width), int(y2 * height)

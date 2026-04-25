from itertools import combinations
from collections import Counter
import random

RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
SUITS = ['♠','♥','♦','♣']
RANK_VALUE = {r: i for i, r in enumerate(RANKS)}

def full_deck(exclude):
    deck = []
    for rank in RANKS:
        for suit in SUITS:
            card = (rank, suit)
            if card not in exclude:
                deck.append(card)
    return deck

def rank_val(card):
    return RANK_VALUE[card[0]]

def eval5(cards):
    vals = sorted([rank_val(c) for c in cards], reverse=True)
    
    suits = [c[1] for c in cards]
    
    is_flush = len(set(suits)) == 1
    
    is_straight = (vals == list(range(vals[0], vals[0]-5, -1)))
    
    counts = Counter(vals)
    
    freq = sorted(counts.values(), reverse=True)

    if is_straight and is_flush:
        return (9, vals[0])

    if freq[0] == 4:
        four = [v for v,c in counts.items() if c == 4][0]
        kick = [v for v,c in counts.items() if c != 4][0]
        return (8, four, kick)

    if freq[:2] == [3, 2]:
        three = [v for v,c in counts.items() if c == 3][0]
        pair  = [v for v,c in counts.items() if c == 2][0]
        return (7, three, pair)

    if is_flush:
        return (6, *vals)

    if is_straight:
        return (5, vals[0])

    if freq[0] == 3:
        three = [v for v,c in counts.items() if c == 3][0]
        kick  = sorted([v for v,c in counts.items() if c != 3], reverse=True)
        return (4, three, *kick)

    if freq[:2] == [2, 2]:
        pairs = sorted([v for v,c in counts.items() if c == 2], reverse=True)
        kick  = [v for v,c in counts.items() if c == 1][0]
        return (3, *pairs, kick)

    if freq[0] == 2:
        pair = [v for v,c in counts.items() if c == 2][0]
        kick = sorted([v for v,c in counts.items() if c != 2], reverse=True)
        return (2, pair, *kick)

    return (1, *vals)

def best_hand(seven_cards):
    best = None
    for five in combinations(seven_cards, 5):
        score = eval5(list(five))
        if best is None or score > best:
            best = score
    return best
    
def win_probability(hole_cards, community, num_opponents, simulations=5000):
    known = hole_cards + community
    deck = full_deck(exclude=known)
    needed = 5 - len(community)

    wins = 0
    ties = 0
    losses = 0

    for _ in range(simulations):
        sample = random.sample(deck, needed + num_opponents * 2)
        
        board = community + sample[:needed]
        
        opp_hands = []
        for i in range(num_opponents):
            opp_hand = sample[needed + i*2 : needed + i*2 + 2]
            opp_hands.append(opp_hand)

        my_score  = best_hand(hole_cards + board)
        opp_scores = [best_hand(h + board) for h in opp_hands]
        best_opp  = max(opp_scores)

        if my_score > best_opp:
            wins += 1
        elif my_score == best_opp:
            ties += 1
        else:
            losses += 1

    return {
        'win':  round(wins  / simulations, 4),
        'tie':  round(ties  / simulations, 4),
        'lose': round(losses / simulations, 4),
    }

def pot_odds(call_amount, pot_size):
    if call_amount <= 0:
        return 0.0
    return round(call_amount / (pot_size + call_amount), 4)

def expected_value(win_prob, pot_size, call_amount):
    lose_prob = 1 - win_prob
    return round(win_prob * pot_size - lose_prob * call_amount, 2)

def recommend_action(win_prob, po, ev, pot_size, call_amount):
    
    if call_amount == 0:
        if win_prob >= 0.60:
            action = 'BET'
            reason = f'Strong hand ({win_prob*100:.1f}%). Put pressure on opponents!'
        else:
            action = 'CHECK'
            reason = f'Moderate hand. See the next card for free.'
    
    elif ev > 0:
        if win_prob >= 0.70:
            action = 'RAISE'
            reason = f'EV = +{ev}. Very strong hand — build the pot!'
        else:
            action = 'CALL'
            reason = f'EV = +{ev}. Pot odds: {po*100:.1f}% vs win%: {win_prob*100:.1f}%. Profitable call.'
    
    else:
        if win_prob >= 0.35 and po < win_prob:
            action = 'CALL (marginal)'
            reason = f'EV = {ev}. Borderline spot — proceed with caution.'
        else:
            action = 'FOLD'
            reason = f'EV = {ev}. Not profitable mathematically. Fold.'
    
    return {'action': action, 'reason': reason}

def analyze_situation(hole_cards, community, num_opponents, pot_size, call_amount, stack):
    
    stages = {0: 'Preflop', 3: 'Flop', 4: 'Turn', 5: 'River'}
    stage  = stages.get(len(community), 'Flop')

    print("=" * 50)
    print("         POKERBOT ANALYSIS")
    print("=" * 50)
    print(f"  Hand      : {hole_cards[0]} {hole_cards[1]}")
    print(f"  Board     : {community if community else 'None'}  [{stage}]")
    print(f"  Opponents : {num_opponents}")
    print(f"  Pot       : {pot_size} chips")
    print(f"  To call   : {call_amount} chips")
    print(f"  Stack     : {stack} chips")
    print()

    print(f"  Simulating...")
    probs = win_probability(hole_cards, community, num_opponents)
    print(f"  Win  : {probs['win']*100:.1f}%")
    print(f"  Tie  : {probs['tie']*100:.1f}%")
    print(f"  Lose : {probs['lose']*100:.1f}%")
    print()

    po = pot_odds(call_amount, pot_size)
    ev = expected_value(probs['win'], pot_size, call_amount)

    if call_amount > 0:
        print(f"  Pot odds  : {po*100:.1f}%")
        print(f"  EV        : {ev:+.2f} chips")
        print()

    rec = recommend_action(probs['win'], po, ev, pot_size, call_amount)
    print("-" * 50)
    print(f"  ACTION : {rec['action']}")
    print(f"  REASON : {rec['reason']}")
    print("-" * 50)
import tkinter as tk
import random

# Card values and suits
card_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
               '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
suits = ['♠', '♥', '♦', '♣']

CARD_WIDTH = 60
CARD_HEIGHT = 90
CARD_SPACING = 70

class BlackjackGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blackjack")
        self.geometry("800x600")

        self.wins = 0
        self.losses = 0

        self.canvas = tk.Canvas(self, width=800, height=500, bg='darkgreen')
        self.canvas.pack()

        self.result_label = tk.Label(self, text="", font=('Arial', 14))
        self.result_label.pack()

        self.score_label = tk.Label(self, text=self.get_score_text(), font=('Arial', 12))
        self.score_label.pack()

        control_frame = tk.Frame(self)
        control_frame.pack(pady=5)

        self.hit_button = tk.Button(control_frame, text="Hit", command=self.hit)
        self.hit_button.grid(row=0, column=0, padx=10)

        self.stand_button = tk.Button(control_frame, text="Stand", command=self.stand)
        self.stand_button.grid(row=0, column=1, padx=10)

        self.restart_button = tk.Button(control_frame, text="Restart", command=self.start_game)
        self.restart_button.grid(row=0, column=2, padx=10)

        self.start_game()

    def get_score_text(self):
        return f"Wins: {self.wins}  |  Losses: {self.losses}"

    def start_game(self):
        self.deck = [f"{rank}{suit}" for rank in card_values for suit in suits]
        random.shuffle(self.deck)

        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]

        self.result_label.config(text="")
        self.hit_button.config(state="normal")
        self.stand_button.config(state="normal")

        self.update_display()

    def draw_card(self):
        return self.deck.pop()

    def hand_value(self, hand):
        ranks = [card[:-1] for card in hand]
        value = sum(card_values[rank] for rank in ranks)
        aces = ranks.count('A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def draw_hand(self, hand, y):
        hand_width = len(hand) * CARD_SPACING
        x_start = (800 - hand_width) // 2
        for i, card in enumerate(hand):
            x = x_start + i * CARD_SPACING
            self.draw_card_visual(x, y, card)

    def draw_card_visual(self, x, y, card):
        rank = card[:-1]
        suit = card[-1]
        color = 'red' if suit in ['♥', '♦'] else 'black'

        # Outer card
        self.canvas.create_rectangle(
            x, y, x + CARD_WIDTH, y + CARD_HEIGHT,
            fill='white', outline='black', width=2
        )

        # Inlay (slightly inset inner border)
        inset = 5
        self.canvas.create_rectangle(
            x + inset, y + inset, x + CARD_WIDTH - inset, y + CARD_HEIGHT - inset,
            outline='#cccccc', width=1
        )

        # Centered card text
        self.canvas.create_text(
            x + CARD_WIDTH / 2, y + CARD_HEIGHT / 2,
            text=f"{rank}{suit}", fill=color, font=('Arial', 14, 'bold')
        )

    def update_display(self):
        self.canvas.delete("all")

        self.canvas.create_text(400, 70, text=f"Dealer Hand (Value: {self.hand_value(self.dealer_hand)})",
                                fill='white', font=('Arial', 12, 'bold'))
        self.draw_hand(self.dealer_hand, 100)

        self.canvas.create_text(400, 270, text=f"Player Hand (Value: {self.hand_value(self.player_hand)})",
                                fill='white', font=('Arial', 12, 'bold'))
        self.draw_hand(self.player_hand, 300)

    def hit(self):
        self.player_hand.append(self.draw_card())
        self.update_display()
        if self.hand_value(self.player_hand) > 21:
            self.result_label.config(text="You bust! Dealer wins.")
            self.losses += 1
            self.end_round()

    def stand(self):
        while self.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.draw_card())
        self.update_display()

        player_score = self.hand_value(self.player_hand)
        dealer_score = self.hand_value(self.dealer_hand)

        if dealer_score > 21 or player_score > dealer_score:
            self.result_label.config(text="You win!")
            self.wins += 1
        elif player_score < dealer_score:
            self.result_label.config(text="Dealer wins.")
            self.losses += 1
        else:
            self.result_label.config(text="Push (tie).")

        self.end_round()

    def end_round(self):
        self.hit_button.config(state="disabled")
        self.stand_button.config(state="disabled")
        self.score_label.config(text=self.get_score_text())

if __name__ == '__main__':
    game = BlackjackGame()
    game.mainloop()

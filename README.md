# Password_gen_FP
personalized password generator 
import tkinter as tk

# List of cards to display
community_cards = ["A♠", "10♥", "3♣", "Q♦", "7♣"]
player_cards = ["K♠", "K♥"]

# Suit color mapping
suit_colors = {
    "♠": "black",
    "♣": "black",
    "♥": "red",
    "♦": "red"
}

# Create the main window
root = tk.Tk()
root.title("Texas Hold'em")
root.geometry("800x500")
root.configure(bg="green")

# Outer frame to center contents vertically
outer_frame = tk.Frame(root, bg="green")
outer_frame.pack(expand=True)

# Label for community cards
community_label = tk.Label(
    outer_frame,
    text="Community Cards",
    font=("Helvetica", 14),
    bg="green",
    fg="white"
)
community_label.pack(pady=(0, 10))

# Community cards frame with border
community_frame = tk.Frame(
    outer_frame,
    bg="darkgreen",
    bd=5,
    relief="ridge",
    padx=20,
    pady=20
)
community_frame.pack(pady=(0, 30))

# Label for player's hand
player_label = tk.Label(
    outer_frame,
    text="Your Hand",
    font=("Helvetica", 14),
    bg="green",
    fg="white"
)
player_label.pack(pady=(0, 10))

# Player cards frame with border
player_frame = tk.Frame(
    outer_frame,
    bg="darkgreen",
    bd=5,
    relief="ridge",
    padx=20,
    pady=20
)
player_frame.pack()

# Card dimensions (in pixels)
card_width = 80
card_height = 120

# Draw each community card using Canvas
for i, card in enumerate(community_cards):
    canvas = tk.Canvas(
        community_frame,
        width=card_width,
        height=card_height,
        bg="white",
        highlightthickness=0,
        highlightbackground="black"
    )
    canvas.grid(row=0, column=i, padx=15)

    suit = card[-1]
    color = suit_colors[suit]

    # Draw the card text (value + suit)
    canvas.create_text(
        card_width/2, card_height/2,
        text=card,
        font=("Helvetica", 20, "bold"),
        fill=color
    )

# Draw player's hand cards
for i, card in enumerate(player_cards):
    canvas = tk.Canvas(
        player_frame,
        width=card_width,
        height=card_height,
        bg="white",
        highlightthickness=0,
        highlightbackground="black"
    )
    canvas.grid(row=0, column=i, padx=15)

    suit = card[-1]
    color = suit_colors[suit]

    # Draw the card text (value + suit)
    canvas.create_text(
        card_width/2, card_height/2,
        text=card,
        font=("Helvetica", 20, "bold"),
        fill=color
    )

# Start the GUI
root.mainloop()

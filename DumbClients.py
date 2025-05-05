import socket
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time

# Client configuration
HOST = '127.0.0.1'  # Server IP address
PORT = 65432        # Server port

# Card display settings
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_SPACING = 90
DEALER_Y = 100
PLAYER_Y = 300

class BlackjackClient(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Game Window Set-Up  
        self.title("Blackjack Game")
        self.geometry("800x600")
        self.configure(bg="darkgreen")
        
        # Game state variables
        self.connected = False
        self.money = 0
        self.current_bet = 0
        self.player_hand = []
        self.dealer_visible = []
        self.dealer_hand = []
        self.game_in_progress = False
        
        # Creating our socket
        self.socket = None
        
        # Set up the UI components
        self.setup_ui()
        
        # Attempt connection in a separate thread to not block the UI
        self.connection_thread = threading.Thread(target=self.connect_to_server)
        self.connection_thread.daemon = True
        self.connection_thread.start()

    def setup_ui(self):
        """Set up the user interface components"""
        # Canvas for drawing cards
        self.canvas = tk.Canvas(self, width=800, height=450, bg="darkgreen")
        self.canvas.pack(pady=10) #pady = pading
        
        # Status frame
        status_frame = tk.Frame(self, bg="darkgreen")
        status_frame.pack(fill=tk.X, padx=20)
        
        # Money label
        self.money_label = tk.Label(status_frame, text="Money: $0", font=("Helvetica", 14, "bold"), 
                                   bg="darkgreen", fg="white")
        self.money_label.pack(side=tk.LEFT, padx=10)
        
        # Bet label
        self.bet_label = tk.Label(status_frame, text="Current Bet: $0", font=("Helvetica", 14, "bold"), 
                                 bg="darkgreen", fg="white")
        self.bet_label.pack(side=tk.LEFT, padx=10)
        
        # Message label
        self.message_label = tk.Label(self, text="Connecting to server...", font=("Helvetica", 14), 
                                     bg="darkgreen", fg="white", wraplength=700)
        self.message_label.pack(pady=5)
        
        # Control frame
        control_frame = tk.Frame(self, bg="darkgreen")
        control_frame.pack(pady=10)
        
        # Game action buttons
        self.hit_button = tk.Button(control_frame, text="Hit", command=self.hit, 
                                  font=("Helvetica", 12, "bold"), state=tk.DISABLED)
        self.hit_button.grid(row=0, column=0, padx=10)
        
        self.stand_button = tk.Button(control_frame, text="Stand", command=self.stand, 
                                    font=("Helvetica", 12, "bold"), state=tk.DISABLED)
        self.stand_button.grid(row=0, column=1, padx=10)

        self.double_button = tk.Button(control_frame, text="Double", command=self.double_down,
                              font=("Helvetica", 12, "bold"), state=tk.DISABLED)  # new code
        self.double_button.grid(row=0, column=2, padx=10)  # new code
        
        self.split_button = tk.Button(control_frame, text="Split", command=self.split_hand,
                                     font=("Helvetica", 12, "bold"), state=tk.DISABLED)  # new code
        self.split_button.grid(row=0, column=3, padx=10)  # new code

        
        # Bet frame
        bet_frame = tk.Frame(self, bg="darkgreen")
        bet_frame.pack(pady=5)
        
        # Bet amount selection
        bet_label = tk.Label(bet_frame, text="Bet Amount:", font=("Helvetica", 12), 
                           bg="darkgreen", fg="white")
        bet_label.grid(row=0, column=0, padx=5)
        
        self.bet_var = tk.IntVar()
        self.bet_var.set(10)
        
        # Bet amount options
        bet_amounts = [10, 25, 50, 100, 200]
        for i, amount in enumerate(bet_amounts):
            tk.Radiobutton(bet_frame, text=f"${amount}", variable=self.bet_var, value=amount,
                          bg="darkgreen", fg="white", selectcolor="darkblue", 
                          font=("Helvetica", 12)).grid(row=0, column=i+1, padx=5)
        
        # Bet button
        self.bet_button = tk.Button(bet_frame, text="Place Bet", command=self.place_bet, 
                                  font=("Helvetica", 12, "bold"), state=tk.DISABLED)
        self.bet_button.grid(row=0, column=len(bet_amounts)+1, padx=10)
        
        # Connection status indicator
        self.status_indicator = tk.Canvas(self, width=20, height=20, bg="darkgreen", 
                                        highlightthickness=0)
        self.status_indicator.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)
        self.status_light = self.status_indicator.create_oval(2, 2, 18, 18, fill="red")
        
        # Add window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect_to_server(self):
        """Connect to the blackjack server"""
        try:
            # Create a new socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10-second timeout
            
            self.update_message("Connecting to server...")
            
            # Connect to server
            self.socket.connect((HOST, PORT))
            
            # Set status to connected
            self.connected = True
            self.update_status_indicator("green")
            self.update_message("Connected to server!")
            
            # Receive welcome message
            welcome_data = self.receive_data()
            if welcome_data and welcome_data.get("type") == "welcome":
                self.money = welcome_data.get("money", 0)
                self.update_money_display()
                self.update_message(welcome_data.get("message", "Connected to server"))
                
                # Enable betting now that we're connected
                self.enable_betting()
            else:
                self.update_message("Error receiving data from server")
                self.connected = False
                self.update_status_indicator("red")
        
        except socket.timeout:
            self.update_message("Connection timed out. Server not responding.")
            self.update_status_indicator("red")
        
        except ConnectionRefusedError:
            self.update_message("Connection refused. Make sure the server is running.")
            self.update_status_indicator("red")
        
        except Exception as e:
            self.update_message(f"Connection error: {str(e)}")
            self.update_status_indicator("red")

    def update_status_indicator(self, color):
        """Update the connection status indicator color"""
        self.status_indicator.itemconfig(self.status_light, fill=color)

    def update_message(self, message):
        """Update the message label safely from any thread"""
        def update():
            self.message_label.config(text=message)
        
        # If called from a non-main thread, use after() to update safely
        if threading.current_thread() is not threading.main_thread():
            self.after(0, update)
        else:
            update()

    def update_money_display(self):
        """Update the money display label"""
        self.money_label.config(text=f"Money: ${self.money}")

    def update_bet_display(self):
        """Update the bet display label"""
        self.bet_label.config(text=f"Current Bet: ${self.current_bet}")

    def enable_betting(self):
        """Enable the bet button"""
        self.bet_button.config(state=tk.NORMAL)

    def disable_betting(self):
        """Disable the bet button"""
        self.bet_button.config(state=tk.DISABLED)

    def enable_game_controls(self):
        """Enable hit and stand buttons"""
        self.hit_button.config(state=tk.NORMAL)
        self.stand_button.config(state=tk.NORMAL)

    def disable_game_controls(self):
        """Disable hit and stand buttons"""
        self.hit_button.config(state=tk.DISABLED)
        self.stand_button.config(state=tk.DISABLED)

    def receive_data(self):
        """Receive and parse data from the server"""
        if not self.connected or not self.socket:
            return None
        
        try:
            data = self.socket.recv(1024).decode('utf-8')
            if data:
                return json.loads(data)
        except json.JSONDecodeError:
            self.update_message("Error: Received invalid data from server")
        except Exception as e:
            self.update_message(f"Error receiving data: {str(e)}")
            self.connected = False
            self.update_status_indicator("red")
        
        return None

    def send_data(self, data):
        """Send data to the server"""
        if not self.connected or not self.socket:
            self.update_message("Not connected to server")
            return False
        
        try:
            self.socket.sendall(json.dumps(data).encode('utf-8'))
            return True
        except Exception as e:
            self.update_message(f"Error sending data: {str(e)}")
            self.connected = False
            self.update_status_indicator("red")
            return False

    def place_bet(self):
        """Place a bet and start a new game"""
        if not self.connected:
            self.update_message("Not connected to server")
            return
        
        if self.game_in_progress:
            self.update_message("Game already in progress")
            return
        
        # Get bet amount
        bet_amount = self.bet_var.get()
        
        # Validate bet so player can only bet equal to or less than what they have
        if bet_amount <= 0 or bet_amount > self.money:
            self.update_message(f"Invalid bet. Please bet between $1 and ${self.money}")
            return
        
        # Sending the bet back to the server
        bet_data = {
            "type": "bet",
            "amount": bet_amount
        }
        
        if self.send_data(bet_data):
            self.current_bet = bet_amount
            self.update_bet_display()
            self.update_message(f"Placing bet: ${bet_amount}")
            
            # Get game state from server
            game_state = self.receive_data()
            
            if game_state and game_state.get("type") == "game_state":
                # Update game state
                self.player_hand = game_state.get("player_hand", [])
                self.dealer_visible = game_state.get("dealer_visible", [])
                self.dealer_hand = []  # Will be populated later
                self.game_in_progress = True
                
                # Update UI
                self.update_canvas()
                if len(self.player_hand) == 2 and self.money >= self.current_bet:
                    self.double_button.config(state=tk.NORMAL)  # new code
                if self.player_hand[0] == self.player_hand[1] and self.money >= 2 * self.current_bet:
                    self.split_button.config(state=tk.NORMAL)  # new code

                self.update_message(f"Your turn. Hand value: {game_state.get('player_value', 0)}")
                
                # Enable game controls
                self.enable_game_controls()
                self.disable_betting()
            else:
                self.update_message("Error starting game")

    def hit(self):
        """Request another card from the server"""
        if not self.game_in_progress:
            return
        
        # Send hit action to server
        hit_data = {
            "action": "hit"
        }
        
        if self.send_data(hit_data):
            # Get result from server
            result = self.receive_data()
            
            if result:
                if result.get("type") == "hit_result":
                    # Update player hand
                    self.player_hand = result.get("player_hand", [])
                    player_value = result.get("player_value", 0)
                    
                    # Update UI
                    self.update_canvas()
                    self.update_message(f"You drew a {result.get('card')}. Hand value: {player_value}")
                
                elif result.get("type") == "result":
                    # Game ended (likely a bust)
                    self.handle_game_result(result)
            else:
                self.update_message("Error receiving hit result")

    def stand(self):
        if not self.game_in_progress:
            return
    
        if self.send_data({"action": "stand"}):
            result = self.receive_data()
            if result["type"] == "next_hand":  # new code
                self.current_hand_index = result["current_index"]  # new code
                self.update_canvas()  # new code
                self.update_message(f"Now playing hand {self.current_hand_index + 1}")  # new code
            elif result["type"] == "result":
                self.handle_game_result(result)
            else:
                self.update_message("Error receiving stand result")


    def double_down(self):  # new code
        if self.send_data({"action": "double"}):
            result = self.receive_data()
            if result["type"] == "result":
                self.handle_game_result(result)
    
    def split_hand(self):  # new code
        if self.send_data({"action": "split"}):
            result = self.receive_data()
            if result["type"] == "split_ack":
                self.player_hands = result["hands"]
                self.current_hand_index = result["current_index"]
                self.update_canvas()
                self.update_message("Playing first hand after split")
            else:
                self.update_message("Split failed or not allowed")


    def handle_game_result(self, result):
        """Handle the end-game result from the server"""
        self.disable_game_controls()
        self.bet_button.config(state=tk.NORMAL)
        self.game_in_progress = False
    
        if "results" in result:  # from split
            self.player_hands = [r["player_hand"] for r in result["results"]]
            self.dealer_hand = result["results"][0]["dealer_hand"]
            messages = [f"Hand {i+1}: {r['message']}" for i, r in enumerate(result["results"])]
            self.update_message(" | ".join(messages))
        else:
            self.player_hand = result.get("player_hand", [])
            self.dealer_hand = result.get("dealer_hand", [])
            self.update_message(result.get("message", "Game over"))
    
        self.money = result.get("money", self.money)
        self.update_money_display()
        self.update_canvas()
    
        if self.money <= 0:
            messagebox.showinfo("Game Over", "You're out of money! Game over.")
            self.quit()

    def draw_card(self, x, y, value, hidden=False):
        """Draw a card on the canvas"""
        # Card background
        self.canvas.create_rectangle(x, y, x + CARD_WIDTH, y + CARD_HEIGHT, 
                                    fill="white", outline="black", width=2)
        
        if hidden:
            # Hidden card, dealers card (card back)
            self.canvas.create_rectangle(x + 5, y + 5, x + CARD_WIDTH - 5, y + CARD_HEIGHT - 5, 
                                        fill="blue", outline="", width=0)
            self.canvas.create_text(x + CARD_WIDTH/2, y + CARD_HEIGHT/2, 
                                   text="?", fill="white", font=("Arial", 24, "bold"))
        else:
            # Card value and symbol
            card_text = str(value)
            if value == 11:
                card_text = "A"  # Ace
            elif value == 10:
                # Randomly pick a face card or 10
                card_text = random.choice(["10", "J", "Q", "K"])
            
            self.canvas.create_text(x + CARD_WIDTH/2, y + CARD_HEIGHT/2, 
                                   text=card_text, fill="black", font=("Arial", 24, "bold"))
            
            # Card corner values
            small_text = card_text
            self.canvas.create_text(x + 10, y + 15, text=small_text, 
                                   fill="black", font=("Arial", 12, "bold"))
            self.canvas.create_text(x + CARD_WIDTH - 10, y + CARD_HEIGHT - 15, 
                                   text=small_text, fill="black", font=("Arial", 12, "bold"))

    def update_canvas(self):
        """Update the game canvas with current game state"""
        self.canvas.delete("all")
    
        # Draw dealer's cards
        self.canvas.create_text(400, 70, text="Dealer", fill="white", font=("Arial", 16, "bold"))
    
        if hasattr(self, "dealer_hand") and self.dealer_hand:
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            self.canvas.create_text(400, 90, text=f"Value: {dealer_value}", fill="white", font=("Arial", 12))
            start_x = 400 - (len(self.dealer_hand) * CARD_SPACING) // 2
            for i, card in enumerate(self.dealer_hand):
                self.draw_card(start_x + i * CARD_SPACING, DEALER_Y, card)
    
        # Draw player hands
        if hasattr(self, "player_hands"):
            for idx, hand in enumerate(self.player_hands):
                y_offset = PLAYER_Y + (idx * (CARD_HEIGHT + 30))  # stack hands vertically
                label = f"Hand {idx+1} (Active)" if idx == self.current_hand_index else f"Hand {idx+1}"
                hand_value = self.calculate_hand_value(hand)
                self.canvas.create_text(400, y_offset - 20, text=f"{label} – Value: {hand_value}",
                                        fill="yellow" if idx == self.current_hand_index else "white",
                                        font=("Arial", 14, "bold"))
                start_x = 400 - (len(hand) * CARD_SPACING) // 2
                for i, card in enumerate(hand):
                    self.draw_card(start_x + i * CARD_SPACING, y_offset, card)
        elif self.player_hand:
            # fallback: single hand mode
            player_value = self.calculate_hand_value(self.player_hand)
            self.canvas.create_text(400, 270, text=f"Player – Value: {player_value}",
                                    fill="white", font=("Arial", 12))
            start_x = 400 - (len(self.player_hand) * CARD_SPACING) // 2
            for i, card in enumerate(self.player_hand):
                self.draw_card(start_x + i * CARD_SPACING, PLAYER_Y, card)


    def calculate_hand_value(self, hand):
        """Calculate the value of a hand, adjusting for aces"""
        if not hand:
            return 0
            
        total = sum(hand)
        # Count aces (value 11) in the hand
        aces = hand.count(11)
        # Adjust aces from 11 to 1 as needed
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def on_close(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to quit the game?"):
            self.connected = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            self.destroy()

# Add a global random import for card display
import random

# Main entry point
if __name__ == "__main__":
    client = BlackjackClient()
    client.mainloop()

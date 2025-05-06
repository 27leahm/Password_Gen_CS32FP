import socket
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
import random

# Client configuration
HOST = '127.0.0.1'  # Server IP address
PORT = 65432        # Server port

# Card display settings - smaller cards with better spacing
CARD_WIDTH = 65
CARD_HEIGHT = 85
CARD_SPACING = 72
DEALER_Y = 30
PLAYER1_Y = 170
PLAYER2_Y = 320

class TwoPlayerBlackjackClient(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Game Window Set-Up  
        self.title("Two-Player Blackjack Game")
        self.geometry("800x600")
        self.configure(bg="darkgreen")
        
        # Game state variables
        self.connected = False
        self.player1_money = 0
        self.player2_money = 0
        self.current_bet = 0
        self.player1_hand = []
        self.player2_hand = []
        self.dealer_visible = []
        self.dealer_hand = []
        self.game_in_progress = False
        self.current_player = 1  # Track which player's turn it is (1 or 2)
        
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
        self.canvas.pack(pady=5)
        
        # Status frame
        status_frame = tk.Frame(self, bg="darkgreen")
        status_frame.pack(fill=tk.X, padx=20)
        
        # Player 1 Money label - left-aligned
        self.player1_money_label = tk.Label(status_frame, text="Player 1 Money: $0", font=("Courier", 12, "bold"), 
                                bg="darkgreen", fg="white")
        self.player1_money_label.pack(side=tk.LEFT, padx=10)

        # Bet label - centered
        self.bet_label = tk.Label(status_frame, text="Current Bet: $0", font=("Courier", 14, "bold"), 
                                bg="darkgreen", fg="yellow")
        self.bet_label.pack(side=tk.LEFT, padx=10, expand=True)

        # Player 2 Money label - right-aligned
        self.player2_money_label = tk.Label(status_frame, text="Player 2 Money: $0", font=("Courier", 12, "bold"), 
                                bg="darkgreen", fg="white")
        self.player2_money_label.pack(side=tk.RIGHT, padx=10)
        
        # Message label
        self.message_label = tk.Label(self, text="Connecting to server...", font=("Courier", 14), 
                                     bg="darkgreen", fg="white", wraplength=700)
        self.message_label.pack(pady=5)
        
        # Turn indicator
        self.turn_label = tk.Label(self, text="", font=("Courier", 14, "bold"), 
                                  bg="darkgreen", fg="yellow")
        self.turn_label.pack(pady=2)
        
        # Control frame
        control_frame = tk.Frame(self, bg="darkgreen")
        control_frame.pack(pady=5)
        
        # Game action buttons
        self.hit_button = tk.Button(control_frame, text="Hit", command=self.hit, 
                                  font=("Courier", 12, "bold"), state=tk.DISABLED)
        self.hit_button.grid(row=0, column=0, padx=10)
        
        self.stand_button = tk.Button(control_frame, text="Stand", command=self.stand, 
                                    font=("Courier", 12, "bold"), state=tk.DISABLED)
        self.stand_button.grid(row=0, column=1, padx=10)
        
        # Bet frame
        bet_frame = tk.Frame(self, bg="darkgreen")
        bet_frame.pack(pady=5)
        
        # Bet amount selection
        bet_label = tk.Label(bet_frame, text="Bet Amount:", font=("Courier", 12), 
                           bg="darkgreen", fg="white")
        bet_label.grid(row=0, column=0, padx=5)
        
        self.bet_var = tk.IntVar()
        self.bet_var.set(10)
        
        # Bet amount options
        bet_amounts = [25, 50, 100, 200, 500, 1000]
        for i, amount in enumerate(bet_amounts):
            tk.Radiobutton(bet_frame, text=f"${amount}", variable=self.bet_var, value=amount,
                          bg="darkgreen", fg="white", selectcolor="darkblue", 
                          font=("Courier", 12)).grid(row=0, column=i+1, padx=5)
        
        # Bet button
        self.bet_button = tk.Button(bet_frame, text="Place Bet", command=self.place_bet, 
                                  font=("Courier", 12, "bold"), state=tk.DISABLED)
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
            self.socket.settimeout(10)  # added a 10-second timeout for connection to server
            
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
                self.player1_money = welcome_data.get("money", 0)
                self.player2_money = welcome_data.get("money", 0)
                self.update_money_display()
                self.update_message("Two-Player Blackjack! Player 1's turn to bet.")
                self.update_turn_indicator(1)
                
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

    def update_turn_indicator(self, player_num):
        """Update the turn indicator to show which player's turn it is"""
        self.turn_label.config(text=f"Player {player_num}'s Turn")
        self.current_player = player_num

    def update_money_display(self):
        """Update the money display labels"""
        self.player1_money_label.config(text=f"Player 1 Money: ${self.player1_money}")
        self.player2_money_label.config(text=f"Player 2 Money: ${self.player2_money}")

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
        
        # Get current player's money
        current_player_money = self.player1_money if self.current_player == 1 else self.player2_money
        
        # Get bet amount
        bet_amount = self.bet_var.get()
        
        # Validate bet so player can only bet equal to or less than what they have
        if bet_amount <= 0 or bet_amount > current_player_money:
            self.update_message(f"Invalid bet. Please bet between $1 and ${current_player_money}")
            return
        
        # Sending the bet back to the server with player identifier
        bet_data = {
            "type": "bet",
            "amount": bet_amount,
            "player": self.current_player
        }
        
        if self.send_data(bet_data):
            self.current_bet = bet_amount
            self.update_bet_display()
            self.update_message(f"Player {self.current_player} placing bet: ${bet_amount}")
            
            # Get game state from server
            game_state = self.receive_data()
            
            if game_state and game_state.get("type") == "game_state":
                # Update game state based on current player
                if self.current_player == 1:
                    self.player1_hand = game_state.get("player_hand", [])
                else:
                    self.player2_hand = game_state.get("player_hand", [])
                    
                self.dealer_visible = game_state.get("dealer_visible", [])
                self.dealer_hand = []  # Will be populated later
                self.game_in_progress = True
                
                # Update UI
                self.update_canvas()
                player_value = game_state.get('player_value', 0)
                self.update_message(f"Player {self.current_player}'s turn. Hand value: {player_value}")
                
                # Enable game controls
                self.enable_game_controls()
                self.disable_betting()
            else:
                self.update_message("Error starting game")

    def hit(self):
        """Request another card from the server"""
        if not self.game_in_progress:
            return
        
        # Send hit action to server with player identifier
        hit_data = {
            "action": "hit",
            "player": self.current_player
        }
        
        if self.send_data(hit_data):
            # Get result from server
            result = self.receive_data()
            
            if result:
                if result.get("type") == "hit_result":
                    # Update player hand based on current player
                    if self.current_player == 1:
                        self.player1_hand = result.get("player_hand", [])
                    else:
                        self.player2_hand = result.get("player_hand", [])
                        
                    player_value = result.get("player_value", 0)
                    
                    # Update UI
                    self.update_canvas()
                    self.update_message(f"Player {self.current_player} drew a {result.get('card')}. Hand value: {player_value}")
                
                elif result.get("type") == "result":
                    # Player busted, handle game result
                    self.handle_player_result(result)
            else:
                self.update_message("Error receiving hit result")

    def stand(self):
        """Stand with current hand"""
        if not self.game_in_progress:
            return
        
        # Send stand action to server with player identifier
        stand_data = {
            "action": "stand",
            "player": self.current_player
        }
        
        if self.send_data(stand_data):
            if self.current_player == 1:
                # Player 1 is done, switch to Player 2
                result = self.receive_data()
                if result and result.get("type") == "player1_done":
                    self.update_turn_indicator(2)
                    self.update_message("Player 1 stands. Now Player 2's turn to place a bet.")
                    self.game_in_progress = False
                    self.disable_game_controls()
                    self.enable_betting()
                else:
                    self.update_message("Error receiving stand result")
            else:
                # Player 2 is done, get final result
                result = self.receive_data()
                if result and result.get("type") == "result":
                    self.handle_final_result(result)
                else:
                    self.update_message("Error receiving stand result")

    def handle_player_result(self, result):
        """Handle a player busting during the game"""
        # Update game state for the current player
        if self.current_player == 1:
            self.player1_hand = result.get("player_hand", [])
            self.player1_money = result.get("money", self.player1_money)
        else:
            self.player2_hand = result.get("player_hand", [])
            self.player2_money = result.get("money", self.player2_money)
            
        # Update UI
        self.update_money_display()
        self.update_canvas()
        self.update_message(f"Player {self.current_player} {result.get('message', 'Game over')}")
        
        if self.current_player == 1:
            # Switch to Player 2's turn
            self.update_turn_indicator(2)
            self.game_in_progress = False
            self.disable_game_controls()
            self.enable_betting()
            self.update_message(f"Player 1 busted. Now Player 2's turn to place a bet.")
        else:
            # Both players have played, game is over
            self.game_in_progress = False
            self.disable_game_controls()
            self.enable_betting()
            self.update_turn_indicator(1)  # Reset to Player 1 for next round
            self.update_message(f"Player 2 busted. Round complete. Player 1's turn to bet for the next round.")
        
        # Check if any player is out of money
        if self.player1_money <= 0 or self.player2_money <= 0:
            messagebox.showinfo("Game Over", "Game over! One player is out of money!")
            self.quit()

    def handle_final_result(self, result):
        """Handle the end-game result from the server after both players have played"""
        # Update game state
        self.player1_hand = result.get("player1_hand", [])
        self.player2_hand = result.get("player2_hand", [])
        self.dealer_hand = result.get("dealer_hand", [])
        self.dealer_visible = []  # Clear visible cards, we now show the full hand
        self.player1_money = result.get("player1_money", self.player1_money)
        self.player2_money = result.get("player2_money", self.player2_money)
        self.game_in_progress = False
        
        # Create a detailed result message
        player1_result = result.get("player1_result", "")
        player2_result = result.get("player2_result", "")
        dealer_value = result.get("dealer_value", 0)
        player1_value = result.get("player1_value", 0)
        player2_value = result.get("player2_value", 0)
        
        result_message = f"Dealer's hand: {dealer_value}\n"
        if player1_result == "win":
            result_message += f"Player 1 wins with {player1_value}! "
        elif player1_result == "lose":
            result_message += f"Player 1 loses with {player1_value}. "
        elif player1_result == "tie":
            result_message += f"Player 1 ties with {player1_value}. "
        elif player1_result == "bust":
            result_message += f"Player 1 busted with {player1_value}. "
            
        if player2_result == "win":
            result_message += f"Player 2 wins with {player2_value}!"
        elif player2_result == "lose":
            result_message += f"Player 2 loses with {player2_value}."
        elif player2_result == "tie":
            result_message += f"Player 2 ties with {player2_value}."
        elif player2_result == "bust":
            result_message += f"Player 2 busted with {player2_value}."
        
        # Update UI
        self.update_money_display()
        self.update_canvas()
        self.update_message(result_message)
        
        # Disable game controls, enable betting, and set turn to Player 1 for next round
        self.disable_game_controls()
        self.enable_betting()
        self.update_turn_indicator(1)
        
        # Check if any player is out of money
        if self.player1_money <= 0 or self.player2_money <= 0:
            messagebox.showinfo("Game Over", "Game over! One player is out of money!")
            self.quit()

    def draw_card(self, x, y, value, hidden=False):
        """Draw a card on the canvas"""
        # Card background with thicker border
        self.canvas.create_rectangle(x, y, x + CARD_WIDTH, y + CARD_HEIGHT, 
                                    fill="white", outline="black", width=3)
        
        if hidden:
            # Hidden card, dealers card (card back)
            self.canvas.create_rectangle(x + 5, y + 5, x + CARD_WIDTH - 5, y + CARD_HEIGHT - 5, 
                                        fill="red", outline="", width=0)
            self.canvas.create_text(x + CARD_WIDTH/2, y + CARD_HEIGHT/2, 
                                   text="?", fill="white", font=("Courier", 20, "bold"))
        else:
            # Card value and symbol
            card_text = str(value)
            if value == 11:
                card_text = "A"  # Ace
            elif value == 10:
                # Randomly pick a face card or 10
                card_text = random.choice(["10", "J", "Q", "K"])
            
            # Main card value
            self.canvas.create_text(x + CARD_WIDTH/2, y + CARD_HEIGHT/2, 
                                   text=card_text, fill="black", font=("Courier", 20, "bold"))
            
            # Card corner values - only in top left to save space
            small_text = card_text
            self.canvas.create_text(x + 8, y + 12, text=small_text, 
                                   fill="black", font=("Courier", 10, "bold"))

    def update_canvas(self):
        """Update the game canvas with current game state"""
        self.canvas.delete("all")
        
        # Draw dealer's cards
        self.canvas.create_text(400, 10, text="Dealer", fill="white", font=("Courier", 14, "bold"))
        
        if self.dealer_hand:
            # Full dealer hand (end of game)
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            self.canvas.create_text(400, 25, text=f"Value: {dealer_value}", 
                                   fill="white", font=("Courier", 10))
            
            # Draw all dealer cards - limit how many are shown side by side
            max_visible = 5
            if len(self.dealer_hand) > max_visible:
                # Draw first few cards
                start_x = 400 - (max_visible * CARD_SPACING) // 2
                for i in range(max_visible-1):
                    self.draw_card(start_x + i * CARD_SPACING, DEALER_Y, self.dealer_hand[i])
                # Draw last card with indicator that cards are skipped
                self.draw_card(start_x + (max_visible-1) * CARD_SPACING, DEALER_Y, self.dealer_hand[-1])
                # Text indicating skipped cards
                self.canvas.create_text(400, DEALER_Y + CARD_HEIGHT + 15, 
                                      text=f"(+{len(self.dealer_hand) - max_visible} more cards)", 
                                      fill="yellow", font=("Courier", 8))
            else:
                # Draw all dealer cards
                start_x = 400 - (len(self.dealer_hand) * CARD_SPACING) // 2
                for i, card in enumerate(self.dealer_hand):
                    self.draw_card(start_x + i * CARD_SPACING, DEALER_Y, card)
                
        elif self.dealer_visible:
            # Only visible dealer cards (during gameplay)
            start_x = 400 - (2 * CARD_SPACING) // 2  # Assume 2 cards initially
            
            # Draw visible card(s)
            for i, card in enumerate(self.dealer_visible):
                self.draw_card(start_x + i * CARD_SPACING, DEALER_Y, card)
            
            # Draw hidden card
            self.draw_card(start_x + len(self.dealer_visible) * CARD_SPACING, DEALER_Y, 0, hidden=True)
        
        # Draw Player 1's cards
        self.canvas.create_text(400, 145, text="Player 1", fill="white", font=("Courier", 14, "bold"))

        if self.player1_hand:
            player1_value = self.calculate_hand_value(self.player1_hand)
            self.canvas.create_text(400, 160, text=f"Value: {player1_value}", 
                                fill="white", font=("Courier", 10))
            
            # Handle large hands for player 1
            max_visible = 5
            if len(self.player1_hand) > max_visible:
                # Draw first few cards
                start_x = 400 - (max_visible * CARD_SPACING) // 2
                for i in range(max_visible-1):
                    self.draw_card(start_x + i * CARD_SPACING, PLAYER1_Y, self.player1_hand[i])
                # Draw last card
                self.draw_card(start_x + (max_visible-1) * CARD_SPACING, PLAYER1_Y, self.player1_hand[-1])
                # Text indicating skipped cards
                self.canvas.create_text(400, PLAYER1_Y + CARD_HEIGHT + 15, 
                                      text=f"(+{len(self.player1_hand) - max_visible} more cards)", 
                                      fill="yellow", font=("Courier", 8))
            else:
                # Draw all player 1 cards
                start_x = 400 - (len(self.player1_hand) * CARD_SPACING) // 2
                for i, card in enumerate(self.player1_hand):
                    self.draw_card(start_x + i * CARD_SPACING, PLAYER1_Y, card)
        
        # Draw Player 2's cards - centered at position 400 instead of 200
        self.canvas.create_text(400, 295, text="Player 2", fill="white", font=("Courier", 14, "bold"))
       
        if self.player2_hand:
            player2_value = self.calculate_hand_value(self.player2_hand)
            self.canvas.create_text(400, 310, text=f"Value: {player2_value}", 
                                fill="white", font=("Courier", 10))
            
            # Handle large hands for player 2 - centered at position 400
            max_visible = 5
            if len(self.player2_hand) > max_visible:
                # Draw first few cards
                start_x = 400 - (max_visible * CARD_SPACING) // 2
                for i in range(max_visible-1):
                    self.draw_card(start_x + i * CARD_SPACING, PLAYER2_Y, self.player2_hand[i])
                # Draw last card
                self.draw_card(start_x + (max_visible-1) * CARD_SPACING, PLAYER2_Y, self.player2_hand[-1])
                # Text indicating skipped cards
                self.canvas.create_text(400, PLAYER2_Y + CARD_HEIGHT + 15, 
                                      text=f"(+{len(self.player2_hand) - max_visible} more cards)", 
                                      fill="yellow", font=("Courier", 8))
            else:
                # Draw all player 2 cards
                start_x = 400 - (len(self.player2_hand) * CARD_SPACING) // 2
                for i, card in enumerate(self.player2_hand):
                    self.draw_card(start_x + i * CARD_SPACING, PLAYER2_Y, card)


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

# Main entry point
if __name__ == "__main__":
    client = TwoPlayerBlackjackClient()
    client.mainloop()

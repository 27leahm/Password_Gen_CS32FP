import socket
import random
import time
import json

# Basic server configuration
HOST = '127.0.0.1'  # Standard loopback IP address
PORT = 65432        # Port to listen on

# Game variables
STARTING_MONEY = 1000

def deal_card():
    """Returns a random card value between 2-11"""
    cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # 10s represent J,Q,K, 11 is Ace
    return random.choice(cards)

def calculate_hand_value(hand):
    """Calculate the value of a hand, adjusting for aces"""
    total = sum(hand)
    # Count aces (value 11) in the hand
    aces = hand.count(11)
    # Adjust aces from 11 to 1 as needed to get under 21
    while total > 21 and aces > 0:
        total -= 10  # Change one ace from 11 to 1 (reduce by 10)
        aces -= 1
    return total

def run_server():
    """Main server function"""
    print("Starting Blackjack server...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Allow socket reuse to avoid "address already in use" errors
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            print(f"Server running on {HOST}:{PORT}")
            print("Waiting for client connection...")
            
            # Accept client connection
            client_socket, address = server_socket.accept()
            print(f"Client connected from {address}")
            
            with client_socket:
                # Initialize player money
                player_money = STARTING_MONEY
                
                # Send initial message to client
                welcome_message = {
                    "type": "welcome",
                    "money": player_money,
                    "message": "Welcome to Blackjack! You have $1000."
                }
                client_socket.sendall(json.dumps(welcome_message).encode('utf-8'))
                
                # Main game loop
                while player_money > 0:
                    try:
                        # Wait for bet from client
                        data = client_socket.recv(1024).decode('utf-8')
                        if not data:
                            print("Client disconnected")
                            break
                        
                        # Parse client message
                        client_message = json.loads(data)
                        message_type = client_message.get("type", "")
                        
                        # Handle client bet
                        if message_type == "bet":
                            bet_amount = client_message.get("amount", 0)
                            
                            # Validate bet
                            if bet_amount <= 0 or bet_amount > player_money:
                                error_message = {
                                    "type": "error",
                                    "message": "Invalid bet amount"
                                }
                                client_socket.sendall(json.dumps(error_message).encode('utf-8'))
                                continue
                            
                            # Deal initial cards
                            player_hand = [deal_card(), deal_card()]
                            dealer_hand = [deal_card(), deal_card()]
                            
                            # Send game state to client
                            game_state = {
                                "type": "game_state",
                                "player_hand": player_hand,
                                "player_value": calculate_hand_value(player_hand),
                                "dealer_visible": [dealer_hand[0]],  # Only first card visible
                                "bet": bet_amount
                            }
                            client_socket.sendall(json.dumps(game_state).encode('utf-8'))
                            
                            # Player's turn loop
                            game_over = False
                            while not game_over:
                                # Wait for player action
                                action_data = client_socket.recv(1024).decode('utf-8')
                                if not action_data:
                                    print("Client disconnected")
                                    return
                                
                                action_message = json.loads(action_data)
                                action = action_message.get("action", "")
                                
                                # Handle player hit
                                if action == "hit":
                                    # Deal a new card to player
                                    new_card = deal_card()
                                    player_hand.append(new_card)
                                    player_value = calculate_hand_value(player_hand)
                                    
                                    # Check if player busts
                                    if player_value > 21:
                                        # Player busts, dealer wins
                                        player_money -= bet_amount
                                        
                                        result = {
                                            "type": "result",
                                            "player_hand": player_hand,
                                            "player_value": player_value,
                                            "dealer_hand": dealer_hand,
                                            "dealer_value": calculate_hand_value(dealer_hand),
                                            "result": "bust",
                                            "message": "Bust! You lose.",
                                            "money": player_money
                                        }
                                        client_socket.sendall(json.dumps(result).encode('utf-8'))
                                        game_over = True
                                    else:
                                        # Player didn't bust, send updated hand
                                        hit_result = {
                                            "type": "hit_result",
                                            "card": new_card,
                                            "player_hand": player_hand,
                                            "player_value": player_value
                                        }
                                        client_socket.sendall(json.dumps(hit_result).encode('utf-8'))
                                
                                # Handle player stand
                                elif action == "stand":
                                    # Dealer's turn
                                    dealer_value = calculate_hand_value(dealer_hand)
                                    
                                    # Dealer draws cards until reaching at least 17
                                    while dealer_value < 17:
                                        dealer_hand.append(deal_card())
                                        dealer_value = calculate_hand_value(dealer_hand)
                                    
                                    # Determine winner
                                    player_value = calculate_hand_value(player_hand)
                                    
                                    if dealer_value > 21:
                                        # Dealer busts, player wins
                                        result_text = "win"
                                        message = "Dealer busts! You win!"
                                        player_money += bet_amount
                                    elif dealer_value > player_value:
                                        # Dealer has higher value, dealer wins
                                        result_text = "lose"
                                        message = "Dealer wins!"
                                        player_money -= bet_amount
                                    elif player_value > dealer_value:
                                        # Player has higher value, player wins
                                        result_text = "win"
                                        message = "You win!"
                                        player_money += bet_amount
                                    else:
                                        # Tie
                                        result_text = "tie"
                                        message = "It's a tie!"
                                    
                                    # Send final result to client
                                    result = {
                                        "type": "result",
                                        "player_hand": player_hand,
                                        "player_value": player_value,
                                        "dealer_hand": dealer_hand,
                                        "dealer_value": dealer_value,
                                        "result": result_text,
                                        "message": message,
                                        "money": player_money
                                    }
                                    client_socket.sendall(json.dumps(result).encode('utf-8'))
                                    game_over = True
                                
                                else:
                                    # Invalid action
                                    error_message = {
                                        "type": "error",
                                        "message": "Invalid action. Use 'hit' or 'stand'."
                                    }
                                    client_socket.sendall(json.dumps(error_message).encode('utf-8'))
                    
                    except json.JSONDecodeError as e:
                        print(f"JSON error: {e}")
                        error_message = {
                            "type": "error",
                            "message": "Invalid message format"
                        }
                        client_socket.sendall(json.dumps(error_message).encode('utf-8'))
                    
                    except Exception as e:
                        print(f"Error during game: {e}")
                        try:
                            error_message = {
                                "type": "error",
                                "message": "Server error occurred"
                            }
                            client_socket.sendall(json.dumps(error_message).encode('utf-8'))
                        except:
                            pass
                
                # Game over - player out of money
                if player_money <= 0:
                    game_over_message = {
                        "type": "game_over",
                        "message": "You're out of money! Game over."
                    }
                    client_socket.sendall(json.dumps(game_over_message).encode('utf-8'))
        
        except Exception as e:
            print(f"Server error: {e}")

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nServer shutdown by user")
    except Exception as e:
        print(f"Unhandled server error: {e}")
    
    print("Server is shutting down. Press Enter to exit...")
    input()

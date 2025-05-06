import socket
import random
import time
import json

# Basic server configuration
HOST = '127.0.0.1'  # Standard loopback IP address
PORT = 65432        # Port to listen on

# Game variables
STARTING_MONEY = 2000

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
    print("Starting Two-Player Blackjack server...")
    
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
                player1_money = STARTING_MONEY
                player2_money = STARTING_MONEY
                
                # Keep track of dealer's hand for the round
                dealer_hand = []
                
                # Send initial message to client
                welcome_message = {
                    "type": "welcome",
                    "money": STARTING_MONEY,
                    "message": "Welcome to Two-Player Blackjack! Each player has $1000."
                }
                client_socket.sendall(json.dumps(welcome_message).encode('utf-8'))
                
                # Main game loop
                while player1_money > 0 and player2_money > 0:
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
                            player_num = client_message.get("player", 1)  # Default to player 1
                            bet_amount = client_message.get("amount", 0)
                            
                            # Get current player's money
                            current_player_money = player1_money if player_num == 1 else player2_money
                            
                            # Validate bet
                            if bet_amount <= 0 or bet_amount > current_player_money:
                                error_message = {
                                    "type": "error",
                                    "message": "Invalid bet amount"
                                }
                                client_socket.sendall(json.dumps(error_message).encode('utf-8'))
                                continue
                            
                            # Deal initial cards
                            player_hand = [deal_card(), deal_card()]
                            
                            # Only deal dealer cards on first player's turn
                            if player_num == 1:
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
                                current_player = action_message.get("player", player_num)
                                
                                # Handle player hit
                                if action == "hit":
                                    # Deal a new card to player
                                    new_card = deal_card()
                                    player_hand.append(new_card)
                                    player_value = calculate_hand_value(player_hand)
                                    
                                    # Check if player busts
                                    if player_value > 21:
                                        # Player busts, dealer wins
                                        if current_player == 1:
                                            player1_money -= bet_amount
                                        else:
                                            player2_money -= bet_amount
                                        
                                        result = {
                                            "type": "result",
                                            "player_hand": player_hand,
                                            "player_value": player_value,
                                            "money": player1_money if current_player == 1 else player2_money,
                                            "result": "bust",
                                            "message": "Bust! You lose."
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
                                    if current_player == 1:
                                        # Player 1 stands, notify to switch to Player 2
                                        player1_final_hand = player_hand  # Store Player 1's final hand
                                        player1_final_value = calculate_hand_value(player_hand)
                                        
                                        # Notify client to switch to Player 2
                                        player1_done = {
                                            "type": "player1_done",
                                            "player1_hand": player1_final_hand,
                                            "player1_value": player1_final_value
                                        }
                                        client_socket.sendall(json.dumps(player1_done).encode('utf-8'))
                                        game_over = True  # End player 1's turn
                                    
                                    else:  # Player 2 stands
                                        player2_final_hand = player_hand  # Store Player 2's final hand
                                        player2_final_value = calculate_hand_value(player_hand)
                                        
                                        # Now dealer plays
                                        dealer_value = calculate_hand_value(dealer_hand)
                                        
                                        # Dealer draws cards until reaching at least 17
                                        while dealer_value < 17:
                                            dealer_hand.append(deal_card())
                                            dealer_value = calculate_hand_value(dealer_hand)
                                        
                                        # Determine results for both players
                                        player1_result = ""
                                        player2_result = ""
                                        player1_message = ""
                                        player2_message = ""
                                        
                                        # Player 1 result
                                        if player1_final_value > 21:
                                            player1_result = "bust"
                                            player1_message = "Player 1 busted"
                                            # Money already deducted
                                        elif dealer_value > 21:
                                            player1_result = "win"
                                            player1_message = "Player 1 wins! Dealer busted"
                                            player1_money += bet_amount
                                        elif dealer_value > player1_final_value:
                                            player1_result = "lose"
                                            player1_message = "Player 1 loses"
                                            player1_money -= bet_amount
                                        elif player1_final_value > dealer_value:
                                            player1_result = "win"
                                            player1_message = "Player 1 wins!"
                                            player1_money += bet_amount
                                        else:
                                            player1_result = "tie"
                                            player1_message = "Player 1 ties"
                                        
                                        # Player 2 result
                                        if player2_final_value > 21:
                                            player2_result = "bust"
                                            player2_message = "Player 2 busted"
                                            # Money already deducted
                                        elif dealer_value > 21:
                                            player2_result = "win"
                                            player2_message = "Player 2 wins! Dealer busted"
                                            player2_money += bet_amount
                                        elif dealer_value > player2_final_value:
                                            player2_result = "lose"
                                            player2_message = "Player 2 loses"
                                            player2_money -= bet_amount
                                        elif player2_final_value > dealer_value:
                                            player2_result = "win"
                                            player2_message = "Player 2 wins!"
                                            player2_money += bet_amount
                                        else:
                                            player2_result = "tie"
                                            player2_message = "Player 2 ties"
                                        
                                        # Send final result to client
                                        final_result = {
                                            "type": "result",
                                            "player1_hand": player1_final_hand,
                                            "player1_value": player1_final_value,
                                            "player2_hand": player2_final_hand,
                                            "player2_value": player2_final_value,
                                            "dealer_hand": dealer_hand,
                                            "dealer_value": dealer_value,
                                            "player1_result": player1_result,
                                            "player2_result": player2_result,
                                            "player1_money": player1_money,
                                            "player2_money": player2_money,
                                            "message": f"Dealer: {dealer_value}, {player1_message}, {player2_message}"
                                        }
                                        client_socket.sendall(json.dumps(final_result).encode('utf-8'))
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
                
                # Game over - a player is out of money
                if player1_money <= 0 or player2_money <= 0:
                    game_over_message = {
                        "type": "game_over",
                        "message": "Game over! One player is out of money."
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

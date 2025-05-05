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
                            split_hands = [player_hand]  # new code
                            current_hand_index = 0       # new code
                            is_split = False             # new code
                            original_bet = bet_amount    # new code

                            
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

                                current_hand = split_hands[current_hand_index]  # new code
                                
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
                                elif action == "double":  # new code
                                    if len(current_hand) == 2 and player_money >= bet_amount:
                                        bet_amount *= 2
                                        card = deal_card()
                                        current_hand.append(card)
                                        value = calculate_hand_value(current_hand)
                                        while calculate_hand_value(dealer_hand) < 17:
                                            dealer_hand.append(deal_card())
                                        dealer_value = calculate_hand_value(dealer_hand)
                                        if value > 21:
                                            outcome = "bust"
                                            player_money -= bet_amount
                                        elif dealer_value > 21 or value > dealer_value:
                                            outcome = "win"
                                            player_money += bet_amount
                                        elif dealer_value > value:
                                            outcome = "lose"
                                            player_money -= bet_amount
                                        else:
                                            outcome = "tie"
                                        result = {
                                            "type": "result",
                                            "player_hand": current_hand,
                                            "player_value": value,
                                            "dealer_hand": dealer_hand,
                                            "dealer_value": dealer_value,
                                            "result": outcome,
                                            "message": f"Result: {outcome}",
                                            "money": player_money
                                        }
                                        client_socket.sendall(json.dumps(result).encode('utf-8'))
                                        game_over = True
                                elif action == "split":  # new code
                                    if len(current_hand) == 2 and current_hand[0] == current_hand[1] and player_money >= bet_amount:
                                        hand1 = [current_hand[0], deal_card()]
                                        hand2 = [current_hand[1], deal_card()]
                                        split_hands = [hand1, hand2]
                                        player_money -= bet_amount
                                        client_socket.sendall(json.dumps({
                                            "type": "split_ack",
                                            "hands": split_hands,
                                            "current_index": 0
                                        }).encode('utf-8'))
                                    else:
                                        client_socket.sendall(json.dumps({
                                            "type": "error",
                                            "message": "Cannot split now"
                                        }).encode('utf-8'))

                                elif action == "stand":
                                    current_hand_index += 1  # new code
                                    if current_hand_index < len(split_hands):  # still have more hands to play
                                        client_socket.sendall(json.dumps({
                                            "type": "next_hand",
                                            "current_index": current_hand_index
                                        }).encode('utf-8'))
                                        continue  # wait for next hand's action
                                
                                    # All hands played — now dealer goes
                                    dealer_value = calculate_hand_value(dealer_hand)
                                    while dealer_value < 17:
                                        dealer_hand.append(deal_card())
                                        dealer_value = calculate_hand_value(dealer_hand)
                                
                                    # Evaluate results for each hand
                                    results = []
                                    for hand in split_hands:
                                        player_value = calculate_hand_value(hand)
                                        if player_value > 21:
                                            result_text = "bust"
                                            message = "You busted."
                                            player_money -= original_bet
                                        elif dealer_value > 21 or player_value > dealer_value:
                                            result_text = "win"
                                            message = "You win!"
                                            player_money += original_bet
                                        elif dealer_value > player_value:
                                            result_text = "lose"
                                            message = "Dealer wins."
                                            player_money -= original_bet
                                        else:
                                            result_text = "tie"
                                            message = "Push (tie)."
                                        results.append({
                                            "player_hand": hand,
                                            "player_value": player_value,
                                            "dealer_hand": dealer_hand,
                                            "dealer_value": dealer_value,
                                            "result": result_text,
                                            "message": message
                                        })
                                
                                    # Send all results back to client
                                    result = {
                                        "type": "result",
                                        "results": results,
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

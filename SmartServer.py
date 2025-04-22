import socket
import random

HOST = '127.0.0.1'
PORT = 65432

def deal_card():
    #this basically just returns a random card value between 1 and 11
    return random.randint(1, 11)

def hand_total(hand):
    total = sum(hand)
    # this calculates the total vlaue as a hand. basically 11 is an ace and it adjusts if it's over 21
    while total > 21 and 11 in hand:
        hand[hand.index(11)] = 1
        total = sum(hand)
    return total

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT)) #binding server, listening for incoming connections
        s.listen()
        print(f"Blackjack server running on {HOST}:{PORT}...")

        conn, addr = s.accept() #accepts connection lol
        with conn: #deals the intial hands
            print(f"Player connected from {addr}")
            player_hand = [deal_card(), deal_card()]
            dealer_hand = [deal_card(), deal_card()]
            # sends intial hand info to player
            conn.sendall(f"Your cards: {player_hand} (Total: {hand_total(player_hand)})".encode())
# main game loop
            while True:
                data = conn.recv(1024).decode().lower()
                if not data:
                    break

                if data == 'hit':
                    player_hand.append(deal_card())
                    total = hand_total(player_hand)
                    conn.sendall(f"You hit: {player_hand} (Total: {total})".encode())
                    if total > 21:
                        conn.sendall("Bust! You lose.".encode())
                        break
                elif data == 'stand':
                    # Dealer plays
                    while hand_total(dealer_hand) < 17:
                        dealer_hand.append(deal_card())

                    player_total = hand_total(player_hand)
                    dealer_total = hand_total(dealer_hand)

                    result = f"Dealer's hand: {dealer_hand} (Total: {dealer_total})\n"
                    if dealer_total > 21 or player_total > dealer_total:
                        result += "You win!"
                    elif player_total < dealer_total:
                        result += "Dealer wins!"
                    else:
                        result += "It's a tie!"

                    conn.sendall(result.encode())
                    break
                else:
                    conn.sendall("Invalid command. Type 'hit' or 'stand'.".encode())

if __name__ == '__main__':
    start_server()

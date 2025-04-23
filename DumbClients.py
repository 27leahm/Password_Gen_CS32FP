import socket

HOST = '127.0.0.1'
PORT = 65432

def start_client(): # set up a socket lol
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        # Initial hand that you get and print from the server
        data = s.recv(1024).decode()
        print(data)

# this while true loop is the main game loop
        while True:
            # you prompt the player for a move, then send to server
            move = input("Type 'hit' or 'stand': ").strip().lower()
            s.sendall(move.encode())

            #then you receieve a response from surver

            response = s.recv(1024).decode()
            print(response)

            # if round is over, break out of the loop
            if "Bust" in response or "win" in response or "tie" in response:
                break

if __name__ == '__main__':
    start_client()

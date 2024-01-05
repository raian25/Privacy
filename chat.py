import socket
import threading
import curses
import sys

class IRCChat:
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def run(self):
        self.stdscr.clear()
        self.stdscr.addstr("Choose an option:\n")
        self.stdscr.addstr("1. Run IRC Server\n")
        self.stdscr.addstr("2. Run IRC Client\n")
        self.stdscr.refresh()

        option = self.stdscr.getch()

        if option == ord('1'):
            irc_server = IRCServer()
            irc_server.start_server()
        elif option == ord('2'):
            irc_client = IRCClient()
            irc_client.start_client()
        else:
            self.stdscr.addstr("Invalid option. Exiting.\n")
            self.stdscr.refresh()
            self.stdscr.getch()

class IRCServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 6667))
        self.server_socket.listen(5)
        self.clients = []
        self.lock = threading.Lock()

    def broadcast(self, message, sender):
        with self.lock:
            for client in self.clients:
                if client != sender:
                    try:
                        client.send(message.encode('utf-8'))
                    except Exception as e:
                        print(f"Error broadcasting message: {e}")

    def handle_client(self, client_socket):
        try:
            nickname = client_socket.recv(1024).decode('utf-8')
            print(f"User {nickname} has joined the chat.")

            with self.lock:
                self.clients.append((nickname, client_socket))

            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                with self.lock:
                    for client_nickname, client in self.clients:
                        if client != client_socket:
                            try:
                                client.send(f"{nickname}: {message}".encode('utf-8'))
                            except Exception as e:
                                print(f"Error sending message to {client_nickname}: {e}")

        except ConnectionResetError:
            print("Client disconnected.")
        except Exception as e:
            print(f"Error handling client: {e}")

        finally:
            with self.lock:
                for client_nickname, client in self.clients:
                    if client == client_socket:
                        self.clients.remove((client_nickname, client))
                        client_socket.close()
                        print(f"{client_nickname} has left the chat.")
                        break

    def start_server(self):
        print("IRC Server is listening for incoming connections...")
        try:
            while True:
                client_socket, _ = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

class IRCClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = input("Enter the server's IP address: ")
        self.server_port = 6667
        self.nickname = None

    def receive_messages(self):
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                print(message)
        except ConnectionResetError:
            print("Connection has been closed.")
        except Exception as e:
            print(f"Error receiving message: {e}")

    def start_client(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.nickname = input("Enter your nickname: ")
            self.client_socket.send(self.nickname.encode('utf-8'))

            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()

            while True:
                message = input("")
                if message == ":q":
                    break
                self.client_socket.send(message.encode('utf-8'))

        except KeyboardInterrupt:
            print("Client shutting down.")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <option>")
        sys.exit(1)

    if sys.argv[1] == 'server':
        irc_server = IRCServer()
        irc_server.start_server()
    elif sys.argv[1] == 'client':
        irc_client = IRCClient()
        irc_client.start_client()
    else:
        print("Invalid option. Use 'server' or 'client'.")

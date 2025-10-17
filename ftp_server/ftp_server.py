import socket
import os
import threading

class FTPServer:

    def __init__(self, host='127.0.0.1', port=2121):
        self.host = host
        self.port = port
        self.users = {'user': '12345'}
        self.server_socket = None
        self.base_dir = os.path.join(os.getcwd(), "ftp_server_files")
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def start(self):
        """Starts the FTP server and listens for connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[*] FTP Server started on {self.host}:{self.port}")
        print(f"[*] Server directory: {self.base_dir}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

    def handle_client(self, client_socket):
        """Handles a single client connection."""
        try:
            client_socket.send(b'220 Welcome to the Simple FTP Server.\r\n')

            authenticated = False
            current_user = None
            current_dir = self.base_dir
            data_socket = None
            data_host = None
            data_port = None

            while True:
                command_raw = client_socket.recv(1024).decode().strip()
                if not command_raw:
                    break

                parts = command_raw.split(' ', 1)
                command = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ''

                print(f"[*] Received command: {command} {arg}")

                if command == 'USER':
                    current_user = arg
                    client_socket.send(b'331 Username OK, need password.\r\n')
                elif command == 'PASS':
                    if current_user in self.users and self.users[current_user] == arg:
                        authenticated = True
                        client_socket.send(b'230 User logged in, proceed.\r\n')
                    else:
                        client_socket.send(b'530 Login incorrect.\r\n')
                        break
                elif not authenticated:
                    client_socket.send(b'530 Please login with USER and PASS.\r\n')
                elif command == 'QUIT':
                    client_socket.send(b'221 Goodbye.\r\n')
                    break
                elif command == 'PWD':
                    relative_path = os.path.relpath(current_dir, self.base_dir)
                    # On Windows, relpath can return '..' if current_dir is not inside base_dir
                    # which we want to represent as root '/'
                    if relative_path == '.':
                        display_path = '/'
                    else:
                        display_path = '/' + relative_path.replace('\\', '/')
                    client_socket.send(f'257 "{display_path}" is the current directory.\r\n'.encode())
                elif command == 'CWD':
                    new_path = os.path.abspath(os.path.join(current_dir, arg))
                    # Security check: Ensure the new path is within the base directory
                    if os.path.isdir(new_path) and new_path.startswith(os.path.abspath(self.base_dir)):
                        current_dir = new_path
                        client_socket.send(b'250 Directory successfully changed.\r\n')
                    else:
                        client_socket.send(b'550 Failed to change directory.\r\n')
                elif command == 'PORT':
                    parts = arg.split(',')
                    data_host = f"{parts[0]}.{parts[1]}.{parts[2]}.{parts[3]}"
                    data_port = int(parts[4]) * 256 + int(parts[5])
                    client_socket.send(b'200 PORT command successful.\r\n')
                elif command == 'LIST':
                    self._handle_LIST(client_socket, data_host, data_port, current_dir)

                elif command == 'RETR':
                    self._handle_RETR(client_socket, data_host, data_port, current_dir, arg)

                elif command == 'STOR':
                    self._handle_STOR(client_socket, data_host, data_port, current_dir, arg)

                elif command == 'DELE':
                    self._handle_DELE(client_socket, current_dir, arg)

                else:
                    client_socket.send(b'500 Unknown command.\r\n')

        except ConnectionResetError:
            print("[*] Client disconnected abruptly.")
        except Exception as e:
            print(f"[!] An error occurred: {e}")
        finally:
            if 'client_socket' in locals() and client_socket:
                client_socket.close()
            print("[*] Connection closed.")

    def _handle_LIST(self, client_socket, data_host, data_port, current_dir):
        if data_host and data_port:
            client_socket.send(b'150 Here comes the directory listing.\r\n')
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((data_host, data_port))
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                is_dir = 'd' if os.path.isdir(item_path) else '-'
                # A simple ls -l like format
                listing = f"{is_dir}rwxr-xr-x 1 owner group {os.path.getsize(item_path):>12} Oct 15 12:00 {item}\r\n"
                data_socket.send(listing.encode())
            data_socket.close()
            client_socket.send(b'226 Directory send OK.\r\n')
            data_host, data_port = None, None
        else:
            client_socket.send(b'425 Use PORT or PASV first.\r\n')

    def _handle_RETR(self, client_socket, data_host, data_port, current_dir, arg):
        file_path = os.path.abspath(os.path.join(current_dir, arg))
        if os.path.isfile(file_path) and file_path.startswith(os.path.abspath(self.base_dir)):
            if data_host and data_port:
                client_socket.send(b'150 Opening BINARY mode data connection.\r\n')
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((data_host, data_port))
                with open(file_path, 'rb') as f:
                    data_socket.sendfile(f)
                data_socket.close()
                client_socket.send(b'226 Transfer complete.\r\n')
                data_host, data_port = None, None
            else:
                client_socket.send(b'425 Use PORT or PASV first.\r\n')
        else:
            client_socket.send(b'550 File not found.\r\n')

    def _handle_STOR(self, client_socket, data_host, data_port, current_dir, arg):
        file_path = os.path.abspath(os.path.join(current_dir, arg))
        if file_path.startswith(os.path.abspath(self.base_dir)):
            if data_host and data_port:
                client_socket.send(b'150 Ok to send data.\r\n')
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((data_host, data_port))
                with open(file_path, 'wb') as f:
                    while True:
                        data = data_socket.recv(4096)
                        if not data:
                            break
                        f.write(data)
                data_socket.close()
                client_socket.send(b'226 Transfer complete.\r\n')
            else:
                client_socket.send(b'425 Use PORT or PASV first.\r\n')
        else:
            client_socket.send(b'550 Invalid file path.\r\n')

    def _handle_DELE(self, client_socket, current_dir, arg):
        file_path = os.path.abspath(os.path.join(current_dir, arg))
        if file_path.startswith(os.path.abspath(self.base_dir)):
            if os.path.isfile(file_path):
                os.remove(file_path)
                client_socket.send(b'250 File deleted successfully.\r\n')
            else:
                client_socket.send(b'550 File not found.\r\n')
        else:
            client_socket.send(b'550 Insuficient permissions.\r\n')



if __name__ == '__main__':
    server = FTPServer()
    server.start()

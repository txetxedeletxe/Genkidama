from genkidama import connect_to_session

import time

import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    session = connect_to_session("localhost")

    procs = []

    for _ in range(1000):
        proc = session.execute("print(input())")
        proc.stdin.write("Hello World\n".encode())
        proc.wait()
        print(proc.stdout.read().decode(), end="")


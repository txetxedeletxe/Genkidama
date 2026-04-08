from genkidama_session import LocalGenkidamaSession

from testscript import write_matrix
if __name__ == "__main__":

    session = LocalGenkidamaSession()

    # TEST 1: Simple hello world (test stdout)
    proc_helloworld = session.exec("print('Hello World!')")
    print("Process HelloWorld:\n", proc_helloworld.stdout_endpoint.read())


    # TEST 2: Write something to the process (test stdin)
    proc_input = session.exec("print(input())")

    proc_input.stdin_endpoint.write("I read this from stdin!\n")
    proc_input.stdin_endpoint.flush()

    print("Process Input:\n", proc_input.stdout_endpoint.read())

    # TEST 3: Receive error messages (test stderr)
    proc_err = session.exec("raise ValueError('This is a test error!')")
    print("Process Error:\n", proc_err.stderr_endpoint.read())


    # TEST 4: An actual computation problem
    with open("./testscript.py") as f:
        script = f.read()

    proc_compute = session.exec(script)

    # Send a Matrix using stdin
    A = [[2,0],[0,1]]
    B = [[1,0,0],[1,1,0]]

    proc_compute.stdin_endpoint.write(write_matrix(A)+write_matrix(B))
    proc_compute.stdin_endpoint.flush()

    proc_compute.wait()

    print("Process Compute:\n", proc_compute.stdout_endpoint.read())

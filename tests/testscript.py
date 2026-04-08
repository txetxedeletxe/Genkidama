"""Script to be sent to a Donor for execution"""
import time

matrix = list[list[float]]

def read_matrix() -> matrix:
    rows, cols = map(int,input().split(" "))

    A = []
    for i in range(rows):
        A += [list(map(float,input().split(" ")))]

    return A

def write_matrix(A : matrix):

    string = f"{len(A)} {len(A[0])}\n"
    for row in A:
        string = string + " ".join(map(str,row)) + "\n"

    return string

def matmul(A: matrix, B: matrix):
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])

    assert cols_A == rows_B

    C = [[0]*cols_B for _ in range(rows_A)]
    for i in range(rows_A):
        for j in range(cols_B):
            C[i][j] = sum(A[i][k]*B[k][j] for k in range(cols_A))

    return C


if __name__ in ("__main__", "genkidama_session"):

    A = read_matrix()
    B = read_matrix()

    C = matmul(A,B)

    print(write_matrix(C))

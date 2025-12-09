# filename: sat/encoder.py

from typing import List


def var_index(row: int, col: int, num: int) -> int:
    """
    p(row, col, num) önermesini tek bir integer değişkene map ediyor.
    row, col, num: 1..9
    Dönüş: 1..729 arası integer (CNF değişken ID'si)
    """
    return 81 * (row - 1) + 9 * (col - 1) + num


def build_cnf_from_grid(grid: List[List[int]]) -> List[List[int]]:
    """
    9x9 sudoku grid'ini CNF formatına çevirir.
    CNF: clause listesi, her clause bir int literal listesi (örn: [1, -5, 23])

    Kısıtlar:
    1) Her hücrede en az bir sayı
    2) Her hücrede en fazla bir sayı
    3) Her satırda, her sayı tam bir kez
    4) Her sütunda, her sayı tam bir kez
    5) Her 3x3 blokta, her sayı tam bir kez
    6) Verilen ipuçları (clue'lar) sabitlenir
    """
    clauses: List[List[int]] = []

    # 1) Her hücrede en az bir sayı
    for i in range(1, 10):          # row
        for j in range(1, 10):      # col
            clause = [var_index(i, j, n) for n in range(1, 10)]
            clauses.append(clause)

    # 2) Her hücrede en fazla bir sayı (aynı hücrede iki farklı n olamaz)
    for i in range(1, 10):
        for j in range(1, 10):
            for n1 in range(1, 10):
                for n2 in range(n1 + 1, 10):
                    clauses.append([
                        -var_index(i, j, n1),
                        -var_index(i, j, n2)
                    ])

    # 3) Her satırda, her sayı tam bir kez
    # 3a) En az bir kez
    for i in range(1, 10):          # row
        for n in range(1, 10):      # number
            clause = [var_index(i, j, n) for j in range(1, 10)]
            clauses.append(clause)

    # 3b) En fazla bir kez
    for i in range(1, 10):
        for n in range(1, 10):
            for j1 in range(1, 10):
                for j2 in range(j1 + 1, 10):
                    clauses.append([
                        -var_index(i, j1, n),
                        -var_index(i, j2, n)
                    ])

    # 4) Her sütunda, her sayı tam bir kez
    # 4a) En az bir kez
    for j in range(1, 10):          # col
        for n in range(1, 10):      # number
            clause = [var_index(i, j, n) for i in range(1, 10)]
            clauses.append(clause)

    # 4b) En fazla bir kez
    for j in range(1, 10):
        for n in range(1, 10):
            for i1 in range(1, 10):
                for i2 in range(i1 + 1, 10):
                    clauses.append([
                        -var_index(i1, j, n),
                        -var_index(i2, j, n)
                    ])

    # 5) Her 3x3 blokta, her sayı tam bir kez
    for block_row in range(0, 3):
        for block_col in range(0, 3):
            for n in range(1, 10):
                # 5a) En az bir kez
                block_cells = []
                for di in range(0, 3):
                    for dj in range(0, 3):
                        i = 3 * block_row + di + 1
                        j = 3 * block_col + dj + 1
                        block_cells.append(var_index(i, j, n))
                clauses.append(block_cells)

                # 5b) En fazla bir kez
                for idx1 in range(len(block_cells)):
                    for idx2 in range(idx1 + 1, len(block_cells)):
                        clauses.append([
                            -block_cells[idx1],
                            -block_cells[idx2]
                        ])

    # 6) Verilen ipuçları (grid içindeki 0 olmayan sayılar)
    for i in range(1, 10):
        for j in range(1, 10):
            val = grid[i - 1][j - 1]
            if val != 0:
                # Bu hücrede val olmak ZORUNDA
                clauses.append([var_index(i, j, val)])

    return clauses

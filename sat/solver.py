# filename: sat/solver.py

from typing import List, Optional
from pysat.solvers import Glucose3  # python-sat kütüphanesi
from .encoder import var_index


Clause = List[int]
CNF = List[Clause]


def solve_cnf_with_openai(clauses: CNF, api_key: str):
    """
    İsim 'with_openai' ama bu fonksiyonda gerçek bir SAT solver (Glucose3) kullanıyoruz.
    API key imza uyumu için duruyor, burada kullanılmıyor.
    
    Dönüş:
      - None      -> çözümsüz (UNSAT)
      - List[int] -> TRUE olan değişken ID'leri (pozitif literal'lar)
    """

    solver = Glucose3()

    # CNF'yi çözücüye yükle
    for clause in clauses:
        solver.add_clause(clause)

    sat = solver.solve()

    if not sat:
        solver.delete()
        return None

    model = solver.get_model()
    solver.delete()

    # PySAT modeli hem pozitif hem negatif literal içerir.
    # Biz sadece pozitif olanları kullanacağız.
    positive = [lit for lit in model if lit > 0]
    return positive


def model_to_grid(model: List[int]):
    """
    SAT modelinden 9x9 sudoku grid'i üretir.
    model: TRUE literal'ların pozitif ID listesi (1..729 arası)
    """

    grid = [[0 for _ in range(9)] for _ in range(9)]

    for v in model:
        if v <= 0:
            continue

        # var_index(row,col,num) = 81*(row-1) + 9*(col-1) + num
        idx = v - 1
        row = idx // 81        # 0..8
        rem = idx % 81
        col = rem // 9         # 0..8
        num = rem % 9 + 1      # 1..9

        grid[row][col] = num

    return grid

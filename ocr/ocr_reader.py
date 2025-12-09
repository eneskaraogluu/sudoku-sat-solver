# filename: ocr_reader.py

import base64
import io
import json
import re

import cv2
import numpy as np
import requests
from PIL import Image


def _to_base64(img: Image.Image) -> str:
    """Pillow Image -> base64 PNG string."""
    buff = io.BytesIO()
    img.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")


def _find_sudoku_bbox_projection(gray: np.ndarray):
    """
    Grid sınırını 'projeksiyon' ile bul:
    - Threshold + binary_inv
    - Her satır / sütunda kaç piksel dolu, ona bak
    - Yoğunluğun ciddi arttığı bölgeyi sudoku alanı kabul et
    Bu, çizgili ve çizgisiz (renk bloklu) sudoku'larda daha stabil.
    """
    # Hafif blur + Otsu threshold
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # True = “doluluk” (yazı, çizgi vs)
    mask = thresh > 0

    # Satır ve sütun toplam yoğunluğu
    rowsum = mask.sum(axis=1)
    colsum = mask.sum(axis=0)

    # Dış boşluklarda rowsum küçük, sudoku bölgesinde büyük olur
    row_max = rowsum.max()
    col_max = colsum.max()

    # Çok esnek eşik: max'in %15–20'si üstündekileri sudoku kabul et
    row_thr = max(5, int(row_max * 0.18))
    col_thr = max(5, int(col_max * 0.18))

    # Sudoku'ya ait satır/sütun indeksleri
    row_idxs = np.where(rowsum > row_thr)[0]
    col_idxs = np.where(colsum > col_thr)[0]

    if row_idxs.size == 0 or col_idxs.size == 0:
        raise RuntimeError("Projeksiyonla sudoku sınırı bulunamadı.")

    top = int(row_idxs[0])
    bottom = int(row_idxs[-1])
    left = int(col_idxs[0])
    right = int(col_idxs[-1])

    # Azıcık içeri gir (dıştaki gürültüyü azalt)
    pad = 2
    top = max(0, top + pad)
    left = max(0, left + pad)
    bottom = min(gray.shape[0] - 1, bottom - pad)
    right = min(gray.shape[1] - 1, right - pad)

    # Debug için istersen burayı loglayabilirsin
    print(f"BBox (proj): left={left}, top={top}, right={right}, bottom={bottom}")

    return left, top, right, bottom


def sudoku_oku_openai(image_path: str, api_key: str):
    """
    1) Resmi okur, griye çevirir
    2) Projeksiyonla sudoku dikdörtgenini bulur (satır/sütun yoğunluğu)
    3) O dikdörtgeni 9x9 eşit hücreye böler
    4) 81 hücreyi TEK OpenAI chat completion isteği ile OCR eder
    5) 9x9 integer grid döndürür
    """

    # ---- 1. Görüntü oku ----
    orig_bgr = cv2.imread(image_path)
    if orig_bgr is None:
        raise RuntimeError(f"Görsel okunamadı: {image_path}")

    gray = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)

    # ---- 2. Sudoku sınırını projeksiyonla bul ----
    left, top, right, bottom = _find_sudoku_bbox_projection(gray)

    # Sadece sudoku bölgesini al
    grid_bgr = orig_bgr[top:bottom + 1, left:right + 1]

    # Pillow'a çevir
    grid_pil = Image.fromarray(cv2.cvtColor(grid_bgr, cv2.COLOR_BGR2RGB))

    width, height = grid_pil.size
    cell_w = width / 9.0
    cell_h = height / 9.0

    cells_b64 = []
    cell_labels = []

    # ---- 3. 9x9 hücreleri böl ----
    for r in range(9):
        for c in range(9):
            # Hücre koordinatları
            x1 = int(c * cell_w)
            y1 = int(r * cell_h)
            x2 = int((c + 1) * cell_w)
            y2 = int((r + 1) * cell_h)

            # İçeriden hafif kırp (grid çizgilerini azaltmak için)
            padding = max(1, int(min(cell_w, cell_h) * 0.08))
            x1 += padding
            y1 += padding
            x2 -= padding
            y2 -= padding

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            cell = grid_pil.crop((x1, y1, x2, y2))
            cells_b64.append(_to_base64(cell))
            cell_labels.append((r + 1, c + 1))

    # ---- 4. OpenAI'ye tek istek ----
    url = "https://api.openai.com/v1/chat/completions"

    system_prompt = (
        "You are an OCR engine for Sudoku cells. "
        "You will receive 81 small images, each containing exactly one cell "
        "of a Sudoku grid. Your job is ONLY to read digits, not to solve the puzzle.\n\n"
        "For each cell:\n"
        "- If there is a clear printed digit 1–9, output that digit.\n"
        "- If the cell is empty (only grid/background), output 0.\n"
        "- Do NOT infer or guess missing digits.\n\n"
        "Cells are provided row by row from (1,1) to (9,9). "
        "We will label each cell as 'Cell (row,col)' before its image.\n\n"
        "OUTPUT FORMAT (MANDATORY):\n"
        "Return ONLY a pure JSON 9x9 array (list of 9 lists, each with 9 integers). "
        "No explanations, no comments, no code fences."
    )

    content = [{"type": "text", "text": system_prompt}]

    for (r, c), b64 in zip(cell_labels, cells_b64):
        content.append(
            {"type": "text", "text": f"Cell ({r},{c})"}
        )
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64}",
                    "detail": "low",
                },
            }
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": content}
        ],
    }

    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code != 200:
        raise RuntimeError(f"OCR API Error {resp.status_code}: {resp.text}")

    raw = resp.json()["choices"][0]["message"]["content"]

    # ---- 5. JSON array'i çek ----
    m = re.search(r"\[[\s\S]*\]", raw)
    if not m:
        raise RuntimeError(f"OCR yanıtında JSON array bulunamadı:\n{raw}")

    clean = m.group(0)

    try:
        grid = json.loads(clean)
    except Exception as e:
        raise RuntimeError(f"JSON parse hatası: {e}\nHam JSON:\n{clean}")

    # Basit doğrulama
    if not isinstance(grid, list) or len(grid) != 9:
        raise RuntimeError("OCR sonucu 9 satır içermiyor (9x9 değil).")

    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            raise RuntimeError("OCR satırlarından biri 9 eleman içermiyor.")
        for v in row:
            if not isinstance(v, int):
                raise RuntimeError("OCR sonucu içinde integer olmayan eleman var.")

    # Debug için terminale bas
    print("OCR Grid:")
    for r in grid:
        print(r)

    return grid

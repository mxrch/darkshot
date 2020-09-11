from lib.utils import *
from config import cfg

if check_admin():
    check_ocr_langs("tesseract", cfg["tessdata_folder"], cfg["ocr_langs"], download=True)
else:
    print("Please run it with admin rights.")
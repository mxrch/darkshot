from PIL import Image
import pytesseract
from config import cfg
import threading

def ocr(img, lang, tessconfig):
	th_name = threading.current_thread().name
	#print(f"[{th_name}] Conversion...")
	new_size = tuple(cfg["zoomlevel"]*x for x in img.size)
	#print(new_size)	
	img = img.resize(new_size, Image.ANTIALIAS)
	#print(f"[{th_name}] Analyse...")
	text = pytesseract.image_to_string(img, lang=lang, config=tessconfig)
	#print(f"[{th_name}] Je return")
	return text
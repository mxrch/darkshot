import datetime

cfg = dict(

logs_dir = "logs",

min = "l0001",
chars = "0123456789abcdefghijklmnopqrstuvwxyz",

tessdata_folder = "", # If it can't auto guess the tessdata path, put it here
ocr_langs = ["eng", "rus", "ara", "hin"], # See ISO languages codes here => https://cloud.google.com/translate/docs/languages

# Think about the fact that the English is the most efficient (more trained),
# and it works with other languages because they have a lot of characters in common
# (French, Deutsch, Italian, etc..)

keywords_langs = ["fr", "en", "ru", "de", "es", "ar", "it", "pt", "id", "hi"],

# See languages codes here => https://github.com/tesseract-ocr/tessdata/

words_to_translate = ['password', 'credential', 'credentials', 'address', 'email', 'phone number', 'sensitive', 'confidential', 'private'],

regexs = {
    "email": "([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+)",
    "export": "reference={}.*?Found this image <b>(\d*?)<\/b>",
    "creditCard": r"(?:\D|)(\d{12,20}|\d{4}(?: |)\d{4}(?: |)\d{4}(?: |)\d{4}(?: |))(?:\D|)"
},

zoomlevel = 3, # the zoom level of the picture for the OCR

threads_num = 5,
results_delimiter = 100,
thread_retry_timeout = 360, # seconds

sample_pic = "static/images/shot.png", # the pic uploaded each time you're getting the last seen link with "noisy" mode
unwanted_folder = "unwanted",

http_timeout = 20.0, # seconds
http_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'},

stateFile = 'resume.json',
resume_margin = 5, # a margin to save the state only (n + threads_num) links back

banner = 'static/banner.txt'
)
from lib.scrape import download
from lib.analyze import ocr
from lib.detection import Detection
from lib.export import export
from lib.generators import *
from lib.utils import *
from lib.log import log
from config import cfg
import threading
from time import sleep
import time
from termcolor import colored

def process_img(threader, dirname, ocr_langs, words, img, link, lock, imghash, running, tessconfig, debug):

    th_name = threading.current_thread().name
    log(f"Starting the image analyse on {link}", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)

    stats = check_n_update_export(dirname, imghash, link, cfg["regexs"], lock) # We avoid duplicated pictures
    if stats:
        log("This image has already been processed, I'm just updating his stats.", timecode=dirname, cfg=cfg, level="GOOD", hidden=False, debug=debug)
    if not stats and imghash in running:
        log("This image is currently being processed by another thread, I wait for him to finish.", timecode=dirname, cfg=cfg, level="WARNING", hidden=False, debug=debug)
        res = threader.getresultDict()
        
        timeout = cfg["thread_retry_timeout"]
        timeout_start = time.time()
        while imghash not in res.values():
            if time.time() < timeout_start + timeout:
                log("Timeout while retrying, aborting thread.", timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
                break
            sleep(0.5)
            log("Retrying...", timecode=dirname, cfg=cfg, level="WARNING", hidden=False, debug=debug)
            res = threader.getresultDict()
        else:
            log("The another thread finished ! I'm resuming.", timecode=dirname, cfg=cfg, level="GOOD", hidden=False, debug=debug)
        sleep(1)
        stats = check_n_update_export(dirname, imghash, link, cfg["regexs"], lock)
    if not stats:
        stats_list = []
        first_text = None
        for lang in ocr_langs:
            log(f"Starting OCR with {lang.upper()} lang", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)
            text = ocr(img, lang, tessconfig)
            if not first_text:
                first_text = text
            Detect = Detection(words, cfg["regexs"])
            stats = Detect.run(text)
            stats_list.append(stats)
        stats = sum_stats(stats_list)
        if sum([group["count"] for group in stats["groups"].values()]) > 0:
            log("Image analyzed ! I found things !", timecode=dirname, cfg=cfg, level="COOL", hidden=False, debug=debug)
            log(f"{stats}", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)
        else:
            log("Image analyzed ! I found nothing.", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)
        with lock:
            export(dirname, stats, link, imghash, img, first_text)
    #print(stats)
    return {"hash": imghash, "stats": stats}

def process_link(link, client, debug, dirname):
    img = download(link, client, debug, dirname)
    if not img:
        return False
    imghash = image_hash(img)
    return img, imghash
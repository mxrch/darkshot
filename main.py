from lib.get_limit import get_limit
import lib.generators as algos
from lib.utils import *
from config import cfg
from lib.detection import Detection
from lib.translate import translate_keywords
from lib.scrape import *
from pprint import pprint # to remove
import datetime
from lib.export import export
from PIL import Image
import os
from lib.process import process_link
from lib.hthreader import Threader
from lib.threads_manager import re_feed, update_list
from threading import RLock
import traceback
import httpx
from termcolor import colored
from reprint import output
from lib.log import log

def main(threads_num, mode, algostr, debug, to_clean, resume_ro):
    print("")
    dirname = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

    log(f"Debug mode : {'ACTIVATED' if debug else 'DEACTIVATED'}", timecode=dirname, cfg=cfg, level="VALUABLE", hidden=False, debug=debug)
    if algostr.lower() in ["ascending", "descending", "random"]:
        log(f"Using algo {algostr.upper()} for link generation", timecode=dirname, cfg=cfg, level="VALUABLE", hidden=False, debug=debug)
    else:
        log(f"Algo {algostr.upper()} is not recognized. Exiting..", timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
        exit()

    clean(to_clean, cfg, debug, dirname)

    client = httpx.Client(timeout=cfg["http_timeout"], headers=cfg["http_headers"])
    unwanted_pics = gen_unwanted_pics_hashes(cfg["unwanted_folder"])
    ocr_langs, tessconfig = check_ocr_langs("tesseract", cfg["tessdata_folder"], cfg["ocr_langs"]) # We're downloading the missing languages, or not
    check_n_create(os.path.join(os.getcwd(), "output", dirname, "data"))
    text = "Translation of keywords..."
    print(text)
    log(text, timecode=dirname, cfg=cfg, level="VALUABLE", hidden=True, debug=debug)

    words = translate_keywords(cfg["keywords_langs"], cfg["words_to_translate"])
    log(f"{str(words).encode()}", timecode=dirname, cfg=cfg, level="VALUABLE", hidden=True, debug=debug)
    initial_output_len = get_initial_output_len(words, cfg)

    print("Getting the last seen link...")
    if mode.lower() in ["stealth", "noisy"]:
        log(f"Selecting mode {mode.upper()} for getting the last seen link", timecode=dirname, cfg=cfg, level="VALUABLE", hidden=False, debug=debug)
    else:
        log(f"Mode {mode.upper()} incorrect for getting the last seen link. Exiting..", timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
        exit()
    limit = get_limit(mode, client)
    print("=> " + limit+"\n")
    log(f"Last seen link: {limit}", timecode=dirname, cfg=cfg, level="VALUABLE", hidden=True, debug=debug)

    text = f"Starting Darkshot with {threads_num} threads...\n"
    print("[+] "+text)
    log(text, timecode=dirname, cfg=cfg, level="VALUABLE", hidden=True, debug=debug)

    algo = getattr(algos, algostr.lower())
    if resume_ro:
        resume = {"read": True, "write": False}
    else:
        resume = {"read": True, "write": True}

    resumeRW = resume["read"] and resume["write"]
    if algo.__name__ == "random" and resumeRW: # Exception
        log("Random algorithm is not compatible with RW resume, so I'm switching to read-only resume mode.", timecode=dirname, cfg=cfg, level="WARNING", hidden=False, debug=debug)
        resume["write"] = False
        resumeRW = resume["read"] and resume["write"]

    data = {}
    hashes = None
    stats = None
    stats_list = None
    lock = RLock() # We avoid threads to modify files at the same time
    resume_list = []
    resume_margin = threads_num + cfg["resume_margin"]
    try:
        threader = Threader(threads_num)
        index = 1
        count = 1
        listening = {}
        running = set()
        with output(initial_len=initial_output_len) as output_lines:
            for new_data, link in run_algo(algo=algo, min=cfg["min"], limit=limit, chars=cfg["chars"], stateFile=cfg["stateFile"], resume=resume):
                data = new_data
                if resumeRW:
                    resume_list = update_resume_list(resume_list, link, resume_margin)
                    data = update_resume_data(algo, data, resume_list)
                out = process_link(link, client, debug, dirname)
                if not out:
                    continue
                img, imghash = out
                if imghash in unwanted_pics:
                    log(f"Unwanted image detected at link {link}, passing", timecode=dirname, cfg=cfg, level="WARNING", hidden=False, debug=debug)
                    continue
                else:
                    log(f"--------COUNT {count} | INDEX {index}--------", timecode=dirname, cfg=cfg, level="INTERESTING", hidden=False, debug=debug)
                    log(f"Processing link: {link} - hash: {imghash}", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)
                listening[index] = None
                outputs = re_feed(threader, dirname, ocr_langs, words, img, link, lock, imghash, running, tessconfig, debug, index)
                running.add(imghash)
                log(f"Images hashes currently being processed: {running}", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)

                if index % cfg["results_delimiter"] == 0:
                    log("Clearing threads, next delimitation", timecode=dirname, cfg=cfg, level="GOOD", hidden=False, debug=debug)
                    index = 1
            
                    threader.finishJobs()
                    outputs = threader.getresultDict()

                    # We restart the threads
                    threader = Threader(threads_num)
                    listening = {}
                    running = set()

                else:
                    index += 1
                    
                tmp_out = update_list(listening, outputs)
                listening = tmp_out["listening"]
                hashes = tmp_out["new"]["hashes"]
                stats_list = tmp_out["new"]["stats"]
                if hashes:
                    running = update_running(hashes, running)

                if not debug:
                    if stats_list:
                        if len(stats_list) > 1:
                            new_stats = sum_stats(stats_list)
                        else:
                            new_stats = stats_list[0]
                        if stats:
                            stats = sum_stats([stats, new_stats])
                        else:
                            stats = new_stats
                    
                    if stats:
                        out = output_print(stats, link, count).split('\n')
                        for nb,line in enumerate(out):
                            output_lines[nb] = line
                        stats_list = []
                
                count += 1
            
        if resumeRW:
            log("Finished !", timecode=dirname, cfg=cfg, level="GOOD", hidden=False, debug=debug)
            save_state(data, algo, 'Finished', stateFile)
    except:
        if debug:
            traceback.print_exc()
        reason = sys.exc_info()[0].__name__
        if reason == "TesseractNotFound":
            print("Please add Tesseract to the PATH, or add his path manually in the script.")
        elif reason == "TessdataFolderNotFound":
            print("The tessdata folder is apparently not at the base of the Tessdata installation.\nPlease specify it manually in the script.")
        elif reason == "AlgoNotFound":
            print("The specified algorithm was not found.\nPlease use ascending, descending or random.")
        elif reason != "SystemExit":
            if resumeRW:
                save_state(data, algo, reason, cfg["stateFile"])
            else:
                if reason == "KeyboardInterrupt":
                    print("\nCTRL+C Detected.\nExiting...")
                    log("CTRL+C Detected, Exiting.", timecode=dirname, cfg=cfg, level="VALUABLE", hidden=True, debug=debug)
                else:
                    print(f"\nError detected ({reason}).\nExiting...")
                    log(f"Error detected ({reason}). Exiting.", timecode=dirname, cfg=cfg, level="ERROR", hidden=True, debug=debug)
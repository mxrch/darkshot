import httpx
import json
import hashlib
from io import BytesIO
from os.path import isfile, isdir
import sys
from lib.errors import *
import os, ctypes
from os import listdir, makedirs
import shutil
from time import sleep
import re
from glob import glob
from pathlib import Path
from PIL import Image
import imghdr
from lib.detection import Detection
from beautifultable import BeautifulTable
from termcolor import colored
from shutil import rmtree
from lib.log import log


def run_algo(algo, min, limit, chars, stateFile, resume=True):
    """A wrapper function to launch the algo generators, handling resume"""
    name = algo.__name__.lower()
    algos = ["ascending", "descending", "random"]
    if name not in algos:
        raise("AlgoNotFound")
    if resume["read"]:
        if isfile(stateFile):
            f = open(stateFile, 'r')
            try:
                data = json.loads(f.read())
            except Exception as e:
                print("The resume file is corrupted. ({})".format(e.__class__.__name__))
                print("Do you want me to :")
                choice = input("1. Create a new fresh resume file\n2. Let you fix it manually\n> ")
                if choice == "1":
                    new = True
                elif choice == "2":
                    print("\nSee you very soon !")
                    f.close()
                    exit()
            else:
                new = False
            f.close()
        else:
            new = True

        if new:
            data = {
                "ascending": {"start": min},
                "descending": {
                    "last": {},
                    "remaining": []
                }
            }
        # LAUNCH
        if name == "ascending":
            end = False
            min = data["ascending"]["start"]
            while 1:
                next = False
                to_remove = []
                for i in algo(limit, chars, min=min):
                    data["ascending"]["start"] = i
                    #Check
                    for d in data["descending"]["remaining"]:
                        if i == d["end"]:
                            #print("GOOD")
                            min = d["start"]
                            next = True
                            to_remove.append(d)
                            break
                    if i == limit:
                        yield (data, i)
                        end = True
                        break
                    elif next:
                        for t in to_remove:
                            data["descending"]["remaining"].remove(t)
                        break
                    else:
                        yield (data, i)
                if end:
                    break

        elif name == "descending":
            min = data["ascending"]["start"]
            data["descending"]["last"]["start"] = limit
            end = False
            while 1:
                next = False
                to_remove = []
                for i in algo(limit, chars, min=min):
                    data["descending"]["last"]["end"] = i
                    #Check
                    for d in data["descending"]["remaining"]:
                        if i == d["start"]:
                            #print("GOOD")
                            limit = d["end"]
                            next = True
                            to_remove.append(d)
                            break
                    if i == min:
                        end = True
                        break
                    elif next:
                        for t in to_remove:
                            data["descending"]["remaining"].remove(t)
                        break
                    else:
                        yield (data, i)
                if end:
                    break

        elif name == "random":
            for i in algo(limit, chars, min=data["ascending"]["start"]):
                next = False
                for d in data["descending"]["remaining"]:
                    if isBetween(chars, d["start"], d["end"], i):
                        next = True
                        break
                if not next:
                    yield (data, i)
                    
    else:
        for i in algo(limit, chars, min):
            yield ({}, i)

def save_state(data, algo, reason, stateFile):
    name = algo.__name__.lower()
    if reason == "KeyboardInterrupt":
        print("\nCTRL+C Detected.\nSaving state...", end='\r')
    elif reason == "Finished":
        print("\nYou scraped it all off !\nSaving state...", end='\r')
    elif reason:
        print("\nError detected ({}).\nSaving state...".format(reason), end='\r')
    if data:
        if name == "descending":
            data["descending"]["remaining"].append(data["descending"]["last"])
            data["descending"]["last"] = {}
        with open(stateFile, 'w') as f:
            f.write(json.dumps(data))
    print("State saved ! ({})      ".format(stateFile))
    exit()

def compare(chars, str1, str2):
    """Returns the higher string, based on the chars list given"""
    if len(str1) > len(str2):
        return str1
    elif len(str2) > len(str1):
        return str2
    else:
        nbs1 = [chars.index(c) for c in str1]
        nbs2 = [chars.index(c) for c in str2]
        for nb1, nb2 in zip(nbs1, nbs2):
            if nb1 > nb2:
                return str1
            elif nb2 > nb1:
                return str2
        return False

def isBetween(chars, str1, str2, target):
    """Returns True if the target is between str1 and str2 (excluding extremities)"""
    first_check = compare(chars, str1, target)
    second_check = compare(chars, str2, target)
    if not first_check or not second_check:
        return False
    elif (first_check == str1 and second_check == str2) or (first_check == target and second_check == target):
        return False
    else:
        return True

def check_req(req):
    if not req.status_code:
        raise RequestFailed
    elif req.status_code != 200:
        raise RequestIssue

def check_admin():
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    finally:
        return is_admin

def check_n_create(path):
    if not isdir(path):
        makedirs(path)

def image_hash(img):
    output = BytesIO()
    img.save(output, format='PNG')
    hash = hashlib.md5(output.getvalue()).hexdigest()
    return hash

def sum_stats(stats_list):
    base_res = None
    for res in stats_list:
        if not base_res:
            base_res = res
            continue
        base_res["blacklists_catch"] += res["blacklists_catch"]
        for name, group in res["groups"].items():
            base_res["groups"][name]["count"] += group["count"]
            base_res["groups"][name]["detected"].extend(group["detected"])

    return base_res

def check_ocr_langs(tesseract_path, tessdata_path, ocr_langs, download=False):
    if tessdata_path:
        if isdir(tessdata_path):
            path = tessdata_path
        else:
            raise TessdataFolderNotFound
    else: # If tessdata path is not specified, we try to guess it with the tesseract path
        if tesseract_path == "tesseract": # pytesseract.pytesseract.tesseract_cmd
            path = shutil.which("tesseract")
            if not path:
                raise TesseractNotFound
        else:
            path = tesseract_path
        firstpath = "\\".join(path.split("\\")[:-1])+"\\tessdata\\"
        possibles_paths = [
            firstpath,
            "/*/tesseract-ocr/tessdata/",
            "/usr/share/tesseract-ocr/*/tessdata/",
            "/usr/local/share/tesseract-ocr/*/tessdata/",
            "/usr/share/tessdata/",
            "/usr/local/share/tessdata/",
            "/usr/local/Cellar/tesseract/*/share/tessdata/"
        ]
        for p in possibles_paths:
            _p = glob(p)
            if _p:
                path = _p[0]
                break
        else:
            raise TessdataFolderNotFound
    # Check
    files = listdir(path)
    langs_installed = [filename.replace(".traineddata", "") for filename in files if ".traineddata" in filename]
    not_here = []
    for lang in ocr_langs:
        if lang not in langs_installed:
            not_here.append(lang)
    if not_here:
        req = httpx.get("https://api.github.com/repos/tesseract-ocr/tessdata/contents")
        check_req(req)
        r_files = json.loads(req.text)
        remote_langs = [filename["name"].replace(".traineddata", "") for filename in r_files if ".traineddata" in filename["name"]]
        to_download = []
        for d in not_here:
            if d not in remote_langs:
                raise OcrLangNotFound("The OCR lang \"{}\" can't be found installed or in the git repo.\nFind them at : https://github.com/tesseract-ocr/tessdata".format(d))
            else:
                to_download.append(d)
        print("The following langs were requested but not found installed.")
        print("".join(["- " + lang + "\n" for lang in to_download]))
        if download:
            for nb, d in enumerate(to_download):
                print("Downloading {}.traineddata ...  ({}/{})          ".format(d, nb+1, len(to_download)), end='\r')
                req = httpx.get("https://raw.githubusercontent.com/tesseract-ocr/tessdata/master/{}.traineddata".format(d))
                check_req(req)
                open(path + d + ".traineddata", 'wb').write(req.content)
            print("All OCR langs requested have been downloaded !              ")
        else:
            exit("Please either run check_ocr_langs.py as admin to download & install missing OCR langs, \nor editing config.py to remove unwanted OCR langs.")
    else:
        if download:
            print("All OCR langs are installed correctly.")

    #path = path[:-1] if path[-1]=="\\" else path
    path = path.replace("\\", "/")
    tessconfig = f'--tessdata-dir "{path}"'
    return ocr_langs, tessconfig

def find_image_occurences(text, hash, regexs):
    count = int(re.compile(regexs["export"].format(hash)).findall(text)[0])
    return count

def update_image_occurences(path, hash, regexs):
    text = ""
    with open(path, 'r', encoding='latin-1') as f:
        text = f.read()
    previous_number = find_image_occurences(text, hash, regexs)
    with open(path, 'w', encoding='latin-1') as f:
        f.write(re.sub(r'(reference={}.*?Found this image)( <b>\d*?</b> )(time|times)(<\/h5>)'.format(hash), r'\1 <b>{}</b> times\4'.format(previous_number + 1), text))

def check_hash(dirname, hash):
    pwd = os.getcwd()
    path = os.path.join(pwd, "output", dirname, "data")
    groups = []
    groups_dirs = os.listdir(path)
    for group in groups_dirs:
        hashes = os.listdir(os.path.join(path, group))
        if hash in hashes:
            groups.append(group)
            continue
    return groups

def check_n_update_export(dirname, hash, link, regexs, lock):
    in_groups = check_hash(dirname, hash)
    if in_groups:
        basepath = os.path.join(os.getcwd(), "output", dirname)
        stats = None
        with lock:
            for group in in_groups:
                path = os.path.join(basepath, "data", group, hash)
                with open(os.path.join(path, 'links.txt'), 'a') as f:
                    f.write(f"https://prnt.sc/{link}\n")
                if group == in_groups[0]:
                    with open(os.path.join(path, 'stats.txt'), 'r') as f:
                        stats = json.loads(f.read())
                update_image_occurences(os.path.join(basepath, group+".html"), hash, regexs)
        return stats
    return False

def update_running(hashes, running):
    for hash in hashes:
        if hash in running:
            running.remove(hash)
    return running

def gen_unwanted_pics_hashes(basepath):
    pics = []
    for root, dirs, files in os.walk(basepath):
        for file in files:
            filepath = Path(root+"/"+file)
            if imghdr.what(filepath): # We verify if it's an image
                pics.append(filepath)
    hashes = []
    for pic in pics:
        img = Image.open(Path(pic))
        hash = image_hash(img)
        hashes.append(hash)
    return hashes

def update_resume_list(resume_list, link, resume_margin):
    if len(resume_list) >= resume_margin:
        resume_list = resume_list[1:]
    resume_list.append(link)
    return resume_list

def update_resume_data(algo, data, resume_list):
    if resume_list:
        name = algo.__name__.lower()
        if name == "ascending":
            data["ascending"]["start"] = resume_list[0]
        elif name == "descending":
            data["descending"]["last"]["end"] = resume_list[0]
    return data

def get_initial_output_len(words, cfg):
    Detect = Detection(words, cfg['regexs'])
    stats = Detect.run('')
    
    banner = ""
    with open(cfg["banner"], 'r') as f:
        banner = f.read()

    return len(banner.split('\n')) + len(stats['groups']) * 2 + 5

def output_print(stats, link, count):
    groups_len = len(stats["groups"])

    space = " "*10
    banner = ""
    with open("static/banner.txt", "r") as f:
        banner = f.read()
    banner = '\n\n'+space+banner.replace('\n', f'\n{space}')+'\n'

    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_BOX_ROUNDED)
    table.columns.header = [colored(head, attrs=['bold']) for head in ["Groups", "Detected pics"]]

    for group_name,group in stats["groups"].items():
        table.rows.append([group_name.capitalize(), group["count"]])

    table.columns.append(["/"]*groups_len, header="/")

    table.columns.append([stats["blacklists_catch"]]+[""]*(groups_len-1), header=colored("Blacklist catch", attrs=['bold']))
    table.columns.append([link]+[""]*(groups_len-1), header=colored("Current link", attrs=['bold']))
    table.columns.append([count]+[""]*(groups_len-1), header=colored("Count", attrs=['bold']))
    return banner + str(table)

def recursive_rm(path):
    for path in Path(path).iterdir():
        if path.is_file() and ".keep" not in str(path):
            path.unlink()
        elif path.is_dir():
            rmtree(path)

def clean(to_clean, cfg, debug, dirname):
    if to_clean:
        to_clean = to_clean.split(',')
        log(f'Cleaning : {to_clean}', timecode=dirname, cfg=cfg, level="VALUABLE", hidden=False, debug=debug)
        authorized = ["resume", "logs", "exports"]
        for target in to_clean:
            if target not in authorized:
                log(f'Target "{target}" is not recognized for cleaning. Exiting..', timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
                exit()

        for target in to_clean:
            if target == "resume":
                tfile = Path(cfg["stateFile"])
                if tfile.is_file():
                    tfile.unlink()
            elif target == "logs":
                recursive_rm("logs")
            elif target == "exports":
                recursive_rm("output")
    else:
        log(f'Nothing to clean', timecode=dirname, cfg=cfg, level="VALUABLE", hidden=True, debug=debug)
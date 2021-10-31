import httpx
from scrapy.selector import Selector
from PIL import Image
import PIL
from io import BytesIO
from termcolor import colored
from lib.log import log
from config import cfg

def check_req(req, debug, dirname):
    if not req.status_code:
        log("Request error.", timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
        return False
    elif req.status_code != 200:
        log("Request error : " + str(req.status_code), timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
        return False
    else:
        return True

def download(link, client, debug, dirname):
    try:
        req = client.get("https://prnt.sc/{}".format(link))
        if not check_req(req, debug, dirname):
            return False

        body = Selector(text=req.text)
        imgur = body.css('img.screenshot-image::attr(src)').extract()[0]

        if not imgur or "//st.prntscr.com" in imgur: # This link is buggy and is returned when the image got removed
            log(f"Picture removed / buggy link for {link}, passing.", timecode=dirname, cfg=cfg, level="LILWARN", hidden=False, debug=debug)
            return False
        elif imgur[:2] == "//":
            imgur = "http:"+imgur
        req = client.get(imgur)
        if not check_req(req, debug, dirname):
            return False
        log(f"Real image link for {link} => {imgur}", timecode=dirname, cfg=cfg, level="INFO", hidden=False, debug=debug)
    except Exception as e:
        log(f"An error occured while requesting {link} :\n{e}", timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
        return False

    try:
        img = Image.open(BytesIO(req.content))
    except PIL.UnidentifiedImageError:
        log(f"An error occured while converting this link to an image object : {imgur}", timecode=dirname, cfg=cfg, level="ERROR", hidden=False, debug=debug)
        return False

    return img
import httpx
import json
from config import cfg
from pprint import pprint

def check_valid_limit(link, client):
    tocheck = '<img class="no-click screenshot-image"'
    req = client.get("https://prnt.sc/"+link)
    if req.status_code == 200:
        if tocheck in req.text:
            return True
    return False

def get_limit(mode, client):
    def stealth():
        req = client.get("https://prntscr.com/twitter.json")
        if req.status_code != 200:
            exit("Error.")

        data = json.loads(req.text)

        for status in data["statuses"]:
            for url in status["entities"]["urls"]:
                if "prnt.sc/" in url["expanded_url"] or "prntscr.com/" in url["expanded_url"]:
                    link = url["expanded_url"].split('/')[-1]
                    if link and check_valid_limit(link, client):
                        return link

    def noisy():
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
        files = {'image': ('shot.png', open(cfg["sample_pic"], 'rb'), 'image/png')}
        req = client.post("https://prntscr.com/upload.php", files=files, headers=headers)
        out = json.loads(req.text)
        if req.status_code != 200:
            if "cloudflare" in req.text.lower():
                print("Cloudflare protection detected, I'm basculing on stealth mode")
            else:
                print(f"Error : Status code {str(req.status_code)}")
            return False
        if out["status"] != "success":
            print(f'Error : Status code {out["data"]}')
            return False
        link = out["data"].split("/")[-1]
        return link
    
    if mode=="stealth":
        out = stealth()
    elif mode=="noisy":
        out = noisy()
        if not out:
            out = stealth()
    return out
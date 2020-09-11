from lib.process import process_img
from lib.hthreader import Threader
from time import sleep


def re_feed(threader, dirname, ocr_langs, words, img, link, lock, imghash, running, tessconfig, debug, index):
	while threader.getEmptyThreadId() == -1:
		sleep(0.25)
	threader.feed(process_img, {"threader": threader, "dirname": dirname, "ocr_langs": ocr_langs, "words": words, "img": img, "link": link, "lock": lock, "imghash": imghash, "running": running, "tessconfig": tessconfig, "debug": debug}, index)
	sleep(1)
	return threader.getresultDict()

def update_list(listening, res):
	out = {"listening": {}, "new": {"hashes": [], "stats": []}}
	for key, value in res.items():
		if value:
			out["new"]["hashes"].append(value["hash"])
			out["new"]["stats"].append(value["stats"])
		else:
			out["listening"][key] = value
	return out
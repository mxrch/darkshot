from lib.utils import check_n_create
from static.templates.parts import top_part, result_part
from os import getcwd
from os.path import join as pathjoin
from os.path import isfile
import json

def export(dirname, stats, link, imghash, img, text):
    max = sorted([group["count"] for group in stats['groups'].values()], reverse=True)[0]
    if max >= 1:
        pwd = getcwd()
        basepath = pathjoin(pwd, "output")
        path = pathjoin(basepath, dirname)
        thead = [groupname for groupname in stats["groups"].keys() if stats["groups"][groupname]["count"] >= 1]
        tbody = [[stats["groups"][groupname]["detected"][count] if stats["groups"][groupname]["count"] > count else {"lang": "", "word":"/"} for groupname in thead] for count in range(max)]
        for groupname, group in stats["groups"].items():
            if group["detected"]:
                itempath = pathjoin(path, "data/{}/{}".format(groupname.lower(), imghash))
                check_n_create(itempath)
                img.save(itempath+"/image.png", format='PNG')
                with open(itempath+"/raw.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                with open(itempath+"/links.txt", "w", encoding="utf-8") as f:
                    f.write(f"https://prnt.sc/{link}\n")
                with open(itempath+"/stats.txt", "w", encoding="utf-8") as f:
                    f.write(json.dumps(stats))

                htmlfile = path+"/"+groupname+".html"
                if not isfile(htmlfile):
                    with open(htmlfile, 'w', encoding="utf-8") as f:
                        f.write(top_part.format(
                            "file:///"+pwd+"/",
                            "file:///"+pwd+"/",
                            "file:///"+pwd+"/",
                            "file:///"+pwd+"/",
                            "file:///"+pwd+"/",
                            "file:///"+pwd+"/",
                            "file:///"+pwd+"/",
                            groupname.capitalize()
                        ))

                thead_str = ""
                for title in thead:
                    thead_str += "<th>{}</th>\n".format(title.capitalize())
                tbody_str = ""
                for row in tbody:
                    tbody_str += "<tr>\n"
                    for item in row:
                        if item["lang"]:
                            word = "{} [{}]".format(item["word"], item["lang"].lower())
                        else:
                            word = item["word"]
                        tbody_str += "<td>{}</td>\n".format(word)
                    tbody_str += "<tr>\n"

                with open(htmlfile, 'a', encoding="utf-8") as f:
                    f.write(result_part.format(
                        link,
                        link,
                        imghash,
                        "file:///"+itempath+"/image.png",
                        "file:///"+itempath+"/image.png",
                        imghash,
                        thead_str,
                        tbody_str,
                        "file:///"+itempath+"/raw.txt",
                        "file:///"+itempath+"/links.txt"
                    ))
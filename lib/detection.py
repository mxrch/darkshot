import re

import luhn


class Detection():
    # Functions
    def updateState(self, group, word, lang, detec_state):
        detec_state["groups"][group]["count"] += 1
        detec_state["groups"][group]["detected"].append(
            {
                "lang": lang,
                "word": word
            }
        )
        return detec_state

    def genBlacklists(self, base):
        blacklist_groups = {
            "credentials": [],
            "personal": [],
            "banking": [],
            "confidential": [],
        }
        blacklists = {"base": {word:False for word in self.base_blacklist},
                    "groups": {name:{word:False for word in group} for name, group in blacklist_groups.items()}}
        return blacklists

    def blacklisted(self, blacklists, group_name, text, detec_state):
        detected = False
        for name, blacklist in blacklists.items():
            if name == "base":
                for word, state in blacklist.items():
                    if word.lower() in text:
                        detected = True
                        if not state:
                            detec_state["blacklists_catch"] += 1
                            blacklists[name][word] = True
            elif name == "groups":
                for groupname, group in blacklist.items():
                    for word, state in group.items():
                        if word.lower() in text:
                            detected = True
                            if not state:
                                detec_state["blacklists_catch"] += 1
                                blacklists[name][groupname][word] = True

        return {"detected": detected, "blacklists": blacklists, "state": detec_state}

    def tradWrapper(self, detect_func, group, words, text, detec_state):
        words_cache = []
        for lang, trads in words.items():
            for trad in trads:
                if trad in words_cache:
                    continue
                detec_state = detect_func(group=group, word=trad, lang=lang, text=text, detec_state=detec_state)
                words_cache.append(trad)
        return detec_state

    # Detection functions
    def basicDetection(self, group, word, lang, text, detec_state):
        if word.lower() in text:
            return self.updateState(group=group, word=word, lang=lang, detec_state=detec_state)
        return detec_state

    def isolatedDetection(self, group, word, lang, text, detec_state):
        """Check if the word is not a substring of another word"""
        if word.lower() in text:
            pos = text.index(word.lower())
            left = False
            right = False
            if pos == 0 or not text[pos-1].isalpha():
                left = True
            if pos == (len(text) - len(word)) or not text[pos+len(word)].isalpha():
                right = True
            if left and right:
                return self.updateState(group=group, word=word, lang=lang, detec_state=detec_state)
        return detec_state

    def regexDetection(self, group, regex, text, detec_state):
        res = re.compile(regex).findall(text)
        if res:
            for substring in res:
                detec_state = self.updateState(group=group, word=substring, lang="", detec_state=detec_state)
        return detec_state

    def creditCardDetection(self, group, regex, lang, text, detec_state):
        res = re.compile(regex).findall(text)
        if res:
            for cb in res:
                sanatized = cb.replace(' ', '')
                if not sanatized.startswith("0") and luhn.verify(sanatized):
                    detec_state = self.updateState(group=group, word=cb, lang="", detec_state=detec_state)
        return detec_state

    # Groups
    def credentials(self, text, words, regexs, detec_state):
        group_name = "credentials"

        detec_state = self.tradWrapper(self.basicDetection, group_name, words["password"], text, detec_state)
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["credential"], text, detec_state)
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["credentials"], text, detec_state)
        detec_state = self.isolatedDetection(group_name, "API", "", text, detec_state)

        return detec_state
    
    def personal(self, text, words, regexs, detec_state):
        group_name = "personal"
        
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["email"], text, detec_state)
        detec_state = self.regexDetection(group_name, regexs["email"], text, detec_state)
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["address"], text, detec_state)
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["phone number"], text, detec_state)

        return detec_state

    def banking(self, text, words, regexs, detec_state):
        group_name = "banking"
        
        detec_state = self.creditCardDetection(group_name, regexs["creditCard"], "", text, detec_state)
        detec_state = self.isolatedDetection(group_name, "IBAN", "", text, detec_state)
        detec_state = self.isolatedDetection(group_name, "RIB", "", text, detec_state)
        detec_state = self.isolatedDetection(group_name, "BIC", "", text, detec_state)
        detec_state = self.isolatedDetection(group_name, "SEPA", "", text, detec_state)

        return detec_state

    def confidential(self, text, words, regexs, detec_state):
        group_name = "confidential"
        
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["confidential"], text, detec_state)
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["private"], text, detec_state)
        detec_state = self.tradWrapper(self.basicDetection, group_name, words["sensitive"], text, detec_state)

        return detec_state

    def __init__(self, words, regexs):
        self.base_blacklist = [] # Add your blacklist here
        #self.base_blacklist = ["royal-crypto", "royalcrypto", "bit-trading", "jiratrade", "traderce", "btc-ex", "btcx", "bittrading", "sellbuy-btc", "crypto-trade24"]
        self.groups = [self.credentials, self.banking, self.personal, self.confidential] # Add your groups here

        self.words = words
        self.regexs = regexs

    # Main
    def run(self, text):
        text = text.lower()
        blacklists = self.genBlacklists(self.base_blacklist)
        detec_state = {"blacklists_catch": 0, "groups": {g.__name__.lower(): {"count": 0, "detected":[]} for g in self.groups}}
        for group in self.groups:
            tmp = self.blacklisted(blacklists, group.__name__.lower(), text, detec_state)
            blacklists = tmp["blacklists"]
            detec_state = tmp["state"]
            if tmp["detected"]:
                continue
            else:
                detec_state = group(text, self.words, self.regexs, detec_state)

        return detec_state

from google_trans_new import google_translator
from pprint import pprint

def translate_keywords(keywords_langs, words_to_translate):
    words = {word: {lang: [] for lang in keywords_langs} for word in words_to_translate}
    translator = google_translator()
    for word in words.keys():
        for code in words[word].keys():
            translation = translator.translate(word, lang_tgt=code)
            words[word][code].append(translation)

    #pprint(words) # If you want to debug the translated words, uncomment it

    # Custom traductions, like acronyms
    try:
        if "fr" in keywords_langs:
            words["password"]["fr"].append("mdp")
            words["credential"]["fr"].remove("accréditation")
            words["credential"]["fr"].append("identifiant")
    except (ValueError, KeyError):
        pass

    return words
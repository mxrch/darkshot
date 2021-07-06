#from google_trans_new import google_translator
from pprint import pprint

def translate_keywords(keywords_langs, words_to_translate):
    words = {word: {lang: [] for lang in keywords_langs} for word in words_to_translate}

    for word in words.keys():
        for code in words[word].keys():
            translation = word
            words[word][code].append(translation)

    #pprint(words) # If you want to debug the translated words, uncomment it

    return words
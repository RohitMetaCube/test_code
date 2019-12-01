import re
import nltk
from nltk.stem import WordNetLemmatizer
from collections import OrderedDict
import unidecode

replacing_strings = {
    "e": "east",
    "s": "south",
    "w": "west",
    "n": "north",
    "bch": "beach",
    "afb": "air force base",
    "pt": "point",
    "hts": "heights",
    "jct": "junction",
    "lk": "lake",
    "st": "saint"
}
ignore_suffixes = set([
    "inc", "corporation", "llc", "corp", "ltd", "co", "company",
    "incorporated", "llp", "com", "limited", "pvt", "pvt ltd", "ltd corp",
    "corp ltd", "cos"
])

ignore_words = set(["the", "and", "of", "at"])
# singular_words = set(["us"])
replacement_dict = {
    "united states": "us",
    "7 eleven": "7eleven",
    "hp": "hewlettpackard",
    "hewlett packard": "hewlettpackard",
    "advanced micro devices": "amd",
    "us postal service": "usps",
    "us post office": "usps",
    "united parcel service": "ups",
    "us poster services": "usps",
    "us air force": "usaf",
    'null': "",
    'retired': "",
    'semiretired': "",
    'semi retired': "",
    'none': "",
    "self": "",
    "self employed": "",
    "independent": "",
    "freelance": "",
    "freelance work": "",
    "selfemployed": "",
    "self employed contractor": "",
    "self employed consultant": "",
    "self contractor": "",
    "self employee": "",
    "ownerself": "",
    "owner self": "",
    "international business machine": "ibm",
    "ctr": "center",
    "inst": "institute",
    "univ": "university",
    "lib": "library",
    "lab": "laboratory"
}

wnl = WordNetLemmatizer()


def isplural(word):
    lemma = wnl.lemmatize(word, 'n')
    plural = True if word is not lemma else False
    return plural, lemma


def singularize(string):
    tokens = nltk.word_tokenize(string)
    new_tokens = []
    for token in tokens:
        if len(token) < 5:
            new_tokens.append(token)
        else:
            status, lemma = isplural(token)
            new_tokens.append(lemma)
    return ' '.join(new_tokens)


new_replacement_dict = {}
for k, v in replacement_dict.items():
    new_replacement_dict[singularize(k)] = singularize(v)
replacement_dict = OrderedDict(
    (r"\b{}\b".format(k), r"{}".format(v))
    for k, v in sorted(
        new_replacement_dict.items(),
        key=lambda k: (len(k[0].split()), len(k[0])),
        reverse=True))


def cnv(text, replacement_character=' '):
    if isinstance(text, (float, int)):
        return text
    elif text:
        return ''.join(
            [i if ord(i) < 128 else replacement_character for i in text])
    else:
        return ''


def remove_suffix(organization_name):
    organization_name = organization_name.strip()
    tokens = re.split("\W*", organization_name)
    if organization_name:
        n_gram_suffixes = set()
        organization_tokens = tokens
        for i in range(len(organization_tokens)):
            n_gram_suffixes.add(" ".join(organization_tokens[i:]).strip())
        n_gram_suffixes.intersection_update(ignore_suffixes)
        while n_gram_suffixes:
            rep = n_gram_suffixes.pop()
            pattern = "\W*".join(token for token in rep.split())
            organization_name = re.sub(r'\b{}\b'.format(pattern), r'',
                                       organization_name.strip())
            n_gram_suffixes = set()
            organization_tokens = re.split("\W*", organization_name.strip())
            for i in range(len(organization_tokens)):
                n_gram_suffixes.add(" ".join(organization_tokens[i:]).strip())
            n_gram_suffixes.intersection_update(ignore_suffixes)
    return organization_name


def remove_tokens(organization_name):
    tokens = organization_name.split()
    new_tokens = []
    for token in tokens:
        if token not in ignore_words:
            new_tokens.append(token)
    return ' '.join(t for t in new_tokens)


def combine_single_characters(organization_name):
    return re.sub(r"\b(\w{1,2})[ ]*([&]{0,1})[ ]*(?=\w\b)", r"\1\2",
                  organization_name).strip()


def replace_tokens(organization_name):
    for words, rep in replacement_dict.items():
        organization_name = re.sub(words, rep, organization_name)
    for words, rep in replacement_dict.items():
        organization_name = re.sub(words, rep, organization_name)
    return organization_name


def preprocess_organization(organization_name,
                            replacement_string=' ',
                            apostrophe_replacement_string=""):
    ''' preprocess organization name '''
    try:
        organization_name = organization_name.decode('utf-8')
    except:
        pass

    organization_name = unidecode.unidecode(organization_name).lower().strip()
    organization_name = re.sub("([/_\\\\]+)", replacement_string,
                               organization_name)
    organization_name = re.sub(r"(\'s)\b",
                               r"{}".format(apostrophe_replacement_string),
                               organization_name)
    #organization_name = massage(organization_name)
    organization_name = re.sub('[^A-Za-z0-9\-\& ]+', " ", organization_name)
    organization_name = remove_suffix(organization_name)
    organization_name = re.sub('[\-]+', replacement_string, organization_name)
    organization_name = combine_single_characters(organization_name)

    organization_name = remove_tokens(organization_name).strip()
    organization_name = singularize(organization_name)
    organization_name = re.sub(r"\b(\w{1,2})[ ]+\&[ ]+(\w)\b", r"\1&\2",
                               organization_name)
    organization_name = replace_tokens(organization_name)
    organization_name = re.sub(" +", replacement_string,
                               organization_name).strip()
    return organization_name

import re

def test_pattern(word):
    pattern = r"\b{}\b".format(re.sub(r"([\.\^\$\*\+\?\{\}\[\]\|\(\)])", r'\\\1', r""+word+""))
    print pattern
    
def test_pattern2(word):
    pattern = r"{}".format(r"{}".format(word).replace(r'\\', r'\\\\'))
    print pattern
    
test_pattern(r"i have a * in this string. This is a\new text")
test_pattern("i have a * in this string. This is a\new text")

test_pattern2(r"i have a * in this string. This is a\new text")
test_pattern2("i have a * in this string. This is a\new text")
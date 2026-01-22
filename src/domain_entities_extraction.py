from pathlib import Path
import re
from domain_entities_normalization import (extract_reference_tokens)


# CONFIG

PDF_DIR = Path("Data/Documents")

terminalStrings = {
    "§",
    "чл.",
    "член ",
    "членове ",
    "ал.",
    "т.",
}

search_window =  100

# TRIE STRUCTURES

class TrieRoot:
    def __init__(self):
        self.children = []  # list[TrieNode]


class TrieNode:
    def __init__(self, value="", isTerminal=False):
        self.value = value
        self.isTerminal = isTerminal
        self.next = None

    def getSize(self):
        curr = self
        length = 0
        while curr is not None:
            curr = curr.next
            length += 1
        return length


def constructTrie(strings):
    root = TrieRoot()

    for s in strings:
        curr = root
        for idx, ch in enumerate(s.lower()):
            node = TrieNode(ch)
            if idx == len(s) - 1:
                node.isTerminal = True

            if curr == root:
                curr.children.append(node)
            else:
                curr.next = node

            curr = node

    return root

def is_next_digit(text: str, terminal_index: int) -> bool:
    k = terminal_index + 1
    n = len(text)

    # прескачаме ВСИЧКИ whitespace символи
    while k < n and text[k].isspace():
        k += 1

    return k < n and text[k].isdigit()

# PDF TEXT EXTRACTION

# ABBREVIATION DETECTOR
# >= 2 главни букви общо, позволени малки само по средата
# Примери: АПК, ЗУБ, ИЗоБ, ЗЗдр
def is_abbreviation(text: str, i: int) -> int:
    n = len(text)

    # boundary check – да не е в средата на ДУМА (буква)
    if i > 0 and (text[i - 1].isalpha()):
        return 0

    j = i
    upper_count = 0

    while j < n:
        ch = text[j]

        if "А" <= ch <= "Я":
            upper_count += 1
        elif "а" <= ch <= "я":
            if upper_count == 0:
                return 0
        else:
            break
        j += 1

    if upper_count >= 2:
        return j

    return 0

def is_eu_directive(text: str, i: int) -> int:
    n = len(text)

    # boundary: да не е в средата на дума/число
    if i > 0 and text[i - 1].isalnum():
        return 0

    j = i

    # първа група цифри (година)
    digits1 = 0
    while j < n and text[j].isdigit():
        j += 1
        digits1 += 1

    if digits1 < 2 or digits1 > 4:
        return 0

    # задължителна /
    if j >= n or text[j] != "/":
        return 0
    j += 1

    # втора група цифри
    digits2 = 0
    while j < n and text[j].isdigit():
        j += 1
        digits2 += 1

    if digits2 < 1 or digits2 > 3:
        return 0

    # опционално: /ЕО или /ЕС
    if j < n and text[j] == "/":
        if text[j:j+3] in ("/ЕО", "/ЕС"):
            j += 3
        else:
            return 0

    return j

def is_any_abbreviation(text: str, i: int) -> int:
    end = is_abbreviation(text, i)
    if end:
        return end

    return is_eu_directive(text, i)


# MAIN PARSER

def extract_domain_entities(text):
    startTrie = constructTrie(terminalStrings)

    references_count = 0

    text = re.sub(r"\s+", " ", text)

    i = 0
    n = len(text)

    tokens = []

    while i < n:
        starts = [x for x in startTrie.children if x.value == text[i].lower()]
        if not starts:
            i += 1
            continue

        matched_any_start = False

        for start in starts:
            curr = start
            j = i

            while curr is not None and j < n and curr.value == text[j].lower() :
                if curr.isTerminal and is_next_digit(text,j):
                    matched_any_start = True
                    start_idx = i
                    k = j + 1
                    found_stop = False

                    while k < n and (k- j) <= search_window:
                        # boundary защита
                        if k > 0 and text[k - 1].isalnum():
                            k += 1
                            continue

                        end_abbreviation_idx = is_any_abbreviation(text, k)
                        if end_abbreviation_idx > 0:
                            references_count+=1
                            law_reference = text[k:end_abbreviation_idx]

                            tokens.extend(extract_reference_tokens(
                                text,
                                start_idx,
                                k,
                                law_reference
                            ))

                            # remove law reference from text
                            mask_start = start_idx
                            mask_end = end_abbreviation_idx

                            mask = "*" * (mask_end - mask_start)
                            text = text[:mask_start] + mask + text[mask_end:]

                            found_stop = True
                            break

                        k += 1

                    if not found_stop:
                        pass

                    i = k
                    break

                curr = curr.next
                j += 1

            if matched_any_start:
                break

        if not matched_any_start:
            i += 1

    return [text, tokens]

# testing
if __name__ == "__main__":
    ref_count = extract_domain_entities()

    ref_count_per_doc = ref_count/4992

    print("references_count: ", ref_count, " per document: ", ref_count_per_doc )

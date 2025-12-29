from pathlib import Path
import re
import PyPDF2
from nltk import Trie
from soupsieve.util import lower

# =========================
# CONFIG
# =========================

PDF_DIR = Path("Data/Documents")

PATTERNS = {
    "invoice_number": re.compile(r"Invoice\s*#?:\s*([\w\-]+)", re.UNICODE),
    "date": re.compile(r"Date\s*:\s*([\d]{1,2}/[\d]{1,2}/[\d]{2,4})"),
    "total_amount": re.compile(r"Total\s*:\s*([€$£]?\s*[\d,.]+)", re.UNICODE),
}

terminalStrings = {
        " §",
        " чл.",
        " член ",
        " членове ",
        # "арг.", арг. от edge case
        " ал.",
        " т.",
}

terminalData = {
    " от "
}

class TrieRoot:
    def __init__(self):
        self.children = []

class TrieNode:
    def __init__(self, value="", isTerminal=False):
        self.next = None
        self.value = value
        self.isTerminal = isTerminal

    def print_node(self):
        curr = self
        while curr is not None:
            curr = curr.next

    def getSize(self):
        length = 0
        while curr is not None:
            curr = curr.next
            length += 1
        return length


def constuctTrie(terminalStrings):
    root = TrieRoot()

    for el in terminalStrings:
        curr = root
        for idx, char in enumerate(el):
            newNode = TrieNode(char)
            newNode.value = char
            if(idx == len(el) -1):
                newNode.isTerminal = True
            if(curr == root):
                curr.children.append(newNode)
            else:
                curr.next = newNode
            curr = newNode

    return root

def extract_text_from_pdf(pdf_path: Path) -> str:
    text_chunks = []

    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)

        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

    return "\n".join(text_chunks)


def parseDA(trie, text, i, next ):
    starts = [x for x in trie.children if x.value == lower(text[i])]
    if len(starts) > 0:
        for start in starts:
            curr = start
            while curr is not None and i < len(text) and curr.value == lower(text[i]):
                if curr.isTerminal:
                    break
                curr = curr.next
                i += 1
# =========================
# MAIN
# =========================

def main():

    trie = constuctTrie(terminalStrings)
    trie2 = constuctTrie(terminalData)

    for child in trie.children:
        child.print_node()

    for pdf_file in PDF_DIR.glob("*.pdf"):
        # print(f"Processing: {pdf_file.name}")

        text = extract_text_from_pdf(pdf_file)

        datacount = 0
        startcount = 0

        # Optional: normalize whitespace (very useful for PDFs)
        # text = re.sub(r"\s+", " ", text)
        i = 0
        while i < len(text):
            starts = [x for x in trie.children if x.value == lower(text[i])]
            if len(starts) > 0:
                for start in starts:
                    curr = start
                    count1 = 0
                    while curr is not None and i<len(text) and curr.value == lower(text[i]):
                        if curr.isTerminal:
                            starts2 = [x for x in trie2.children]
                            startcount+=1
                            if len(starts2) > 0:
                                for start1 in starts2:
                                    curr1 = start1
                                    counter = 0
                                    while curr1 is not None and i < len(text) and counter < 60:
                                        if curr1.isTerminal:
                                            print("really done", text[i-(counter+count1): i])
                                            datacount+=1
                                            break
                                        if lower(text[i]) == curr1.value:
                                                curr1 = curr1.next
                                        i += 1
                                        counter += 1
                            else:
                                break
                        count1+=1
                        curr = curr.next
                        i+=1
            i+=1

        # print(startcount, " - ", datacount, f" document {pdf_file.name}")



if __name__ == "__main__":
    main()

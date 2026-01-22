from pathlib import Path
import PyPDF2
import re

PDF_DIR = Path("Data/Documents")
SEARCH_WINDOW = 60

legal_entities_types = {
    'LEGAL': "LEGAL",
    'ARTICLE': "ARTICLE",
    'SECTION' : "SECTION",
    'SUBSECTION' : "SUBSECTION",
}

class LegalEntityHierarchy:
    def __init__(self, name):
        self.child = None
        self.name = name

    def add_child(self, child):
        self.child = child

    def construct_hierarchy(self):
        return self.helper(self)[1:]

    def helper(self, child_hierarchy):
        if child_hierarchy is None:
            return ""

        return "_" + self.name + self.helper(self.child)

LegalEntity = LegalEntityHierarchy(legal_entities_types["LEGAL"])

ArticleEntity = LegalEntityHierarchy(legal_entities_types["ARTICLE"])

SectionEntity = LegalEntityHierarchy(legal_entities_types["SECTION"])

SubSectionEntity = LegalEntityHierarchy(legal_entities_types["SUBSECTION"])

LegalEntity.add_child(ArticleEntity)
ArticleEntity.add_child(SectionEntity)
SectionEntity.add_child(SubSectionEntity)


def extract_text_from_pdf(pdf_path: Path) -> str:
    chunks = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                chunks.append(t)
    return " ".join(chunks)

def is_abbreviation(text: str, i: int) -> int:
    n = len(text)

    if i > 0 and text[i - 1].isalnum():
        return 0

    j = i
    upper = 0

    while j < n:
        ch = text[j]
        if "А" <= ch <= "Я":
            upper += 1
        elif "а" <= ch <= "я":
            if upper == 0:
                return 0
        else:
            break
        j += 1

    return j if upper >= 2 else 0

LEVEL_DEFS = {
    "чл": {"forms": {"чл.", "член", "членове"}},
    "ал": {"forms": {"ал.", "алинея"}},
    "т":  {"forms": {"т.", "точка"}},
    "§":  {"forms": {"§", "параграф"}},
}

def match_level(text, i):
    for level, data in LEVEL_DEFS.items():
        for form in data["forms"]:
            if text[i:i+len(form)].lower() == form:
                return level, i + len(form)
    return None, i

def read_number(text, i, end):
    while i < end and not text[i].isdigit():
        i += 1
    start = i
    while i < end and text[i].isdigit():
        i += 1
    return (int(text[start:i]), i) if start < i else (None, i)

RANGE_CHARS = {"-", "–", "—"}

def read_number_or_range(text, i, end):
    # първо число
    start_num, i = read_number(text, i, end)
    if start_num is None:
        return [], i

    nums = [start_num]

    # пропускаме whitespace
    while i < end and text[i].isspace():
        i += 1

    # диапазон?
    if i < end and text[i] in RANGE_CHARS:
        i += 1
        end_num, i = read_number(text, i, end)
        if end_num is not None and end_num >= start_num:
            nums = list(range(start_num, end_num + 1))

    return nums, i

def extract_reference_tokens(text, start, end, law):
    tokens = set()
    law = law.upper()
    tokens.add(law)

    # контекст 1: член
    current_article = None
    current_article_paragraph = None  # ал. към чл.

    # контекст 2: параграф (§)
    current_section = None
    current_section_paragraph = None  # ал. към §

    # контекст 3: започва с ал. без чл./§
    standalone_paragraph = None

    i = start
    while i < end:
        level, ni = match_level(text, i)
        if level is None:
            i += 1
            continue

        i = ni
        nums, i = read_number_or_range(text, i, end)
        if not nums:
            continue

        # член
        if level == "чл":
            current_article_paragraph = None
            standalone_paragraph = None

            for a in nums:
                current_article = a
                tokens.add(f"_чл:{a}_{law}")

        # параграф
        elif level == "§":
            current_section_paragraph = None
            standalone_paragraph = None

            for s in nums:
                current_section = s
                tokens.add(f"§:{s}_{law}")

                # ако има активен член → § е подниво на чл.
                if current_article is not None:
                    tokens.add(f"чл:{current_article}_§:{s}_{law}")

        # алинея
        elif level == "ал":
            for p in nums:
                if current_article is not None:
                    current_article_paragraph = p
                    tokens.add(
                        f"чл:{current_article}_ал:{p}_{law}"
                    )

                elif current_section is not None:
                    current_section_paragraph = p
                    tokens.add(
                        f"§:{current_section}_ал:{p}_{law}"
                    )

                else:
                    standalone_paragraph = p
                    tokens.add(f"ал:{p}_{law}")

        # точка
        elif level == "т":
            for t in nums:
                # т. към чл + ал
                if current_article is not None and current_article_paragraph is not None:
                    tokens.add(
                        f"чл:{current_article}_ал:{current_article_paragraph}_т:{t}_{law}"
                    )

                # т. към § + ал
                elif current_section is not None and current_section_paragraph is not None:
                    tokens.add(
                        f"§:{current_section}_ал:{current_section_paragraph}_т:{t}_{law}"
                    )

                # т. към § (без ал)
                elif current_section is not None:
                    tokens.add(
                        f"§:{current_section}_т:{t}_{law}"
                    )

                # т. към самостоятелна ал
                elif standalone_paragraph is not None:
                    tokens.add(
                        f"ал:{standalone_paragraph}_т:{t}_{law}"
                    )

                else:
                    pass

    return ["LEGAL:" + token for token in tokens ]

# ================= MAIN =================

def main():
    all_tokens = []

    for pdf in PDF_DIR.glob("*.pdf"):
        print(f"\n--- {pdf.name} ---")
        text = extract_text_from_pdf(pdf)
        text = re.sub(r"\s+", " ", text)

        i = 0
        n = len(text)

        while i < n:
            end_law = is_abbreviation(text, i)
            if end_law:
                law = text[i:end_law]
                start = max(0, i - SEARCH_WINDOW)

                tokens = extract_reference_tokens(
                    text,
                    start,
                    i,
                    law
                )

                all_tokens.append(tokens)
                print(tokens)

                i = end_law
            else:
                i += 1

    return all_tokens

# testing
if __name__ == "__main__":
    main()

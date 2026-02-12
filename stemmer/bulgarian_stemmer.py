#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pickle
import os


class BulgarianStemmer:
    def __init__(self, filename='stemmer/stem_rules_context_1.pkl'):
        self.stem_boundary = 1

        file_extension = os.path.splitext(filename)[1]
        if file_extension == '.pkl':
            self.load_pickle_context(filename)
        elif file_extension == '.txt':
            self.load_text_context(filename)
        else:
            raise IOError("Wrong file extension! .txt or .pkl files only!")

    def __call__(self, word: str) -> str:
        return self.stem(word)

    def load_pickle_context(self, filename: str):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, filename)

        with open(full_path, 'rb') as f:
            self.stemming_rules = pickle.load(f)

    def load_text_context(self, filename: str):
        self.stemming_rules = {}

        with open(filename, 'r', encoding='cp1251') as f:
            for line in f:
                rule_match = re.search(
                    r'([а-я]+)\s*==>\s*([а-я]*)\s+([0-9]+)',
                    line.lower()
                )

                if not rule_match:
                    continue

                if int(rule_match.group(3)) > self.stem_boundary:
                    self.stemming_rules[
                        rule_match.group(1)
                    ] = rule_match.group(2)

    def stem(self, word: str) -> str:
        word = word.lower()

        # думата съдържа поне една кирилска буква
        if not re.search(r'[а-я]', word) or len(word) <= 1:
            return word

        for i in range(len(word)):
            suffix = word[i:]
            if suffix in self.stemming_rules:
                return word[:i] + self.stemming_rules[suffix]

        return word

    def print_word(self, word: str):
        print(self(word))


if __name__ == '__main__':
    stemmer = BulgarianStemmer('stem_rules_context_1.pkl')

    stemmer.print_word('обикновен')
    stemmer.print_word('английският')
    stemmer.print_word('човекът')
    stemmer.print_word('уникалният')
    stemmer.print_word('негодувания')

from requests import Session, Response
from bs4 import BeautifulSoup as bs
import argparse


class OnlineTranslator:
    def __init__(self):
        self.languages: dict = {'to': str, 'from': str, 'word': str}
        self.url: str = 'https://context.reverso.net/translation/'
        self.lang_list: list = sorted([
            'arabic',
            'german',
            'english',
            'spanish',
            'french',
            'hebrew',
            'japanese',
            'dutch',
            'polish',
            'portuguese',
            'romanian',
            'russian',
            'turkish',
            'chinese',
            'all',
        ])
        self.session = Session()
        self.arg = self.args()

    def args(self):
        self.argv = argparse.ArgumentParser()
        self.argv.add_argument("_from")
        self.argv.add_argument("to")
        self.argv.add_argument("word")
        return self.argv.parse_args()

    def menu(self) -> None:
        _from = self.arg._from
        to = self.arg.to
        if _from not in self.lang_list:
            print(f'Sorry, the program doesn\'t support {_from}.')
            exit()
        if to not in self.lang_list:
            print(f'Sorry, the program doesn\'t support {to}.')
            exit()
        word = self.arg.word
        self.languages['word'] = word
        if to == -1 or to == 'all':
            self.dump_all(_from, word)
            return
        self.languages['to'] = to.capitalize()
        return self.parser(
            self.call(_from, to, word), 5
        )

    def dump_all(self, mlang: str, word: str) -> None:
        for lang in self.lang_list:
            if lang != mlang:
                if lang != 'all':
                    self.languages['to'] = lang.capitalize()
                    self.parser(self.call(mlang, lang, word), 1)

    def call(self, lang: str, trans: str, word: str) -> bs:
        request: Response = self.session.get(
            f'{self.url}{lang}-{trans}/{word}',
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit'
                '/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                'Content-Encoding': 'gzip',
            },
        )
        if request.status_code == 404:
            print(f'Sorry, unable to find {self.arg.word}')
            exit()
        elif request.status_code != 200:
            print('Something went wrong with your internet connection')
            exit()
        request.encoding = 'utf-8'
        return bs(request.content, 'html5lib')

    def parser(self, sopita: bs, n: int) -> None:
        examples_original: list = [
            r.text.strip() + ':'
            for r in sopita.select('#examples-content .example > .src')
        ][:n]
        examples_translated: list = [
            r.text.strip() for r in sopita.select('#examples-content .example > .trg')
        ][:n]

        translations: list = [
            r.text.strip().split('  ')[0]
            for r in sopita.select(
                '#translations-content > .translation, .translation.rtl'
            )
        ][:n]
        self.print_trans(translations, examples_original, examples_translated)

    def print_trans(self, trans: list, ex: list, ex1: list) -> None:
        zipped = list(zip(ex, ex1))
        with open(f'{self.languages.get("word")}.txt', 'a') as f:
            print(f'\n{self.languages.get("to")} Translations:')
            f.write(f'\n{self.languages.get("to")} Translations:\n')
            for k in trans:
                print(k)
                f.write(k + '\n')
            print()
            print(f'\n{self.languages.get("to")} Examples:')
            f.write(f'\n{self.languages.get("to")} Examples:\n')
            for x in zipped:
                for n in x:
                    print(n)
                    f.write(n + '\n')
                print()


if __name__ == "__main__":
    Translator = OnlineTranslator()
    Translator.menu()

from asyncio import AbstractEventLoop, get_event_loop, Task
from time import time
from typing import List, Optional, Tuple, Iterator
from aiohttp import ClientSession
from colorama import Fore, Style
from bs4 import BeautifulSoup as bs
import argparse


class Translator:
    url: str = "https://context.reverso.net/translation/"
    lang_list: List[str] = sorted(
        [
            "arabic",
            "german",
            "english",
            "spanish",
            "french",
            "hebrew",
            "japanese",
            "dutch",
            "polish",
            "portuguese",
            "romanian",
            "russian",
            "turkish",
            "chinese",
        ]
    )

    def main(self, _from: str, to: str, word: str) -> None:
        loop: AbstractEventLoop = get_event_loop()
        t0 = time()
        print(Fore.BLUE + f"App started.")
        if to == "all":
            loop.run_until_complete(self.get_translations(loop, _from, word))
        else:
            loop.run_until_complete(self.get_translations(loop, _from, word, to=to))
        print(
            Fore.BLUE + f"App finished at: {round(time() - t0, 2)}.", flush=True,
        )

    async def get_translations(
        self, loop: AbstractEventLoop, _from: str, word: str, to: Optional[str] = None
    ) -> None:
        tasks: List[Tuple[Task, str, int]] = []
        if to:
            html = await self.call(_from, to, word)
            self.process_data(*self.soup(html, 5), language=to)
            exit()
        for language in self.lang_list:
            if language != _from:
                tasks.append(
                    (loop.create_task(self.call(_from, language, word)), language, 1,)
                )
        for task, lang, amount in tasks:
            html: str = await task
            sopita = self.soup(html, 1)
            self.process_data(*sopita, language=lang)

    @staticmethod
    async def fetch(client: ClientSession, url: str) -> str:
        async with client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit"
                "/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            },
        ) as response:
            if response.status == 404:
                print(f"Sorry, unable to find the word.")
                exit()
            elif response.status != 200:
                print("There is something wrong with your internet connection.")
                exit()
            return await response.text()

    async def call(self, _from: str, _to: str, _word: str) -> str:
        async with ClientSession() as session:
            if _from not in self.lang_list:
                print(f"Sorry, the program doesn't support {_from}.")
                exit()
            if _to not in self.lang_list:
                print(f"Sorry, the program doesn't support {_to}.")
                exit()
            url = f"{self.url}{_from}-{_to}/{_word}"
            return await self.fetch(session, url)

    @staticmethod
    def soup(txt: str, n: int) -> Tuple[List[str], List[str], List[str]]:
        sopita = bs(txt, "html5lib")
        examples_original: List[str] = [
            r.text.strip() + ":"
            for r in sopita.select("#examples-content .example > .src")
        ][:n]
        examples_translated: List[str] = [
            r.text.strip() for r in sopita.select("#examples-content .example > .trg")
        ][:n]

        translations: List[str] = [
            r.text.strip().split("  ")[0]
            for r in sopita.select(
                "#translations-content > .translation, .translation.rtl"
            )
        ][:n]
        return examples_original, examples_translated, translations

    @staticmethod
    def process_data(
        examples_original: List[str],
        examples_translated: List[str],
        translations: List[str],
        language: str,
    ) -> None:
        examples: Iterator[Tuple[str, str]] = zip(
            examples_original, examples_translated
        )
        with open(f"{args.word}.txt", "w") as file:
            print(
                Style.BRIGHT + Fore.CYAN + f"{language.capitalize()} translations:",
                flush=True,
                file=file,
            )
            for translation in translations:
                print(Fore.WHITE + translation, flush=True, file=file)
            print(
                Style.BRIGHT + Fore.CYAN + f"{language.capitalize()} examples:",
                flush=True,
                file=file,
            )
            for original, translated in examples:
                print(Fore.WHITE + original, flush=True, file=file)
                print(Fore.LIGHTYELLOW_EX + translated, flush=True, file=file)
        with open(f"{args.word}.txt", "r") as f:
            print(f.read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("_from")
    parser.add_argument("to")
    parser.add_argument("word")
    args = parser.parse_args()
    t = Translator()
    t.main(args._from, args.to, args.word)

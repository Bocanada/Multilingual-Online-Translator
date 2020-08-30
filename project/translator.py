from asyncio import AbstractEventLoop, get_event_loop, Task
from time import time
from typing import List, NamedTuple, Optional, Set, Tuple, Iterator
from aiohttp import ClientSession
from colorama import Fore, Style
from bs4 import BeautifulSoup as bs
import click


class Data(NamedTuple):
    examples: Iterator[Tuple[str, str]]
    translations: List[str]
    language: str


class Translator:
    url: str = "https://context.reverso.net/translation/"
    lang_list: List[str] = [
        "arabic",
        "chinese",
        "german",
        "english",
        "french",
        "hebrew",
        "japanese",
        "dutch",
        "polish",
        "portuguese",
        "romanian",
        "russian",
        "turkish",
        "spanish",
    ]
    word: str

    async def get_translations(
        self, loop: AbstractEventLoop, _from: str, to: Optional[str] = None
    ) -> None:
        if to:
            html: str = await self.call(_from, to)
            self.Data = Data(*self.soup(html, 5), to)
            click.echo(self)
            return
        tasks: Set[Tuple[Task, str]] = set()
        self.lang_list.remove(_from)
        for language in self.lang_list:
            tasks.add((loop.create_task(self.call(_from, language)), language))
        for task, lang in tasks:
            html = await task
            self.Data = Data(*self.soup(html, 1), lang)
            click.echo(self)

    async def fetch(self, client: ClientSession, url: str) -> str:
        async with client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
        ) as response:
            if response.status == 404:
                click.echo(f"Sorry, unable to find the translation for '{self.word}'.")
                raise SystemExit
            elif response.status != 200:
                click.echo("There is something wrong with your internet connection.")
                raise SystemExit
            return await response.text()

    async def call(self, _from: str, _to: str) -> str:
        async with ClientSession() as session:
            url = f"{self.url}{_from}-{_to}/{self.word}"
            return await self.fetch(session, url)

    @staticmethod
    def soup(txt: str, n: int) -> Tuple[Iterator[Tuple[str, str]], List[str]]:
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
        return zip(examples_original, examples_translated), translations

    def __repr__(self) -> str:
        with open(f"{self.word}.txt", "w") as file:
            click.echo(
                f"{Style.BRIGHT + Fore.CYAN}{self.Data.language.capitalize()} translations:",
                file=file,
                color=True,
            )
            for translation in self.Data.translations:
                click.echo(f'{Fore.WHITE}{translation}', file=file, color=True)
            click.echo(
                f"{Style.BRIGHT + Fore.CYAN}{self.Data.language.capitalize()} examples:",
                file=file,
                color=True,
            )
            for original, translated in self.Data.examples:
                click.echo(f'{Fore.WHITE}{original}', file=file, color=True)
                click.echo(f'{Fore.LIGHTYELLOW_EX}{translated}', file=file, color=True)
        with open(f"{self.word}.txt", "r") as f:
            return f.read()


@click.command()
@click.option(
    '-f',
    '_from',
    default='english',
    type=click.Choice(Translator.lang_list),
)
@click.option(
    '-t', 'to', type=click.Choice(Translator.lang_list + ['all']), default='all'
)
@click.option('-w', 'word', help='The word you want to translate.', required=True)
def main(_from: str, to: str, word: str) -> None:
    t = Translator()
    t.word = word
    loop: AbstractEventLoop = get_event_loop()
    t0 = time()
    click.echo(f"{Fore.BLUE}App started.")
    if to == 'all':
        loop.run_until_complete(t.get_translations(loop, _from))
    else:
        loop.run_until_complete(t.get_translations(loop, _from, to=to))
    click.echo(f"{Fore.BLUE}Time taken: {round(time() - t0, 2)}")


if __name__ == "__main__":
    main()

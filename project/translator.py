from __future__ import annotations

import asyncio
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable

from bs4 import BeautifulSoup as bs
from click import Choice, command, option
from httpx import AsyncClient
from rich.console import Console

console = Console()
print = console.print

TranslationData = namedtuple(
    "TranslationData",
    ["examples_original", "examples_translated", "translations", "language"],
)


def soup(
    task: tuple[bytes, str] | None = None,
    res_content: bytes = None,
    lang: str = None,
    n: int = 6,
) -> TranslationData:
    if (not res_content or not lang) and task:
        res_content, lang = task
    assert res_content and lang
    sopita = bs(res_content, "html5lib")
    examples_original: tuple[str, ...] = tuple(
        f"{r.text.strip()}:" for r in sopita.select("#examples-content .example > .src")
    )[:n]
    examples_translated: tuple[str, ...] = tuple(
        r.text.strip() for r in sopita.select("#examples-content .example > .trg")
    )[:n]
    translations: tuple[str, ...] = tuple(
        r.text.strip().split("  ")[0]
        for r in sopita.select("#translations-content > .translation, .translation.rtl")
    )[:n]
    return TranslationData(
        iter(examples_original),
        iter(examples_translated),
        iter(translations),
        lang.capitalize(),
    )


def client():
    return AsyncClient(
        base_url="https://context.reverso.net/translation/",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:79.0)Gecko/20100101 Firefox/79.0"
            )
        },
    )


@dataclass
class Translator:
    word: str
    lang_list: tuple[str, ...] = field(
        default=(
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
        ),
        init=False,
    )
    client: AsyncClient = field(default_factory=client, init=False)

    async def gather_tasks(self, from_lang: str) -> Iterable[tuple[bytes, str]]:
        tasks: tuple[asyncio.Task[bytes], ...] = tuple(
            asyncio.create_task(self.fetch(from_lang, language), name=language)
            for language in self.lang_list
            if language != from_lang
        )
        await asyncio.gather(*tasks)
        result_task = ((task.result(), task.get_name()) for task in tasks)
        return result_task

    async def get_translations(self, _from: str, to: str | None = None) -> None:
        if to is not None and to != "all":
            html = await self.fetch(_from, to)
            data = soup(res_content=html, lang=to)
            return self.to_stdout(data)
        result = await self.gather_tasks(_from)
        with ProcessPoolExecutor() as executor:
            res = executor.map(soup, result)
        for data in res:
            self.to_stdout(data)
        await self.client.aclose()

    async def fetch(self, from_lang: str, to_lang: str) -> bytes:
        url = f"{from_lang}-{to_lang}/{self.word}"
        response = await self.client.get(url)
        if not response.is_error:
            return await response.aread()
        if response.status_code == 404:
            raise SystemExit(
                f"Sorry, unable to find the translation for {self.word!r}."
            )
        raise SystemExit("There is something wrong with your internet connection.")

    def to_stdout(self, data: TranslationData):
        console.print(f"{data.language} translations:", style="bold underline cyan")
        for translation in data.translations:
            console.print(translation, style="bold white")
        console.print(f"{data.language} examples:", style="bold underline cyan")
        for original, translated in zip(
            data.examples_original,
            data.examples_translated,
        ):
            console.print(original, style="magenta")
            console.print(translated, style="bold magenta")


@command()
@option(
    "-f",
    "_from",
    default="english",
    type=Choice(Translator.lang_list),
)
@option("-t", "to", type=Choice(Translator.lang_list + ("all",)), default="all")
@option("-w", "word", help="The word you want to translate.", required=True)
def main(_from: str, to: str, word: str = "hello") -> None:
    t = Translator(word)
    t.word = word.lower()
    asyncio.run(t.get_translations(_from, to=to))


if __name__ == "__main__":
    main()

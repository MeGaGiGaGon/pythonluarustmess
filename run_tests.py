import argparse
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Self

def existing_path(raw: str) -> Path:
    path = Path(raw)
    if path.exists():
        return path
    else:
        raise ValueError(f"Path {raw!r} does not exist")

@dataclass
class TestCase:
    name: str
    plrm_code: str
    stdin: str
    stdout: str
    return_code: str

    @classmethod
    def default(cls, name: str, plrm_code: str) -> Self:
        return cls(name, plrm_code, "", "", "")


def get_test_cases() -> Generator[TestCase]:
    tests_folder = Path(__file__).parent / "tests"
    for test in sorted(tests_folder.rglob("*.md")):
        markdown_blocks: list[str] = []
        raw_markdown = test.read_text()
        index = 0
        while True:
            try:
                next_block_start = raw_markdown.index("```", index)
            except ValueError:
                break
            try:
                next_block_end = raw_markdown.index("```", next_block_start + 3)
            except ValueError:
                print(f"WARNING: Unclosed code block in file {test}")
                break
            markdown_blocks.append(raw_markdown[next_block_start+3:next_block_end])
            index = next_block_end + 3

        case = TestCase.default("///", "")
        for markdown_block in markdown_blocks:
            try:
                block_type, *rest = markdown_block.splitlines()
            except ValueError:
                print(f"WARNING: Badly formatted code block in file {test}")
                continue
            rest = "\n".join(rest)
            if block_type.startswith("plrm"):
                if case.name != "///":
                    yield case
                if block_type.endswith("collect"):
                    rest = f"blockcollect {rest} end"
                case = TestCase.default(test.name, rest)
            if block_type.startswith("stdin"):
                case.stdin = rest
            if block_type.startswith("stdout"):
                case.stdout = rest
            if block_type.startswith("return"):
                case.return_code = rest
        if case.name != "///":
            yield case

if __name__ == "__main__":
    from interpreters import interpreter_generic
    parser = argparse.ArgumentParser(
        prog="MDTestPLRM",
        description="Runner for PLRM MarkDown Tests",
    )
    _ = parser.add_argument("--case", "-k", help="Run a specific case (matching by name includes)", default="")
    args = parser.parse_args()
    print(*get_test_cases(), sep="\n")
    for case in get_test_cases():
        if args.case not in case.name:  # pyright: ignore[reportAny]
            continue
        code = interpreter_generic.CodeBlock.parser(case.plrm_code, 0)
        print(code)
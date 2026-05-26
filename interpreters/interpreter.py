import io
import string
from typing import TypeAlias, Sequence, Mapping, Literal, Generator
from dataclasses import dataclass

# enum CodeItem

@dataclass
class NameRef:
    name: str

@dataclass
class Enum:
    variants: Block

@dataclass
class Record:
    fields: Mapping[str, CodeItem]

@dataclass
class Function:
    argument: Record
    body: Block

@dataclass
class MatchCase:
    case_condition: CodeItem
    body: CodeItem

@dataclass
class Match:
    matched: CodeItem
    cases: Sequence[MatchCase]

@dataclass
class Loop:
    loop_type: Literal["For", "While"]
    loop_end_type: Literal["Collect", "Last"]
    iterator: CodeItem
    target: CodeItem
    body: Block

@dataclass
class Block:
    body: Sequence[CodeItem]

@dataclass
class Error:
    message: str

@dataclass
class IfBodies:
    condition: CodeItem
    body: Block

@dataclass
class If:
    bodies: Sequence[IfBodies]
    else_: Block

@dataclass
class Tuple:
    elements: Block

CodeItem: TypeAlias = str | None | bool| NameRef | Enum | Record | Function | Match | Loop | Block | Error

@dataclass
class StringToken:
    content: str
    raw: str
    depth: int
    offset: int

@dataclass
class ItemToken:
    content: CodeItem
    raw: str
    depth: int
    offset: int


type Token = StringToken | ItemToken

def tokenize(input: str) -> Generator[Token]:
    index = 0
    depth = 0
    last_start = 0
    while index < len(input):
        if input[index] in string.whitespace:
            index += 1
            continue
        item = ""
        while input[index] not in string.whitespace:
            item += input[index]
            index += 1
        # breakpoint()
        if item.startswith("string"):
            split = item.split("string")
            if all([not x for x in split]):
                try:
                    end_str = "end" * (len(split) - 1)
                    end_index = input.index(end_str, index)
                    raw_end_index = end_index + len(end_str)
                    yield ItemToken(input[index+1:end_index-1], input[last_start:raw_end_index], depth, last_start)
                    index = raw_end_index
                except ValueError:
                    yield ItemToken(Error("Unclosed string"), input[last_start:index], depth, last_start)
            else:
                yield ItemToken(Error("Unclosed string"), input[last_start:index], depth, last_start)
        else:
            match item:
                case "Empty":
                    yield ItemToken(None, input[last_start:index], depth, last_start)
                case "True":
                    yield ItemToken(True, input[last_start:index], depth, last_start)
                case "False":
                    yield ItemToken(False, input[last_start:index], depth, last_start)
                case "end":
                    depth = depth - 1
                    if depth < 0:
                        yield ItemToken(Error("End depth below 0"), input[last_start:index], depth, last_start)
                        depth = 0
                    else:
                        yield StringToken(item, input[last_start:index], depth, last_start)
                case "enum" | "record" | "match" | "function" | "while" | "for" | "if" | "block" | "of" | "new":
                    yield StringToken(item, input[last_start:index], depth, last_start)
                    depth = depth + 1
                case str():
                    yield StringToken(item, input[last_start:index], depth, last_start)
        last_start = index

# output = io.StringIO()
# first = True
# for token in tokenize(open("interpreters/interpreter.plrm", "r").read()):
#     if token.content in ["enum", "record", "match", "function", "while", "for", "if", "block", "of", "new"]:
#         print("\n", "  " * token.depth, token.content, "\n", "  " * (token.depth + 1), sep="", end="", file=output)
#         first = True
#     elif token.content == "end":
#         first = True
#         print("\n", "  " * token.depth, token.content, "\n", "  " * token.depth, sep="", file=output, end="")
#     else:
#         if first:
#             first = False
#             print(token.content if isinstance(token, StringToken) else str(type(token.content)), end="", file=output)
#         else:
#             print("", token.content if isinstance(token, StringToken) else str(type(token.content)), end="", file=output)
#         if token.depth == 0:
#             first = True
#             print(file=output)

# output.seek(0)
# output = output.read()
# # print(repr(output))
# output = output.splitlines()
# output = [x.rstrip() for x in output if x.rstrip()]
# print("\n".join(output))


for token in tokenize(open("interpreters/interpreter.plrm", "r").read()):
    # print(token if isinstance(token, StringToken) else str(type(token.content)))
    print("  " * token.depth, token.content if isinstance(token, StringToken) else str(type(token.content)), sep="")

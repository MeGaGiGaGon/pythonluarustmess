import sys
from typing import ClassVar, Never, final, Literal, override
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

@final
class Ok[T]:
    __match_args__ = ("_value",)
    def __init__(self, value: T):
        self._value: T = value
    
    @override
    def __repr__(self) -> str:
        return f"Ok({self._value!r})"
    
    def is_ok[E](self: Result[T, E]) -> Literal[True]:
        return True
    
    def to_value(self) -> T:
        return self._value

@final
class Err[E]:
    def __init__(self, value: E):
        self._value: E = value
    
    @override
    def __repr__(self) -> str:
        return f"Err({self._value!r})"
    
    def is_ok[T](self: Result[T, E]) -> Literal[False]:
        return False
    
    def to_value(self) -> E:
        return self._value

type Result[T, E] = Ok[T] | Err[E]

type ParserResult[O, E] = Result[tuple[int, O], E]
type ParserFunc[O, E] = Callable[[str, int], ParserResult[O, E]]

def simple_parser[O, E](parser: ParserFunc[O, E]) -> Parser[O, E]:
    return Parser(parser)

class Parser[O, E]:
    def __init__(self, func: ParserFunc[O, E]):
        self._func: ParserFunc[O, E] = func
    
    def __call__(self, input: str, index: int) -> ParserResult[O, E]:
        return self._func(input, index)

    def ok_to[NEW_O](self, to: NEW_O) -> Parser[NEW_O, E]:
        def inner(input: str, index: int) -> ParserResult[NEW_O, E]:
            match self._func(input, index):
                case Ok((index, _)):
                    return Ok((index, to))
                case Err() as e:
                    return e
        return Parser(inner)

    def map_ok[NEW_O](self, func: Callable[[O], NEW_O]) -> Parser[NEW_O, E]:
        def inner(input: str, index: int) -> ParserResult[NEW_O, E]:
            match self._func(input, index):
                case Ok((index, output)):
                    return Ok((index, func(output)))
                case Err() as e:
                    return e
        return Parser(inner)

    def star_map_ok[*TS, NEW_O](self: Parser[tuple[*TS], E], func: Callable[[*TS], NEW_O]) -> Parser[NEW_O, E]:
        def inner(input: str, index: int) -> ParserResult[NEW_O, E]:
            match self._func(input, index):
                case Ok((index, output)):
                    return Ok((index, func(*output)))
                case Err() as e:
                    return e
        return Parser(inner)
    
    def __or__[OO, OE](self, other: Parser[OO, OE]) -> Parser[O | OO, OE]:
        def inner(input: str, index: int) -> ParserResult[O | OO, OE]:
            match self._func(input, index):
                case Ok() as ok:
                    return ok
                case Err():
                    return other(input, index)
        return Parser(inner)
    
    def then[OO, OE](self, other: Parser[OO, OE]) -> Parser[tuple[O, OO], E | OE]:
        def inner(input: str, index: int) -> ParserResult[tuple[O, OO], E | OE]:
            match self._func(input, index):
                case Ok((index, self_output)):
                    match other._func(input, index):
                        case Ok((index, other_output)):
                            return Ok((index, (self_output, other_output)))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return Parser(inner)
    
    def unpack_then[*TS, OO, OE](self: Parser[tuple[*TS], E], other: Parser[OO, OE]) -> Parser[tuple[*TS, OO], E | OE]:
        def inner(input: str, index: int) -> ParserResult[tuple[*TS, OO], E | OE]:
            match self._func(input, index):
                case Ok((index, self_output)):
                    match other._func(input, index):
                        case Ok((index, other_output)):
                            return Ok((index, (*self_output, other_output)))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return Parser(inner)
    
    def then_ignore[OE](self, other: Parser[object, OE]) -> Parser[O, E | OE]:
        def inner(input: str, index: int) -> ParserResult[O, E | OE]:
            match self._func(input, index):
                case Ok((index, self_output)):
                    match other._func(input, index):
                        case Ok((index, _)):
                            return Ok((index, self_output))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return Parser(inner)
    
    def ignore_then[OO, OE](self, other: Parser[OO, OE]) -> Parser[OO, E | OE]:
        def inner(input: str, index: int) -> ParserResult[OO, E | OE]:
            match self._func(input, index):
                case Ok((index, _)):
                    match other._func(input, index):
                        case Ok((index, other_output)):
                            return Ok((index, other_output))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return Parser(inner)

    def zero_or_more(self) -> Parser[Sequence[O], Never]:
        def inner(input: str, index: int) -> ParserResult[Sequence[O], Never]:
            result: list[O] = []
            while True:
                match self._func(input, index):
                    case Ok((index, output)):
                        result.append(output)
                    case Err():
                        break
            return Ok((index, result))
        return Parser(inner)
    
    def debug(self, message: str) -> Parser[O, E]:
        def inner(input: str, index: int) -> ParserResult[O, E]:
            global depth
            print("  " * depth, message, " ", index, sep="")
            depth += 1
            res = self._func(input, index)
            depth -= 1
            print("  " * depth, res, sep="")
            return res
        return Parser(inner)

class ForwardRefParser[O, E](Parser[O, E]):
    @override
    def __init__(self, func: Callable[[], Parser[O, E]]):  # pyright: ignore[reportMissingSuperCall]
        self._meta_func: Callable[[], Parser[O, E]] = func
    
    @property
    @override
    def _func(self) -> ParserFunc[O, E]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._meta_func()

def debug[O, E](message: str) -> Callable[[Parser[O, E]], Parser[O, E]]:
    def inner(func: Parser[O, E]) -> Parser[O, E]:
        return func.debug(message)
    return inner

def just(seq: str) -> Parser[str, None]:
    def inner(input: str, index: int) -> ParserResult[str, None]:
        if input.startswith(seq, index):
            return Ok((index + len(seq), seq))
        else:
            return Err(None)
    return Parser(inner)

def any_of(seq: Sequence[str]) -> Parser[str, None]:
    def inner(input: str, index: int) -> ParserResult[str, None]:
        for item in seq:
            if input.startswith(item, index):
                return Ok((index + len(item), item))
        return Err(None)
    return Parser(inner)

@simple_parser
def take_word(input: str, index: int) -> ParserResult[str, None]:
    if index >= len(input):
        return Err(None)
    starting_index = index
    while index < len(input) and input[index] not in "\n\r\t ":
        index += 1
    return Ok((index, input[starting_index:index]))


class Spanned[T]:
    def __init__(self, inner: T, start: int, end: int):
        self._inner: T = inner
        self.start: int = start
        self.end: int = end
    
    def to_inner(self) -> T:
        return self._inner
    
    @override
    def __repr__(self) -> str:
        return f"Spanned(_inner={self._inner!r}, start={self.start!r}, end={self.end!r})"

def make_spanned[O, E](parser: Parser[O, E]) -> Parser[Spanned[O], E]:
    def new_parser(input: str, index: int) -> ParserResult[Spanned[O], E]:
        result = parser(input, index)
        match result:
            case Ok():
                new_index, to_span = result.to_value()
                return Ok((new_index, Spanned(to_span, index, new_index)))
            case Err():
                return result
    return Parser(new_parser)

def spanned_simple_parser[O, E](parser: ParserFunc[O, E]) -> Parser[Spanned[O], E]:
    return make_spanned(Parser(parser))

def make_meta_spanned[**P, O, E](parser_maker: Callable[P, Parser[O, E]]) -> Callable[P, Parser[Spanned[O], E]]:
    def new_parser_maker(*args: P.args, **kwargs: P.kwargs) -> Parser[Spanned[O], E]:
        parser = parser_maker(*args, **kwargs)
        def new_parser(input: str, index: int) -> ParserResult[Spanned[O], E]:
            result = parser(input, index)
            match result:
                case Ok():
                    new_index, to_span = result.to_value()
                    return Ok((new_index, Spanned(to_span, index, new_index)))
                case Err():
                    return result
        return Parser(new_parser)
    return new_parser_maker

@dataclass
class Whitespace:
    raw: Sequence[str]

    parser: ClassVar[Parser[Spanned[Whitespace], None]]
Whitespace.parser = make_spanned(any_of("\n\r\t ").zero_or_more().map_ok(Whitespace)).debug("Whitespace")


@dataclass
class String:
    content: str

    @debug("String")
    @spanned_simple_parser
    @staticmethod
    def parser(input: str, index: int) -> ParserResult[String | Error, None]:
        if input.startswith("string", index):
            offset = 6
            while input.startswith("string", offset + index):
                offset += 6
            count = offset // 6
            try:
                end = input.index("end" * count, index)
                return Ok((end + 3 * count, String(input[index + 6 * count + 1:end].strip())))
            except ValueError:
                return Ok((index + offset, Error("string" * count, "Unclosed string")))
        else:
            return Err(None)

@dataclass
class Ref:
    sep: Spanned[Whitespace]
    referenced: str

    parser: ClassVar[Parser[Spanned[Ref], None]]
Ref.parser = make_spanned(just("ref").ignore_then(Whitespace.parser).then(take_word).star_map_ok(Ref)).debug("Ref")

@dataclass
class Is:
    name: str
    sep1: Spanned[Whitespace]
    sep2: Spanned[Whitespace]
    value: CodeItem

    parser: ClassVar[Parser[Spanned[Is], None]] = ForwardRefParser(
        lambda: make_spanned(
            take_word.then(Whitespace.parser)
            .then_ignore(just("is"))
            .unpack_then(Whitespace.parser)
            .unpack_then(CodeItem.parser)
            .star_map_ok(Is)
        ).debug("Is")
    )

@dataclass
class Of:
    name: str
    sep1: Spanned[Whitespace]
    sep2: Spanned[Whitespace]
    value: CodeItem

    parser: ClassVar[Parser[Spanned[Is], None]] = ForwardRefParser(
        lambda: make_spanned(
            take_word.then(Whitespace.parser)
            .then_ignore(just("is"))
            .unpack_then(Whitespace.parser)
            .unpack_then(CodeItem.parser)
            .star_map_ok(Is)
        ).debug("Is")
    )

@dataclass
class Enum:
    sep1: Spanned[Whitespace]
    name: str
    sep2: Spanned[Whitespace]
    items: CodeBlock

    parser: ClassVar[Parser[Spanned[Enum], None]] = ForwardRefParser(
        lambda: make_spanned(
            just("enum")
            .ignore_then(Whitespace.parser)
            .then(take_word)
            .unpack_then(Whitespace.parser)
            .unpack_then(CodeBlock.parser)
            .star_map_ok(Enum)
        ).debug("Enum")
    )

@dataclass
class Call:
    sep1: Spanned[Whitespace]
    call_on: CodeItem
    sep2: Spanned[Whitespace]
    method: CodeItem
    sep3: Spanned[Whitespace]
    argument: CodeItem

    parser: ClassVar[Parser[Spanned[Call], None]] = ForwardRefParser(
        lambda: make_spanned(
            just("call")
            .ignore_then(Whitespace.parser)
            .then(CodeItem.parser)
            .unpack_then(Whitespace.parser)
            .unpack_then(CodeItem.parser)
            .unpack_then(Whitespace.parser)
            .unpack_then(CodeItem.parser)
            .star_map_ok(Call)
        ).debug("Enum")
    )

    def execute(self, scope_items: Mapping[str, CodeItem]):
        call_on = self.call_on.execute()


@dataclass
class Error:
    raw: str
    message: str

    @make_meta_spanned
    @staticmethod
    def parser(message: str) -> Parser[Error, None]:
        def inner(input: str, index: int) -> ParserResult[Error, None]:
            match take_word(input, index):
                case Ok((index, raw)):
                    return Ok((index, Error(raw, message)))
                case Err() as e:
                    return e
        return Parser(inner).debug("Error")

    def execute(self, scope_items: Mapping[str, CodeItem]) -> tuple[InnerCodeItem, Mapping[str, CodeItem]]:
        return self

@dataclass
class UnknownToken:
    raw: str

    @debug("UnknownToken")
    @spanned_simple_parser
    @staticmethod
    def parser(input: str, index: int) -> ParserResult[UnknownToken, None]:
        match take_word(input, index):
            case Ok((index, raw)):
                return Ok((index, UnknownToken(raw)))
            case Err() as e:
                return e

    def execute(self, scope_items: Mapping[str, CodeItem]) -> tuple[InnerCodeItem, Mapping[str, CodeItem]]:
        return String(self.raw), scope_items

type InnerCodeItem = String | Ref | Call | Enum | Is | Error | UnknownToken

@dataclass
class CodeItem:
    item: Spanned[InnerCodeItem]

    parser: ClassVar[Parser[CodeItem, None]] = ForwardRefParser(
        lambda: (
            String.parser
            | Ref.parser
            | Call.parser
            | Enum.parser
            | Is.parser
            | UnknownToken.parser
        )
        .map_ok(CodeItem)
        .debug("CodeItem")
    )

    def execute(self, scope_items: Mapping[str, CodeItem]) -> tuple[InnerCodeItem, Mapping[str, CodeItem]]:
        return self.item.to_inner().execute(scope_items)

@dataclass
class CodeBlock:
    start: Spanned[Whitespace]
    items: Sequence[tuple[CodeItem, Spanned[Whitespace]]]

    parser: ClassVar[Parser[CodeBlock, None]]
CodeBlock.parser = Whitespace.parser.then(
    CodeItem.parser.then(Whitespace.parser).zero_or_more()
).star_map_ok(CodeBlock).debug("CodeBlock")

depth = 0

if __name__ == "__main__":
    if len(sys.argv) == 2:
        input = sys.argv[1]
    else:
        input = sys.stdin.read()
    print(CodeBlock.parser(input, 0))

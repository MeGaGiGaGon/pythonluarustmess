import abc
from dataclasses import dataclass
from typing import Any, ClassVar, Never, final, Literal, override
from collections.abc import Callable, Sequence

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
    __match_args__ = ("_value",)
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
    return SimpleParser(parser)

class Parser[O, E](abc.ABC):
    @property
    @abc.abstractmethod
    def func(self) -> ParserFunc[O, E]:
        ...

    def __call__(self, input: str, index: int) -> ParserResult[O, E]:
        return self.func(input, index)

    def ok_to[NEW_O](self, to: NEW_O) -> Parser[NEW_O, E]:
        def inner(input: str, index: int) -> ParserResult[NEW_O, E]:
            match self.func(input, index):
                case Ok((index, _)):
                    return Ok((index, to))
                case Err() as e:
                    return e
        return SimpleParser(inner)

    def map_ok[NEW_O](self, func: Callable[[O], NEW_O]) -> Parser[NEW_O, E]:
        def inner(input: str, index: int) -> ParserResult[NEW_O, E]:
            match self.func(input, index):
                case Ok((index, output)):
                    return Ok((index, func(output)))
                case Err() as e:
                    return e
        return SimpleParser(inner)

    def star_map_ok[*TS, NEW_O](self: Parser[tuple[*TS], E], func: Callable[[*TS], NEW_O]) -> Parser[NEW_O, E]:
        def inner(input: str, index: int) -> ParserResult[NEW_O, E]:
            match self.func(input, index):
                case Ok((index, output)):
                    return Ok((index, func(*output)))
                case Err() as e:
                    return e
        return SimpleParser(inner)

    def __or__[OO, OE](self, other: Parser[OO, OE]) -> Parser[O | OO, OE]:
        def inner(input: str, index: int) -> ParserResult[O | OO, OE]:
            match self.func(input, index):
                case Ok() as ok:
                    return ok
                case Err():
                    return other(input, index)
        return SimpleParser(inner)
    
    def then[OO, OE](self, other: Parser[OO, OE]) -> Parser[tuple[O, OO], E | OE]:
        def inner(input: str, index: int) -> ParserResult[tuple[O, OO], E | OE]:
            match self.func(input, index):
                case Ok((index, self_output)):
                    match other.func(input, index):
                        case Ok((index, other_output)):
                            return Ok((index, (self_output, other_output)))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def unpack_then[*TS, OO, OE](self: Parser[tuple[*TS], E], other: Parser[OO, OE]) -> Parser[tuple[*TS, OO], E | OE]:
        def inner(input: str, index: int) -> ParserResult[tuple[*TS, OO], E | OE]:
            match self.func(input, index):
                case Ok((index, self_output)):
                    match other.func(input, index):
                        case Ok((index, other_output)):
                            return Ok((index, (*self_output, other_output)))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def then_ignore[OE](self, other: Parser[object, OE]) -> Parser[O, E | OE]:
        def inner(input: str, index: int) -> ParserResult[O, E | OE]:
            match self.func(input, index):
                case Ok((index, self_output)):
                    match other.func(input, index):
                        case Ok((index, _)):
                            return Ok((index, self_output))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def ignore_then[OO, OE](self, other: Parser[OO, OE]) -> Parser[OO, E | OE]:
        def inner(input: str, index: int) -> ParserResult[OO, E | OE]:
            match self.func(input, index):
                case Ok((index, _)):
                    match other.func(input, index):
                        case Ok((index, other_output)):
                            return Ok((index, other_output))
                        case Err() as e:
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)

    def zero_or_more(self) -> Parser[Sequence[O], Never]:
        def inner(input: str, index: int) -> ParserResult[Sequence[O], Never]:
            result: list[O] = []
            while True:
                match self.func(input, index):
                    case Ok((index, output)):
                        result.append(output)
                    case Err():
                        break
            return Ok((index, result))
        return SimpleParser(inner)

    def one_or_more(self) -> Parser[Sequence[O], E]:
        def inner(input: str, index: int) -> ParserResult[Sequence[O], E]:
            first = self.func(input, index)
            match first:
                case Ok((index, output)):
                    result: list[O] = [output]
                    while True:
                        match self.func(input, index):
                            case Ok((index, output)):
                                result.append(output)
                            case Err():
                                break
                    return Ok((index, result))
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def debug(self, message: str) -> Parser[O, E]:
        def inner(input: str, index: int) -> ParserResult[O, E]:
            global depth
            print("  " * depth, message, " ", index, sep="")
            depth += 1
            res = self.func(input, index)
            depth -= 1
            print("  " * depth, res, sep="")
            return res
        return SimpleParser(inner)


class SimpleParser[O, E](Parser[O, E]):
    def __init__(self, func: ParserFunc[O, E]):
        self._func: ParserFunc[O, E] = func
    
    @property
    @override
    def func(self) -> ParserFunc[O, E]:
        return self._func

depth = 0

class ForwardRefParser[O, E](Parser[O, E]):
    def __init__(self, func: Callable[[], Parser[O, E]]):
        self._metafunc: Callable[[], Parser[O, E]] = func

    @property
    @override
    def func(self) -> ParserFunc[O, E]:
        return self._metafunc()

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
    return SimpleParser(inner)

def any_of(seq: Sequence[str]) -> Parser[str, None]:
    def inner(input: str, index: int) -> ParserResult[str, None]:
        for item in seq:
            if input.startswith(item, index):
                return Ok((index + len(item), item))
        return Err(None)
    return SimpleParser(inner)

def char_in_range(start: int, end: int) -> Parser[str, None]:
    def inner(input: str, index: int) -> ParserResult[str, None]:
        if index < len(input):
            if start <= ord(input[index]) <= end:
                return Ok((index + 1, input[index]))
        return Err(None)
    return SimpleParser(inner)

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
    return SimpleParser(new_parser)

def spanned_simple_parser[O, E](parser: ParserFunc[O, E]) -> Parser[Spanned[O], E]:
    return make_spanned(SimpleParser(parser))

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
        return SimpleParser(new_parser)
    return new_parser_maker

wsitem = any_of(" \n\t\r")
@dataclass
class WSComment:
    sep1: str
    comment: Comment
    sep2: str

    parser: ClassVar[Parser[WSComment, None]] = ForwardRefParser(lambda: wsitem.then(Comment.parser).unpack_then(wsitem).star_map_ok(WSComment))

@dataclass
class Whitespace:
    inner: str | tuple[str, Whitespace] | tuple[WSComment, Whitespace]
ws: Parser[Whitespace, None] = ForwardRefParser(lambda: (wsitem.then(ws) | WSComment.parser.then(ws) | wsitem).map_ok(Whitespace))

digit = any_of([  "zero","one","two","three","four","five","six","seven","eight","nine"])
@dataclass
class Number:
    start: str
    sep1: Whitespace
    number: int
    sep2: Whitespace
    end: str
number = just("number").then(ws).unpack_then(digit.one_or_more().map_ok("".join).map_ok(int)).unpack_then(ws).unpack_then(just("end")).star_map_ok(Number).debug("number")

chars = char_in_range(0x21, 0x10FFFF).one_or_more().map_ok("".join)

@simple_parser
def stringtail(input: str, index: int) -> ParserResult[Sequence[str], None]:
    return (wsitem.one_or_more().map_ok("".join).then(just("end")) | wsitem.one_or_more().map_ok("".join).then(chars).unpack_then(stringtail)).map_ok(lambda x: [x[0], x[1]] if len(x) == 2 else [x[0], x[1], *x[2]])(input, index)

@dataclass
class String:
    start: str
    sep1: Whitespace
    string: str
    sep2: Whitespace
    end: str
string = just("string").then(stringtail).map_ok(lambda x: String(x[0], Whitespace(x[1][0]), "".join(x[1][1:-2]), Whitespace(x[1][-2]), x[1][-1])).debug("string")

@dataclass
class Comment:
    start: str
    sep1: Whitespace
    string: str
    sep2: Whitespace
    end: str

    parser: ClassVar[Parser[Comment, None]] = just("comment").then(stringtail).map_ok(lambda x: Comment(x[0], Whitespace(x[1][0]), "".join(x[1][1:-2]), Whitespace(x[1][-2]), x[1][-1]))

@dataclass
class Call:
    start: str
    sep1: Whitespace
    method_of: Item
    sep2: Whitespace
    method_name: Item
    sep3: Whitespace
    call_value: Item

    parser: ClassVar[Parser[Call, None]] = ForwardRefParser(lambda: just("call").then(ws).unpack_then(Item.parser).unpack_then(ws).unpack_then(Item.parser).unpack_then(ws).unpack_then(Item.parser).star_map_ok(Call))

@dataclass
class Assign:
    start: str
    sep1: Whitespace
    assign_to: NameItem
    sep2: Whitespace
    value: Item
assign: Parser[Assign, None] = ForwardRefParser(lambda: just("call").then(ws).unpack_then(NameItem.parser).unpack_then(ws).unpack_then(Item.parser).star_map_ok(Assign))

@dataclass
class ForLoop:
    type: str
    sep1: Whitespace
    assign_to: NameItem
    sep2: Whitespace
    in_: str
    sep3: Whitespace
    iter_over: Item
    sep4: Whitespace
    block: BlockItem
    end: str
forloop = ForwardRefParser(lambda: (
    (just("for") | just("forcollect"))
    .then(ws)
    .unpack_then(NameItem.parser)
    .unpack_then(ws)
    .unpack_then(just("in"))
    .unpack_then(ws)
    .unpack_then(Item.parser)
    .unpack_then(ws)
    .unpack_then(Block.blockitem)
    .unpack_then(just("end")).star_map_ok(ForLoop)
))

@dataclass
class WhileLoop:
    type: str
    sep1: Whitespace
    condition: Item
    sep2: Whitespace
    block: BlockItem
    end: str
whileloop = ForwardRefParser(lambda: (
    (just("while") | just("whilecollect"))
    .then(ws)
    .unpack_then(Item.parser)
    .unpack_then(ws)
    .unpack_then(Block.blockitem)
    .unpack_then(just("end")).star_map_ok(WhileLoop)
))

type Case = tuple[Item, Whitespace, Item, Whitespace]
@dataclass
class Match:
    start: str
    sep1: Whitespace
    scrutinee: Item
    sep2: Whitespace
    cases: Sequence[Case]
    sep3: Whitespace
    end: str

    case: ClassVar[Parser[Case, None]] = ForwardRefParser(lambda: (Item.parser.then(ws).unpack_then(Item.parser).unpack_then(ws)))
match = ForwardRefParser(lambda: just("match").then(ws).unpack_then(Item.parser).unpack_then(ws).unpack_then(Match.case.one_or_more()).unpack_then(ws).unpack_then(just("end")).star_map_ok(Match))

@dataclass
class Name:
    value: str
name = ForwardRefParser(func=lambda: char_in_range(0x21, 0x10FFFF).one_or_more().map_ok("".join).map_ok(Name)).debug("name")

@dataclass
class Generics:
    sep1: Whitespace
    generics: str
    sep2: Whitespace
    names: Sequence[tuple[Name, Whitespace]]
    end: str
    sep3: Whitespace

    @simple_parser
    @staticmethod
    def parser(input: str, index: int) -> ParserResult[Generics | Whitespace, None]:
        match ws.then(just("generic")).unpack_then(ws)(input, index):
            case Ok((index, start_vals)):
                names: list[tuple[Name, Whitespace]] = []
                while True:
                    match name.then(ws)(input, index):
                        case Ok((candidate_index, (candidate_name, candidate_ws))):
                            if candidate_name.value != "end":
                                index = candidate_index
                                names.append((candidate_name, candidate_ws))
                            else:
                                break
                        case Err():
                            break
                match just("end").then(ws)(input, index):
                    case Ok((index, end)):
                        return Ok((index, Generics(*start_vals, names, *end)))
                    case Err():
                        return ws(input, index)
            case Err():
                return ws(input, index)
generics = Generics.parser.debug("generics")

@dataclass
class Implementations:
    inner: Sequence[tuple[Function, Whitespace]] | Whitespace
implementations = ForwardRefParser[Implementations, None](lambda: (Function.parser.then(ws).one_or_more() | ws).map_ok(Implementations))

@dataclass
class Enum:
    start: str
    sep1: Whitespace
    name: NameItem
    generics: Generics | Whitespace
    body: Sequence[tuple[NameItem, Whitespace]] | Whitespace
    end: str

    enummembers: ClassVar[Parser[Sequence[tuple[NameItem, Whitespace]], None]] = ForwardRefParser(lambda: NameItem.parser.then(ws).one_or_more() | ws)
enumbody = Enum.enummembers.then(ws).unpack_then(just("implement")).unpack_then(ws).unpack_then(implementations) | Enum.enummembers
enum = ForwardRefParser(lambda: just("enum").then(ws).unpack_then(NameItem.parser).unpack_then(generics).unpack_then(enumbody).unpack_then(just("end")).star_map_ok(Enum)).debug("enum")

@dataclass
class Record:
    start: str
    sep1: Whitespace
    name: NameItem
    generics: Generics | Whitespace
    body: tuple[NameItem, Whitespace, TypeItem] | tuple[NameItem, Whitespace, TypeItem, Whitespace, RecordMembers] | tuple[RecordMembers, Whitespace, str, Whitespace, Implementations]
    end: str
record = ForwardRefParser(lambda: just("record").then(ws).unpack_then(NameItem.parser).unpack_then(generics).unpack_then(recordbody).unpack_then(just("end")).star_map_ok(Record))
type RecordMembers = tuple[NameItem, Whitespace, TypeItem] | tuple[NameItem, Whitespace, TypeItem, Whitespace, RecordMembers]
recordmembers = ForwardRefParser[RecordMembers, None](lambda: NameItem.parser.then(ws).unpack_then(typeitem) | NameItem.parser.then(ws).unpack_then(typeitem).unpack_then(ws).unpack_then(recordmembers))
recordbody = recordmembers | recordmembers.then(ws).unpack_then(just("implement")).unpack_then(ws).unpack_then(implementations)

@dataclass
class Function:
    inner: tuple[str, Generics | Whitespace, NameItem, Whitespace, TypeItem, Whitespace, TypeItem, Whitespace, BlockItem, Whitespace, str]
    
    parser: ClassVar[Parser[Function, None]] = ForwardRefParser(lambda: just("function").then(generics).unpack_then(NameItem.parser).unpack_then(ws).unpack_then(typeitem).unpack_then(ws).unpack_then(typeitem).unpack_then(ws).unpack_then(Block.blockitem).unpack_then(ws).unpack_then(just("end")).map_ok(Function)).debug("function")

@dataclass
class ExternalFunction:
    inner: tuple[str, Generics | Whitespace, NameItem, Whitespace, TypeItem, Whitespace, TypeItem]
externalfunction = ForwardRefParser[ExternalFunction, None](lambda: just("externalfunction").then(generics).unpack_then(NameItem.parser).unpack_then(ws).unpack_then(typeitem).unpack_then(ws).unpack_then(typeitem).map_ok(ExternalFunction)).debug("externalfunction")

@dataclass
class Ref:
    start: str
    sep1: Whitespace
    name: NameItem
ref = ForwardRefParser(lambda: just("ref").then(ws).unpack_then(NameItem.parser).star_map_ok(Ref)).debug("ref")

type BlockItem = Sequence[tuple[Item, Whitespace]] | Whitespace
@dataclass
class Block:
    start: str
    sep1: Whitespace
    block: BlockItem
    end: str

    blockitem: ClassVar[Parser[BlockItem, None]] = ForwardRefParser(lambda: Item.parser.then(ws).one_or_more() | ws)
block = just("block").then(ws).unpack_then(Block.blockitem).unpack_then(just("end")).star_map_ok(Block).debug("blockstmt")

@dataclass
class Item:
    inner: Number | String | Call | Assign | ForLoop | WhileLoop | Match | Enum | Record | Function | ExternalFunction | Ref | Name | Block

    parser: ClassVar[Parser[Item, None]] = ForwardRefParser(lambda: (number | string | Call.parser | assign | forloop | whileloop | match | enum | record | Function.parser | externalfunction | ref | name | block).map_ok(Item).debug("item"))

@dataclass
class NameItem:
    inner: String | Assign | Enum | Record | Function | Ref | Name
    parser: ClassVar[Parser[NameItem, None]] = ForwardRefParser(lambda: (string | assign | enum | record | Function.parser | ref | name).map_ok(NameItem).debug("nameitem"))

type TypeItem = Name |  tuple[Name, Whitespace, str, Whitespace, TypeItemGenerics, Whitespace, str]
typeitem: Parser[TypeItem, None] = ForwardRefParser(lambda: name | name.then(ws).unpack_then(just("of")).unpack_then(ws).unpack_then(typeitemgenerics).unpack_then(ws).unpack_then(just("end"))).debug("typeitem")
type TypeItemGenerics = tuple[Name, Whitespace, TypeItem] | tuple[Name, Whitespace, TypeItem, Whitespace, TypeItemGenerics]
typeitemgenerics: Parser[TypeItemGenerics, None] = ForwardRefParser(lambda: name.then(ws).unpack_then(typeitem) | name.then(ws).unpack_then(typeitem).unpack_then(ws).unpack_then(typeitemgenerics))

print(Block.blockitem(open("interpreters/builtins.plrm").read(), 0))
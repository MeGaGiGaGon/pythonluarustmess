from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Literal, overload, override

type ParserResult[O] = tuple[O, int]
type ParserFunc[I, O] = Callable[[Sequence[I], int], ParserResult[O]]


class Parser[I, O, P: (Literal[True], Literal[False])](ABC):
    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @abstractmethod
    def predicate(self) -> Sequence[Sequence[I]] | None: ...

    @abstractmethod
    def func(self) -> ParserFunc[I, O]: ...

    @abstractmethod
    def with_new_func[U](self, func: ParserFunc[I, U]) -> Parser[I, U, P]: ...

    def __call__(self, input: Sequence[I], index: int) -> ParserResult[O]:
        return self.func()(input, index)

    def then[OO, OP: (Literal[True], Literal[False])](
        self, other: Parser[I, OO, OP]
    ) -> Parser[I, tuple[O, OO], P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[O, OO]]:
            res, index = self(input, index)
            res2, index = other(input, index)
            return (res, res2), index

        return self.with_new_func(inner)

    def then_unpack[*TS, OP: (Literal[True], Literal[False])](
        self, other: Parser[I, tuple[*TS], OP]
    ) -> Parser[I, tuple[O, *TS], P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[O, *TS]]:
            res, index = self(input, index)
            res2, index = other(input, index)
            return (res, *res2), index

        return self.with_new_func(inner)

    def map[OO](self, func: Callable[[O], OO]) -> Parser[I, OO, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            res, index = self(input, index)
            return func(res), index

        return self.with_new_func(inner)

    def star_map[*TS, OO](
        self: Parser[I, tuple[*TS], P], func: Callable[[*TS], OO]
    ) -> Parser[I, OO, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            res, index = self(input, index)
            return func(*res), index

        return self.with_new_func(inner)


class PredicateParser[I, O](Parser[I, O, Literal[True]]):
    def __init__(
        self, func: ParserFunc[I, O], predicate: Sequence[Sequence[I]]
    ) -> None:
        self._func: ParserFunc[I, O] = func
        self._predicate: Sequence[Sequence[I]] = predicate

    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @override
    def predicate(self) -> Sequence[Sequence[I]] | None:
        return self._predicate

    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func

    @override
    def with_new_func[U](self, func: ParserFunc[I, U]) -> PredicateParser[I, U]:
        return PredicateParser(func, self._predicate)


class SimpleParser[I, O](Parser[I, O, Literal[False]]):
    def __init__(self, func: ParserFunc[I, O]) -> None:
        self._func: ParserFunc[I, O] = func

    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @override
    def predicate(self) -> Sequence[Sequence[I]] | None:
        return None

    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func

    @override
    def with_new_func[U](self, func: ParserFunc[I, U]) -> SimpleParser[I, U]:
        return SimpleParser(func)


class ForwardRefParser[I, O](Parser[I, O, Literal[False]]):
    def __init__(self, func: Callable[[], ParserFunc[I, O]]) -> None:
        self._func: Callable[[], ParserFunc[I, O]] = func

    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @override
    def predicate(self) -> Sequence[Sequence[I]] | None:
        return None

    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func()

    @override
    def with_new_func[U](self, func: ParserFunc[I, U]) -> SimpleParser[I, U]:
        return SimpleParser(func)


def chain[I, O](*parsers: Parser[I, O, Literal[True]]) -> Parser[I, O, Literal[True]]:
    new_predicates: list[Sequence[I]] = []
    for parser in parsers:
        for predicate in parser.predicate():
            for higher_precedence_predicate in new_predicates:
                if len(predicate) < len(higher_precedence_predicate):
                    continue
                if all(
                    predicate[index] == higher_precedence_predicate[index]
                    for index in range(len(higher_precedence_predicate))
                ):
                    msg = f"Predicate {predicate!r} is overlapped by shorter predicate {higher_precedence_predicate!r} and will never apply"
                    raise ValueError(msg)
            new_predicates.append(predicate)

    def inner(input: Sequence[I], index: int) -> ParserResult[O]:
        for parser in parsers:
            for seq in parser.predicate():
                seq_index = 0
                temp_index = index
                while temp_index < len(input) and seq_index < len(seq):
                    if input[temp_index] != seq[seq_index]:
                        break
                    seq_index += 1
                    temp_index += 1
                if seq_index < len(seq):
                    continue
                return parser(input, index)
        msg = f"No parser predicates matched the input\nSample of input: {input[index:10]!r}\n{new_predicates=!r}"
        raise ValueError(msg)
    return PredicateParser(inner, new_predicates)


def just_seq[I](seq: Sequence[I]) -> PredicateParser[I, Sequence[I]]:
    def inner(input: Sequence[I], index: int) -> ParserResult[Sequence[I]]:
        seq_index = 0
        while index < len(input) and seq_index < len(seq):
            if input[index] != seq[seq_index]:
                msg = f"Expected {seq[seq_index]!r} (part of {seq=!r}), got {input[index]} ({index=})"
                raise ValueError(msg)
            seq_index += 1
            index += 1
        if seq_index < len(seq):
            msg = f"Expected {seq[seq_index]!r} (part of {seq=!r}), but input ran out at {index=}"
            raise ValueError(msg)
        return seq, index

    return PredicateParser(inner, [seq])

foo = chain(
    just_seq("a").then(ForwardRefParser(lambda: foo)).map(lambda x: [*x[0], *x[1]]),
    just_seq("b")
)

print(foo("b", 0))
print(foo("ab", 0))
print(foo("aab", 0))
print(foo("aaab", 0))
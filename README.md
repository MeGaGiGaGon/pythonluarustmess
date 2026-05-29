# pythonrustluamess

While designing a python-like language with rust style enums/structs,
I got distracted by being able to make the language have no special
symbols by using lua-like syntax. This cursed abomination is the
result.

### From Rust:
- Enums
- Structs (renamed to records)
- impl blocks

### From Python:
- Semi-static dynamic typing
- Method inheritance
- Lost of standard library things

### From Lua:
- Syntax

## Features/Syntax
### McKeeman Form Grammar
```
ws
  wsitem
  wscomment ws
  wsitem ws

wsitem
  '0020'
  '000A'
  '000D'
  '0009'

wscomment
  wsitem comment wsitem

number
  "number" ws digits ws "end"

digits
  digit
  digit ws digits

digit
  "zero"
  "one"
  "two"
  "three"
  "four"
  "five"
  "six"
  "seven"
  "eight"
  "nine"

chars
  '0020' . '10FFFF' chars
  '0020' . '10FFFF'

string
  "string" string "end"
  "string" ws chars ws "end"

comment
  "comment" comment "end"
  "comment" ws chars ws "end"

call
  "call" ws item ws item ws item

assign
  "assign" ws nameitem ws item

forloop
  forlooptype ws nameitem ws "in" ws item ws block ws "end"

forlooptype
  "for"
  "forcollect"

whileloop
  whilelooptype ws item ws block ws "end"

whilelooptype
  "while"
  "whilecollect"

match
  "match" ws item ws cases ws "end"

cases
  item ws item
  item ws item ws cases

generics
  ws "generics" ws genericnames ws "end" ws
  ws

genericnames
  name
  name ws genericnames

enum
  "enum" ws nameitem generics enumbody ws "end"

enumbody
  enummembers
  enummembers ws "implement" ws implementations

enummembers
  nameitem
  nameitem ws enummembers

record
  "record" ws nameitem generics recordbody ws "end"

recordbody
  recordmembers
  recordmembers ws "implement" ws implementations

recordmembers
  nameitem ws typeitem
  nameitem ws typeitem ws recordmembers

implementations
  function
  function ws implementations

function
  "function" ws nameitem ws typeitem ws "to" ws typeitem ws "end"

ref
  "ref" ws nameitem

name
  '0021' . '10FFFF'
  '0021' . '10FFFF' name

block
  "block" ws blockitem ws "end"

blockitem
  item
  item ws blockitem

item
  number
  string
  call
  assign
  forloop
  whileloop
  match
  enum
  record
  function
  ref
  name
  block

nameitem
  string
  assign
  enum
  record
  function
  ref
  name

typeitem
  name
  name ws "of" ws typeitemgenerics ws "end"

typeitemgenerics
  name ws typeitem
  name ws typeitem ws typeitemgenerics
```

### Expression-based
All code in prlm is an expression with a return value.

### Strings
Strings use the `string` keyword to start, and `end` to end.
```
string Hello end
```
The string contents do not include the leading and trailing whitespace

#### Curesed Thing:
To escape the word "string" or "end" inside a string, add more
`string`s and `end`s:
```
stringstring This string ends endend
```

### Comments
Comments act the same as strings, except can be used in the middle of
other code without affecting it.
```
comment Hello end
```

### Enums
Returns the newly created enum
```
enum MyEnum
  VariantA
  VariantB
end
```

### Records
Returns the newly created record
```
record MyRecord
  fieldOne String
  fieldTwo Integer
end
```

### Functions
#### Cursed Thing:
Functions only ever take one argument.

You must use a record/enum to pass in more than one value at a time.

The value of the argument is stored in the auto-created variable `input`

Functions auto-return the last computed value
```
function double Integer to String
  call input add input 
end
```

#### Cursed Thing:
Calling functions

To call a function, use the `call` keyword.

The call uses the syntax:
```
call <value to call on> <function to call> <input to function>
```

For calling an object itself, pass `Empty` for `<value to call on>`:
```
call Empty double dec one end comment Returns two end
```

### Integers
Numbers must have their base specified, then each digit one after another. 
```
hex F seven end
dec two four seven end
oct three six seven end
bin one one one one zero one one one end
```


## Tests
Tests are done through markdown files.

Only the `plrm` block is required, all others are optional and can be ignored.

\`\`\`plrm
Code here
\`\`\`

\`\`\`stdin
Input here
\`\`\`

\`\`\`stdout
Output here
\`\`\`

\`\`\`return
plrm code constructing a return value
\`\`\`

The `plrm` block can be suffixed with `collect` to collect all results instead
of just the last one:
\`\`\`plrmcollect
Code here
\`\`\`

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

The `stdin`, `stdout`, and `return` blocks can be suffixed with `python` to run
python code to generate the input instead of hard-coding it:
\`\`\`stdoutpython
Python code here
\`\`\`

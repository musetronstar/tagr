# tagr

`tagr` translates natural language  text from `STDIN` into TAGL on `STDOUT`.

In this prototype form, it is a *structural translator* in that it produces
output in the *shape* of valid TAGL statements. It will try to produce valid
output even in the face of input errors - analagous to how web browsers
still do their best to produce a valid DOM tree in the face of HTML errors.

In the future, we might add options for strict semantic validation
where the tags must be defined having the correct tagd POS types.

## Usage

```bash
echo "tagd is a semantic-relational engine" | tagr
>> tagd is_a semantic_relational_engine;
```

### tagd POS hints

`tagr` also accepts:

```text
--hint <tagd_pos>=<value>
```

Hints constrain translation using tagd POS roles such as
`subject`, `sub_relator`, `relator`, `object`, etc.
The tagd POS hint should use the same name defined in the `../tagd/tagl/src/parser.y` TAGL grammer

Each hint value must be present in the input text. The hint does not inject
new text into the input stream; it helps `tagr` identify and group structure
that is already present.

## Examples

### Subordinate relation

Input:

```text
dog is a mammal
```

Output:

```tagl
>> dog is_a mammal;
```

### Predicate

Input:

```text
dog can bark
```

Output:

```tagl
>> dog can bark;
```

### Predicate with modifier / quantifier

Input:

```text
A dog has 4 legs and a tail.
```

Output:

```tagl
>> dog has legs = 4, tail;
```

### Subordinate relation with predicate

Input:

```text
dog is a mammal and can bark
```

Output:

```tagl
>> dog is_a mammal
can bark;
```

### Subordinate relation with predicate and modifier / quantifier

Input:

```text
A dog is a mammal that can bark, has 4 legs and a tail.
```

Output:

```tagl
>> dog is_a mammal
can bark
has legs = 4, tail;
```

Constrains "age" to the tagd POS `<subject>`.

```bash
echo "age how old a person or thing is" | tagr --hint subject=age
```

## Maxim

All that tagr does is,
Bytes in -> TAGL out:
+ STDIN - bytes
+ STOUT - correct TAGL, comments
- STDERR - TAGL errors, logged events (default, but syslog style facilities later)


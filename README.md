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

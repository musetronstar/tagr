# tagr

`tagr` is a Python prototype that translates English text from `STDIN` into TAGL on `STDOUT`.

## Usage

```bash
echo "tagd is a semantic-relational engine" | tagr
>> tagd is_a semantic_relational engine;
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

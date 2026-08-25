# Math and Dollar-Sign Content

A corpus of every math notation in common use, plus every ordinary use of `$` that must
not be mistaken for math.

Formatting this document must not change a single non-whitespace character, must not
introduce a newline inside an inline math span, and must not collapse a display block
onto one line. Reflowing the surrounding prose is expected and fine.

Long cases carry filler so the wrap column falls *inside* the construct. That is the
condition most of these defects need, and the reason a short example proves nothing.

## Part A: Inline Forms

### A1. Dollar inline, short

Inline math: $E = mc^2$ is famous.

### A2. Dollar inline, crossing the wrap column

Filler words to push the formula across the wrap column boundary here now ok $a + b + c + d$ tail.

### A3. Dollar-dollar on one line, crossing the wrap column

Filler words to push the formula across the wrap column boundary here now ok $$a + b + c + d$$ tail.

### A4. LaTeX paren delimiters, crossing the wrap column

Filler words to push the formula across the wrap column boundary here now ok \(a + b + c + d\) tail.

### A5. GitLab dollar-backtick, crossing the wrap column

Filler words to push the formula across the wrap column boundary here now ok $`a + b + c + d`$ tail.

### A6. MyST math role, crossing the wrap column

Filler words to push the formula across the wrap column boundary here now ok {math}`a + b + c + d` tail.

### A7. Several spans in one paragraph

Given $a > 0$ and $b > 0$, the identity $\sqrt{ab} \le \tfrac{1}{2}(a + b)$ holds, with equality exactly when $a = b$, which is the arithmetic-geometric mean inequality.

## Part B: Block Forms

### B1. Display block, single line interior

$$
L = \frac{1}{2} \rho v^2 S C_L
$$

### B2. Display block, multi-line interior

$$
\begin{aligned}
a &= b + c \\
d &= e + f
\end{aligned}
$$

### B3. LaTeX bracket delimiters

\[
a + b = c
\]

### B4. LaTeX environment, no outer delimiters

\begin{equation}
E = mc^2
\end{equation}

### B5. Fenced math block, GitHub and GitLab

```math
\frac{a}{b} + c
```

### B6. Fenced math directive, MyST

```{math}
a + b = c
```

### B7. Display block with a MyST label

$$
a + b = c
$$ (my-label)

## Part C: Interiors That Collide With Markdown

Each interior contains characters that flowmark treats as meaningful in prose. All cross
the wrap column, so the fragment landing at the start of a wrapped line is the one at
risk of being escaped.

### C1. Underscores, which prose would read as emphasis

Filler words to push the formula across the wrap column boundary here now ok $x_1 + x_2 + y_1$ tail.

### C2. Asterisks, which prose would read as emphasis or a bullet

Filler words to push the formula across the wrap column boundary here now ok $a * b * c * d$ tail.

### C3. A plus, which prose would read as a list bullet

Filler words to push the formula across the wrap column boundary here now ok $a + b + c + d$ tail.

### C4. A minus, which prose would read as a list bullet

Filler words to push the formula across the wrap column boundary here now ok $a - b - c - d$ tail.

### C5. A greater-than, which prose would read as a blockquote

Filler words to push the formula across the wrap column boundary here now ok $a > b > c > d$ tail.

### C6. A hash, which prose would read as a heading

Filler words to push the formula across the wrap column boundary here now ok $a \# b \# c$ tail.

### C7. Numerals with periods, which prose would read as an ordered list

Filler words to push the formula across the wrap column boundary here now ok $a + 1. b + 2. c$ tail.

### C8. An apostrophe, which the typographer would curl

Only an apostrophe between two word characters is curled, so these two lines differ:
$x'y$ is rewritten and $f'(x)$ is not. Both are valid TeX and neither may change.

Short line with a transposed product $x'y$ and an index $n'th$ here.

Filler words to push the formula across the wrap column boundary here now ok $f'(x) + g'(x)$ tail.

### C9. Straight quotes, which the typographer would curl

Filler words to push the formula across the wrap column boundary here now ok $x = "a" + "b"$ tail.

### C10. Three dots, which the typographer would turn into an ellipsis

Filler words to push the formula across the wrap column boundary here now ok $a_1, ..., a_n$ tail.

### C11. Double hyphen, which the typographer would turn into a dash

Filler words to push the formula across the wrap column boundary here now ok $a -- b -- c$ tail.

### C12. Backslash commands

Filler words to push the formula across the wrap column boundary here now ok $\frac{a}{b} + \frac{c}{d}$ tail.

### C13. Nested backticks inside a span

A code span containing a backtick, `` ` ``, next to math $a + b$ on the same line.

## Part D: Dollars That Are Not Math

None of these may be recognised as math, and all of them format correctly today. They
are here as regression cover for the delimiter rule.

### D1. A single currency amount

Short line costs $100 only.

### D2. Two currency amounts on one line

Filler words to push the formula across the wrap column boundary here now ok costs $100 and $200 total.

### D3. Currency across the wrap column

Filler words to push the formula across the wrap column boundary here now ok it costs $100 and then $200 more, ok.

### D4. Escaped dollars

Filler words to push the formula across the wrap column boundary here now ok costs \$100 and \$200 total.

### D5. Shell variables

Filler words to push the formula across the wrap column boundary here now ok set $HOME and $PATH now.

### D6. A trailing lone dollar

Filler words to push the formula across the wrap column boundary here now ok the price in $ is high.

### D7. A lone dollar mid-sentence

Filler words to push the formula across the wrap column boundary here now ok a lone $ sign here.

### D8. A closing dollar followed by a digit

Filler words to push the formula across the wrap column boundary here now ok $a+b$5 tail.

### D9. Dollars inside a code span

Filler words to push the formula across the wrap column boundary here now ok run `$ echo $HOME` now.

### D10. Dollars inside a code fence

```bash
$ echo $HOME
cost=$100
```

### D11. Math and currency interleaved, from the reference document

If the noteholders had converted their $420K at the 20% discount, they would be paying $\$0.55116 \times \$0.80$ per share, or $0.44093 per share. And $\$420K \div 0.44093$ is $952{,}532$ shares.

### D12. Currency in a table cell

| Item | Price | Formula |
| --- | --- | --- |
| Widget | $100 | $a + b$ |
| Gadget | $250 | $c \times d$ |

## Part E: Malformed and Ambiguous

These have no correct rendering in any dialect. The requirement is only that flowmark
degrade safely: do not crash, do not delete, do not add characters. Whatever it does with
them, it must keep doing consistently.

### E1. An unclosed inline span

Filler words to push the formula across the wrap column boundary here now ok an unclosed $a + b here.

### E2. Dollars in separate paragraphs, which must never pair

Para one has $a and more text to make this paragraph long enough to wrap somewhere.

Para two has b$ and more text to make this paragraph long enough to wrap somewhere.

### E3. An unclosed display block

$$
a + b = c

Text following an unterminated display opener.

### E4. Mismatched single and double delimiters

Filler words to push the formula across the wrap column boundary here now ok $$a + b$ tail.

### E5. Whitespace immediately inside the delimiters

Not math under the Pandoc or GitHub rules, because the opening delimiter is followed by a
space.

Filler words to push the formula across the wrap column boundary here now ok $ a + b + c + d $ tail.

### E6. An empty span

Filler words to push the formula across the wrap column boundary here now ok an empty $$ pair here.

### E7. A span containing a newline in the source

Inline math is single-line in every dialect, so this is two lone dollars, not a span: $a +
b$ across the break.

### E8. Adjacent spans with no separator

Filler words to push the formula across the wrap column boundary here now ok $a$$b$ tail.

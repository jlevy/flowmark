# Math and Dollar-Sign Content

A broad integration corpus for common math notations, Markdown contexts, parser
collisions, and ordinary dollar-sign prose.

Formatting must preserve every recognized math slice exactly after Flowmark's documented
newline normalization. It must not introduce a line ending inside inline math or collapse
a display block. Dollar-shaped prose must remain byte-safe even when the preservation-
biased recognizer conservatively treats a balanced pair as atomic. Reflowing surrounding
prose is expected.

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

### A8. Pandoc intraword forms

Water is H$_2$O, a coefficient may be written 1$a$, and a formula may be followed
immediately by a letter as in $a$B.

### A9. Whitespace-padded dollar math

MyST can allow padding inside single-dollar math, so $ a + b $ is protected by default
without asking Flowmark which dialect authored it.

### A10. Closing dollar followed by a digit

The preservation-biased union accepts $a$2 even though stricter dialects may reject it.

### A11. Soft newline inside inline math

Pandoc accepts a soft newline inside inline math, and Flowmark must retain the authored
break in $a +
b$ rather than adding, removing, or relocating it.

### A12. Unicode adjacency and combining marks

Inline forms may touch non-ASCII text: 水$x_1$量, α$e^{iπ}$β, and $á + b̂$ all remain
intact.

### A13. Soft newline inside a blockquote

> Quoted prose before the formula $a +
> b$ continues after its authored break.

### A14. Math in link text

A [linked formula $a + b$](https://example.com/math) keeps both syntaxes intact.

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

### B8. Display block in a blockquote

> $$
> \begin{aligned}
> a &= b + c \\
> d &= e + f
> \end{aligned}
> $$ (quoted-equation)

### B9. Display block in a list item

- $$
  a + b = c
  $$ {#listed-equation}

### B10. Starred and nested environments

\begin{align*}
a &= b + c \\
\begin{gathered}
d &= e + f
\end{gathered}
\end{align*}

### B11. Custom environment name

\begin{proof@draft}
Text-like tokens _inside_ a custom environment remain source text.
\end{proof@draft}

### B12. Bracket display inside nested containers

- > \[
  > a + b = c
  > \]

## Part C: Interiors That Collide With Markdown

Each interior contains characters that Flowmark treats as meaningful in prose. Long cases
also cross the wrap column so the fragment landing at the start of a wrapped line is at
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

### C14. Double underscores parsed as emphasis

Short math $\text{__init__}$ tail.

### C15. Markdown emphasis, links, and images in a formula body

Short math $a *b* + [x](target) + ![y](image.png)$ tail.

### C16. Entities, HTML, and backticks in a formula body

Short math $&amp; + <tag> + \text{`literal`}$ tail.

### C17. TeX comments and line-sensitive content

$$
a + b % this comment and its line ending are significant
+ c
$$

## Part D: Dollar-Shaped Prose and Escape Parity

These cases must remain byte-safe. Balanced currency and shell examples may be treated as
atomic by the preservation-biased default; that conservative classification is preferable
to mutating a valid math form in another dialect.

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

An unclosed currency dollar in one cell must never pair with a math dollar in the next
cell and hide the structural pipe from the table parser.

| Item | Price | Formula |
| --- | --- | --- |
| Widget | $100 | $a + b$ |
| Gadget | $250 | $c \times d$ |

### D13. One backslash before an opener

Odd escape parity leaves \$a$ outside the math recognizer.

### D14. Two backslashes before an opener

Even escape parity allows \\$a + b$ to open a protected span.

### D15. Three backslashes before an opener

Odd escape parity leaves \\\$a$ outside the math recognizer.

### D16. Four backslashes before an opener

Even escape parity allows \\\\$a + b$ to open a protected span.

### D17. Escaped and active candidate closers

The escaped dollar inside $a + b\$ + c$ stays in the body, while the final active dollar
closes it. With even parity, $a + b\\$ ends at that dollar and leaves the slashes intact.

## Part E: Malformed and Ambiguous

These cases are invalid or ambiguous in at least one dialect. Flowmark must not crash,
emit an internal token, or let an unmatched block opener consume unrelated trailing
prose. Exact committed output and a second pass define safe, deterministic degradation.

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

MyST can enable this single-dollar form. The preservation-biased default accepts it even
though Pandoc and GitHub use narrower whitespace rules.

Filler words to push the formula across the wrap column boundary here now ok $ a + b + c + d $ tail.

### E6. An empty span

Filler words to push the formula across the wrap column boundary here now ok an empty $$$$ double-dollar span here.

### E7. A span containing a newline in the source

This repeats the permissive Pandoc boundary in a deliberately awkward sentence: $a +
b$ across the break must remain one protected span.

### E8. Adjacent spans with no separator

Filler words to push the formula across the wrap column boundary here now ok $a$$b$ tail.

### E9. Mismatched environment closer

\begin{align*}
a + b = c
\end{equation}

Text after a mismatched closer must not disappear into an opaque suffix.

### E10. Unmatched outer environment with a closed nested environment

\begin{outer}
\begin{inner}
a + b = c
\end{inner}

Text after the unmatched outer environment remains independently formattable.

### E11. Unmatched double-dollar opener before valid single-dollar math

An unmatched $$ opener before later valid $a + b$ math must not suppress the closed inner
candidate when the outer candidate is discarded.

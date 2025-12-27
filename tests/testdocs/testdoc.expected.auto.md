---
title: Test Document
author: Test Author
date: 2023-01-01
tags:
  - markdown
  - formatting
  - test
---
## Test document

This is a simple test document to verify Flowmark usage.
It’s sort of a “transparent box” test of the Flowmark auto-formatter.
Re-run Flowmark and compare output.

*[Everything is
Free](https://open.spotify.com/track/0H8ukN2MIW2iNvqJP1kb4O?si=PWBwK6QgS8Siksuwbt4K0A)
by Gillian Welch*

The dangers of ‘culture fit’.

> The dangers of ‘culture fit’.

The [ways equity can be granted](#how-equity-is-granted) as compensation—including
restricted stock, stock options, and restricted stock units—are **notoriously complex**.
Equity compensation involves confounding terminology, legal obscurities, and many
high-stakes decisions for those who give and *receive it*. Blah blah blah and blah.

- **[Signing bonus](https://www.investopedia.com/terms/s/signing-bonus.asp).** Cash you
  get just for signing.
  (Signing bonuses usually have some strings attached—for example, you could have to pay
  back the bonus if you leave the company within 12 or 24 months.)

- **Cashless exercise**: In the event of an IPO, a broker can allow you to exercise all
  of your vested options and immediately sell a portion of them into the public market,
  removing the need for cash up front to exercise and pay taxes.

- Filenames and packages: `some-package`, `some-file.js` (to fit standard Node/npm
  conventions)

### A subsection with some citations

- Mark P. Cussen, Investopedia, [*Introduction To Incentive Stock
  Options*](http://www.investopedia.com/articles/stocks/12/introduction-incentive-stock-options.asp),
  updated 2017.

- Alex MacCaw, [*An Engineer’s Guide to Stock
  Options*](http://blog.alexmaccaw.com/an-engineers-guide-to-stock-options), 2013.

- Andy Rachleff, Wealthfront, [*The 14 Crucial Questions about Stock
  Options*](https://blog.wealthfront.com/stock-options-14-crucial-questions), 2014.

### Command Execution

- `command` - Name of kash command or action to execute

- `args` - Arguments as comma-separated string or individual `arg_0`, `arg_1`, etc.

- Additional parameters become options (e.g., `model=gpt-4o`, `language=en`)

[^uptimenote]: In engineering, “counting nines” traditionally refers to *service
    availability* (uptime)—99.99% uptime means ≤ 52 minutes of downtime per year.

## Some apostrophes and quotes--and dashes, too

“Hello,” he said! “What’s … your specialty?”
he enquired (in an idle tone).

He read the multiline quote: “This is line one and this is line two and finally line
three.” It was beautiful.

She whispered ‘Remember this important message’ softly.

The stated reason—“I’m working on myself”—may be sincere on one level.

* **From his Autobiography (1967-69):**

  + **On His Life’s Vision ("Reflections on My Eightieth Birthday"):** “I have lived in
    the pursuit of a vision, both personal and social.
    Personal: to care for what is noble, for what is beautiful, for what is gentle; to
    allow moments of insight to give wisdom at more mundane times.
    Social: to see in imagination the society that is to be created, where individuals
    grow freely, and where hate and greed and envy die because there is nothing to
    nourish them. These things I believe, and the world, for all its horrors, has left me
    unshaken”.

Cas’ surprise at John’s question hung over them both for a brief moment, like a thinly
disguised sack of potatoes.
“From 2002-2004 I specialized in the Sarbanes-Oxley Act (Pub.L. 107–204, 116 Stat.
745, enacted July 30, 2002), which was known (in the House) as the 'Corporate and
Auditing Accountability, Responsibility, and Transparency Act' and--” But here he cut
her off! And who could blame him?
He had spoken with the FBI. There was no time to lose.

These companies add (or “issue”) stock.

Dash--dash. Dash -- dash.
Dash -- dash.

10-20 10–20 10—20.

10 - 20 10 – 20 10 — 20.

a-b a–b a—b.

a - b a – b a — b.

## Math

This is a display formula:

$$ L = \frac{1}{2} \rho v^2 S C_L $$

And here is a formula in inline form as $L = \frac{1}{2} \rho v^2 S C_L$ with more text
following. If the noteholders had converted their $420K at the 20% discount, they would
be paying $\$0.55116 \times \$0.80$ per share, or $0.44093 per share.
And $\$420K \div 0.44093$ is $952{,}532$ shares.

## Legalese

> ⚖️
> 
> ↔️ CONVERTIBLE PROMISSORY NOTE
> 
> Note Series: `___________________________`
> 
> e. **Amendment and Waiver.** Any term of this Note may be amended or waived with the
> written consent of Company and the Majority Holders.
> 
> f. **Governing Law; Venue.** This Note shall be governed by and construed under the
> laws of the State of `________`, as applied to agreements among `_______` residents,
> made and to be performed entirely within the State of `______`, without giving effect
> to conflicts of laws principles.
> The venue for any dispute arising out of or related to this Note will lie exclusively
> in the state or federal courts located in King County, Washington, and the parties to
> this Note irrevocably waive any right to raise forum non conveniens or any other
> argument that King County, Washington is not the proper venue.
> The parties to this Note irrevocably consent to personal jurisdiction in the state and
> federal courts of the state of Washington.

> iv. **Further Limitations on Disposition.** Without in any way limiting the
> representations set forth above, the Holder further agrees not to make any disposition
> of all or any portion of the Securities unless and until:
> 
> 1\. There is then in effect a registration statement under the Act covering such
> proposed disposition and such disposition is made in accordance with such registration
> statement; or

## Typical ChatGPT Output

| **Feature** | **OpenAPI 3.1** | **OpenAI tool schema** | **Anthropic tool schema** | **Model Context Protocol (MCP) 2025-06-18** | **Pydantic v2 generated schema** |
| --- | --- | --- | --- | --- | --- |
| **Primary scope** | Full REST contract: paths, verbs, auth, servers **plus** data shapes | *Input-only* definition of a function’s parameters for `/chat/completions` `tools=[…]` | Same for `/v1/messages` `tools=[…]`; also used in Claude server-tools | Tool discovery & invocation over JSON-RPC / SSE; adds output contract & rich result types | In-process data validation; can emit JSON-Schema or OpenAPI components |
| **Where it lives / transport** | `.yaml`/`.json` served over HTTPS or bundled with code | Embedded inside a chat request | Embedded inside a chat request | Separate MCP server; clients list and call tools via `tools/*` RPC methods | Python code emits schema at runtime (`model_json_schema()` or `.schema_json()`) |
| **JSON-Schema dialect** | Official OAS dialect, built on **draft 2020-12**([spec.openapis.org][1]) | Fixed **draft 07 subset** (no `$ref` across docs, no `oneOf` of heterogeneous types)([community.openai.com][2], [community.openai.com][3]) | **draft 2020-12** (full vocabulary)([docs.anthropic.com][4]) | **draft 2020-12** for both `inputSchema` & `outputSchema`([modelcontextprotocol.io][5]) | **draft 2020-12** (and emits OpenAPI 3.1 when asked)([docs.pydantic.dev][6]) |
| **Advanced keywords allowed** (`$ref`, `oneOf`, `allOf`, `format`, …) | All JSON-Schema 2020-12, plus OAS extensions | **Limited** – many validators ignored, `$ref` must stay within the same object | **Allowed** – `$ref`, `enum`, `oneOf`, formats, examples | Fully allowed; additionally supports `annotations` object for T\&S metadata | Whatever the target dialect allows; user may disable/enable `$ref` flattening |
| **Output schema support** | Yes (`components.schemas`, responses) | **No** – output is free-form chat or follow-up `tool` message | **No** (planned) | **Yes** – `outputSchema` field; clients are encouraged to validate results([modelcontextprotocol.io][5]) | Yes – any Pydantic model’s JSON-Schema can describe outputs |
| **Streaming / partial results** | Via HTTP chunked or SSE, not part of schema | Supported in chat streaming but schema is unaffected | `stream:"auto"` yields incremental `tool_use` blocks | Built-in: server can stream intermediate `notifications/tools/*` & progress events | Not applicable (library) |
| **Runtime validation guarantee** | External validators or server framework (e.g., FastAPI) | **Caller must validate**; model may hallucinate | **Caller must validate** | MCP server **must** validate both inputs & outputs | Core-runtime C/Rust validation; raises `ValidationError` on failure |
| **Versioning cadence** | IETF-style spec; v3.1 is current | Implicit in OpenAI API releases | Versioned via `anthropic-version` header; schema fields stable | dated revisions (e.g., 2025-06-18) with change log | Semantic-versioned PyPI releases |
| **Typical Python authoring flow** | FastAPI/Django-Ninja introspect **Pydantic** models and function signatures to emit spec | Dicts or libraries like **Instructor**, LangChain, your `FunctionDescription` helper | `anthropic.tools` helper (wraps Pydantic/TypedDict) | `@mcp.tool` decorator in the reference SDK auto-derives schema from type hints | `class Model(BaseModel)…` or `@validate_call` on a function |
| **Notable limitations / gotchas** | Large; learning curve, must keep paths & refs consistent | *Must* root at `{type:"object"}`; no circular `$ref`; 64-char `name`; rejects empty `properties` | 16-KB per-tool limit; still beta; server-tool names are versioned (`web_search_20250305`) | Requires running MCP server; JSON-RPC adds another hop; security model still maturing | Performance slower than **msgspec**; still Python focused (no on-wire format) |

#### Key points

* **OpenAPI 3.1** is the most *expressive* and HTTP-oriented.

* **OpenAI’s schema** is the *smallest*, locked to draft-07, input-only.

* **Anthropic’s schema** lets you use *full* 2020-12, so the same Pydantic model works
  unchanged.

* **MCP** generalises tooling across vendors, adds output validation, discovery, and
  progress streams.

* **Pydantic v2** remains the Python “source-of-truth” generator: you can compile the
  **same** model into OpenAPI, plain JSON-Schema, OpenAI-tools, Anthropic-tools, or MCP
  definitions with one line of code.

[1]: https://spec.openapis.org/oas/3.1/dialect/2024-11-10.html "JSON Schema dialect for OpenAPI | OpenAPI Initiative Publications"
[2]: https://community.openai.com/t/the-assistant-will-never-recognize-a-required-parameter-that-is-of-object-type-in-function-tools/614154?utm_source=chatgpt.com "The Assistant will never recognize a required parameter that is of ..."
[3]: https://community.openai.com/t/extended-or-minimal-schemas-for-tool-parameters/578636?utm_source=chatgpt.com "Extended or minimal Schemas for tool parameters? - API"
[4]: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview "Tool use with Claude - Anthropic"
[5]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools "Tools - Model Context Protocol"
[6]: https://docs.pydantic.dev/latest/concepts/json_schema/ "JSON Schema - Pydantic"

## Wrapping tests

### Some wrapping

William F. Buckley Jr.
was coming to breakfast.
Buckley was born November 24, 1925, in
[New York City](https://en.wikipedia.org/wiki/New_York_City), the son of Aloise
Josephine Antonia (Steiner) and William Frank Buckley Sr., a
[Texas](https://en.wikipedia.org/wiki/Texas)-born lawyer and oil developer.
His mother, from New Orleans, was of Swiss-German, German, and Irish descent, while his
paternal grandparents, from Hamilton, Ontario, Canada, were of Irish ancestry.
The sixth of ten children, Buckley moved as a boy with his family to Mexico, and then to
Sharon, Connecticut, before beginning his formal schooling in Paris, where he attended
first grade. By age seven, he received his first formal training in English at a day
school in London; his first and second languages were Spanish and French.
As a boy, Buckley developed a love for music, sailing, horses, hunting, and skiing.
All of these interests would be reflected in his later writings.
Just before World War II, at age 12–13, he attended the Catholic preparatory school [St.
John’s Beaumont School](https://en.wikipedia.org/wiki/St_John%27s_Beaumont_School) in
England.

The U.S. holds 50% of the global startup investment pool, down from 95% in the 1990s.
(This data is
[summarized](https://www.inc.com/leigh-buchanan/american-businesses-no-longer-dominate-venture-capital.html)
in *Inc.*; the [full report](http://startupsusa.org/global-startup-cities/) was
conducted by the Center for American Entrepreneurship.)

“You start getting entrepreneur of the year awards from Harvard Business School.
Investment bankers are staking out your house.
You could eat free for a year at Buck’s.” —Marc Andreessen[^a16zcom201.ufg7ag]

### A few paragraphs and bullets

A good heuristic is to assume your readers will be **100% intelligent and 100%
ignorant**. Of course, in reality, varied experience exists within an individual reader.
Most people may already know *something*, and some people are quicker learners than
others. Even world class experts most likely only really know parts of a subject, and
contributors may have practical experience in one role--perhaps they have been an
entrepreneur, for example, but not an investor.
So writing with the assumption that each reader could be both has a variety of
advantages:

- Assuming 100% ignorance will help people who think they know a lot about a subject
  understand **what they didn’t know they didn’t know**, and fill in the gaps in their
  knowledge. It encourages contribution from experts and people with practical
  experience.

- Assuming 100% intelligence makes readers feel respected, and feel proud to be
  associated with the material.
  It will incline beginners to contribute their feedback.

- Ensures that each reader feels capable of tackling a problem, specific or general.

- Ensures that each reader can embody a new way of thinking about a topic.

- **Encourages communication between beginners and experts**, which can be highly
  instructive for both sides.

- Emphasize confusions, overlooked suggestions, pitfalls, and misunderstandings that are
  common.

* ☁️ SaaS / paid services

* 🚪 Alternatives to the option being discussed

* 💸 Cost or expense issues, discussion, and gotchas

* 🕍 A mild warning attached to “full solution” or opinionated frameworks (the cathedral
  is a nod to
  [Raymond’s metaphor](https://en.wikipedia.org/wiki/The_Cathedral_and_the_Bazaar))

* 🍺 Open source / free software

- For well-known people, places, things, and events, prefer linking to the **Wikipedia
  page**.

  - If there is a good quality Wikipedia page, prefer it to company or organization home
    pages, home pages of cities or states or agencies, and other things notable enough
    to be covered well.

  - Why? It usually gives a lot more context to the reader, and saves them having to
    Google to find it. It will also help with our search and web page snippet features,
    since the mouseovers on the links will be better quality than for those on marketing
    pages or poorly organized or out-of-date official websites.

    - Example: "The [Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
      [California](https://en.wikipedia.org/wiki/California) is home to both
      [Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
      [Google](https://en.wikipedia.org/wiki/Google)."

A lot has changed in the last decade.
We’re currently in a
[seller’s market](https://www.washingtonpost.com/news/where-we-live/wp/2018/01/10/what-home-sellers-can-expect-in-2018-the-market-is-still-in-your-favor-if-the-price-is-right/)
nationwide, meaning buyers are not favored in most markets.
Home prices last peaked in 2006, and are
[up 6.7 percent](http://money.cnn.com/2018/04/24/real_estate/home-prices-rise-case-shiller/index.html)
this year (they’ve risen [about](https://fred.stlouisfed.org/series/CSUSHPISA)
[6% every year](http://www.chicagotribune.com/business/ct-biz-tax-law-home-values-20180102-story.html)
for the last six) and rising—particularly in hot markets like San Francisco, where the
average home sells in 21 days.
Mortgage rates are rising, too, and fast.
From September 2017 to March 2018, [mortgage rates rose from 3.78% to
4.45%](https://www.nytimes.com/2018/03/28/upshot/housing-sales-mortgage-rates-tax-law.html).
Ouch. Neil Irwin, economist and New York Times correspondent,
[explains](https://www.nytimes.com/2018/03/28/upshot/housing-sales-mortgage-rates-tax-law.html)
that demand for housing is going up as millennials age into their 30s, but the cost of
building new homes to accommodate buyers is rising as well.
The
[tax law](https://turbotax.intuit.com/tax-tips/irs-tax-return/2017-tax-reform-legislation-what-you-should-know/L96aFuPhc)
passed in February 2017 is expected to [slow rising housing
costs](http://www.chicagotribune.com/business/ct-biz-tax-law-home-values-20180102-story.html)
for the upper middle class and the very wealthy.
The tax law’s impact on everyone else is mostly centered on the doubling of the standard
deduction for married couples (still 58% of
[first-time buyers](https://www.nytimes.com/2017/04/21/realestate/first-time-home-buyers-statistics.html))
to $24,000, which means the tax benefit of buying is
[no longer relevant](https://fred.stlouisfed.org/series/CSUSHPISA) for most people.

* When an investor is trying to get you to agree to a term you think is unfair, you need
  to protect your interests without sounding accusatory toward the investor: *“Sorry,
  I’m just inexperienced, I read/was told that it’s not wise to [term they want you to
  agree to].”* [[Paul Graham, Y Combinator](http://paulgraham.com/fr.html)]

* When you want to test a VC’s interest to determine where to put your energy, you don’t
  want to sound desperate or pushy: *“I know that you’re not likely to give me a strong
  indication at this meeting, but I’d love to know if this is the* sort *of opportunity
  you could imagine taking.
  I’ll happily put in the work to persuade you over time!
  But would I be better off focusing my attention on other VCs?”* [[Mark Suster, Upfront
  Ventures](https://bothsidesofthetable.com/how-to-develop-your-fundraising-strategy-58c2f0b22d6d)]

🔹 **Automated and emerging legal services**: Many services like
[**Stripe Atlas**](https://stripe.com/atlas), **[Atrium](https://www.atrium.co/)**,
[**Clerky**](https://www.clerky.com/), [*LegalZoom*](https://www.legalzoom.com/), and
*[UpCounsel](https://www.upcounsel.com/)* automate or simplify tasks and processes
provided by lawyers.
[**Atrium**](https://www.atrium.co/) is a new legal services company worth keeping an
eye on.

- [Alternative Minimum Tax
  (AMT)](http://fairmark.com/general-taxation/alternative-minimum-tax/alternative-minimum-tax-101/)
  is a [complex part](https://www.irs.gov/taxtopics/tc556.html) of the federal tax code
  many taxpayers never worry about.
  Generally, you do not pay [unless you have high income (>$250K) or high
  deductions](http://www.marketwatch.com/story/congratulations-you-owe-the-alternative-minimum-tax-2014-01-14).
  It also depends on the state you’re in, since your state taxes can significantly
  affect your deductions.
  Confusingly, if you are affected, AMT tax rates are usually at **26%** or **28%**
  marginal tax rate, but effectively is **35%** for some ranges, meaning it is [higher
  than ordinary income tax for some incomes and lower for
  others](http://www.forbes.com/sites/feeonlyplanner/2011/12/16/the-alternative-minimum-tax-sweet-spot/).
  AMT rules are so complicated you often need professional tax help if they might apply
  to you. The IRS’s
  [AMT Assistant](https://www.irs.gov/Businesses/Small-Businesses-&-Self-Employed/Alternative-Minimum-Tax-(AMT)-Assistant-for-Individuals)
  might also help.

- ❗ If you do get an offer, you need to understand the value of the equity component.
  You need quite a bit of information to figure this out, and should just ask.
  If the company trusts you enough to be giving you an offer, and still doesn’t want to
  answer these questions about your offer, it’s **a warning sign**. (There are many
  [resources](https://blog.wealthfront.com/stock-options-14-crucial-questions/) out
  there with more details about
  [questions](http://www.inc.com/atish-davda/5-questions-you-should-ask-before-taking-a-start-up-job-offer.html)
  like this.) Information that will help you weigh the offer might be: *What percentage
  of the company do the shares represent?* *What set of shares was used to compute that
  percentage (is this really the percentage of all shares, or some subset)?* *What did
  the last round value the company at?
  (I.e. the preferred share price times the total outstanding shares)?* *What is the
  most recent 409A valuation?
  When was it done, and will it be done again soon?* *Do you allow early exercise of my
  options?* *Are all employees on the same vesting schedule?* *Is there any acceleration
  of my vesting if the company is acquired?* *Do you have a policy regarding follow-on
  stock grants?* *Does the company have any repurchase right to vested shares?*

- Finally, consider the [common scenarios](#common-scenarios) for exercising options,
  discussed below.

- ❗ It may not be common, but some companies retain a right to repurchase (buy back)
  vested shares. It’s simple enough to ask, "Does the company have any repurchase right
  to *vested* shares?”
  (Note repurchasing *unvested* shares that were purchased via early exercise is
  different, and helps you.)
  If you don’t want to ask, the fair market value repurchase right should be included in
  the documents you are being asked to sign or acknowledge that you have read and
  understood. (Skype had a
  [complex](https://www.quora.com/Which-valley-startups-have-a-Skype-like-repurchase-right)
  [controversy](http://www.wac6.com/wac6/2011/07/skypes-employee-stock-option-plan-worthless-only-if-you-quit-before-2014.html)
  related to repurchasing.)
  You might find a repurchase right for vested shares in the Stock Plan itself, the
  Stock Option Agreement, the Exercise Agreement, the bylaws, the certificate of
  incorporation, or any other stockholder agreement.

Venture capital firms fund companies-commonly referred to as startups-that have
ambitious goals of being dominant high-value businesses in their target market ([market
caps](https://www.investopedia.com/terms/m/marketcapitalization.asp) of >$1B and margins
of >50%). These firms seek to make investments early in a company’s life when stock is
cheap, in hopes of holding through periods of hyper-growth in order to realize
abnormally large returns (200%+).

- Preferred stock usually has a
  [**liquidation preference**](http://www.investopedia.com/terms/l/liquidation-preference.asp),
  meaning the preferred stock owner will be paid before the common stock owners upon
  liquidation.

  - [**Liquidation overhang**](https://equityzen.com/blog/startup-valuations-and-liquidation-preference-overhang/)
    can occur when the value of a company just doesn’t reach the number of dollars
    investors put into it.
    Because of liquidation preference, those holding preferred stock (investors) will
    have to be paid before those holding common stock (employees).
    If investors invested a hundred million dollars in your company, your equity as an
    employee won’t be worth anything if the company is sold when it’s in liquidation
    overhang and the sale doesn’t
    [exceed that amount](https://avc.com/2010/10/employee-equity-the-liquidation-overhang/).

  - ☝️ Preferences are
    [notoriously](https://venturebeat.com/2010/08/16/beware-the-trappings-of-liquidation-preference/)
    [complex](https://medium.com/@CharlesYu/the-ultimate-guide-to-liquidation-preferences-478dda9f9332).
    Investors and entrepreneurs negotiate a lot of these details, including:

    - The **multiple**, a number designating how many times the investor must be paid
      back before common shareholders receive proceeds (often the multiple is 1X, but it
      can be 2X or higher).

    - Whether preferred stock is
      [**participating**](https://en.wikipedia.org/wiki/Participating_preferred_stock),
      meaning investors get their money back and also participate in proceeds from
      common stock.

    - Whether there is a **cap**, which limits the payout if it is participating.

- **Secondary buyers**: Thinking on all this
  [has evolved](http://www.industryventures.com/2014/12/02/employee-liquidity-good-for-private-companies/)
  [in recent years](https://techcrunch.com/2015/10/14/selling-private-company-shares-2-0/).
  Some companies do see value in offering (mostly limited) opportunities for sale.

  - [SharesPost](http://sharespost.com/), [Equidate](https://www.equidateinc.com/), and
    [EquityZen](https://equityzen.com/) have sought to establish a market around
    secondary sales, particularly for well-known pre-IPO companies.

- **NSOs**: You pay full taxes at exercise, and the sale is like any investment gain:

  - At grant and vesting:

    - No tax if granted at FMV

  - At exercise:

    - Ordinary tax on the bargain element

    - Income and employment tax withholding on paycheck

  - At sale:

    - Long-term capital gains tax on gain if held for *1 year past exercise*

    - Ordinary tax otherwise (including immediate sale)

- **ISOs**: You might pay less tax at exercise, but it’s complicated:

  - At grant and vesting:

    - No tax if granted at FMV

  - At exercise:

    - AMT tax event on the bargain element; no ordinary or capital gains tax

    - No income or employment tax withholding on paycheck

  - At sale:

    - Long-term capital gains if held for *1 year past exercise and 2 years past grant
      date*

    - Ordinary tax otherwise (including immediate sale)

ElastiCache Basics:

- 📒 [Homepage](https://aws.amazon.com/elasticache/) ∙
  [User guide](http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide) ∙
  [FAQ](https://aws.amazon.com/elasticache/faqs/) ∙
  [Pricing](https://aws.amazon.com/elasticache/pricing/)

- **ElastiCache** is a managed in-memory cache service, that can be used to store
  temporary data in a fast in-memory cache, typically in order to avoid repeating the
  same computation multiple times when it could be reused.

- It supports both the [Memcached](https://memcached.org) and [Redis](https://redis.io)
  open source in-memory cache software and exposes them both using their native access
  APIs.

- The main benefit is that AWS takes care of running, patching and optimizing the cache
  nodes for you, so you just need to launch a cluster and configure its endpoint in your
  application, while AWS will take of most of the operational work of running the cache
  nodes.

DynamoDB Basics:

- 📒 [Homepage](https://aws.amazon.com/dynamodb/) ∙
  [Developer guide](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/) ∙
  [FAQ](https://aws.amazon.com/dynamodb/faqs/) ∙
  [Pricing](https://aws.amazon.com/dynamodb/pricing/)

- **DynamoDB** is a [NoSQL](https://en.wikipedia.org/wiki/NoSQL) database with focuses
  on speed, flexibility, and scalability.
  DynamoDB is priced on a combination of throughput and storage.

ElastiCache Tips:

- Choose the
  [engine](http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/SelectEngine.html),
  clustering configuration and
  [instance type](http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/CacheNodes.SelectSize.html)
  carefully based on your application needs.
  The documentation explains in detail the pros, cons and limitations of each engine in
  order to help you choose the best fit for your application.
  In a nutshell, Redis is preferable for storing more complex data structures, while
  Memcached is just a plain key/value store.
  The simplicity of Memcached allows it to be slightly faster and allows it to scale out
  if needed, but Redis has more features which you may use in your application.

- For Memcached AWS provides enhanced SDKs for certain programming languages which
  implement
  [auto-discovery](http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/AutoDiscovery.html),
  a feature not available in the normal memcached client libraries.

**CEOs** and **COOs** who run a company or team of significant size should be sure to
talk to an equity compensation consultant or specialist at a law firm.
**Founders** looking for an introduction to legalities of running a company may wish to
check out Clerky’s [*Legal Concepts for Founders*](https://handbook.clerky.com/).

This number has steadily declined since 2002 levels of 12.3% and 23.2% respectively
([NCEO analysis](https://www.nceo.org/assets/pdf/articles/GSS-2014-data.pdf) of General
Social Survey data).

- **Visionary projects.** Projects that were in a completely brand-new space without a
  precedent, going from 0 to 1.

More line spacing challenges with multi-paragraph items:

- Use `z` (zoxide) instead of `cd`.

  ```shell
  # Use z in place of cd: switch directories (first time):
  z ~/some/long/path/to/foo
  # Thereafter it's faster:
  z foo
  ```

- Use `eza` instead of `ls`. It has color support, support for Nerd Font icons, and
  other improvements.

And enumerations:

4. **Format a doc:** You can convert a doc to nicely formatted HTML with

   ```shell
   tp format '~/Downloads/Airspeed Velocity of Unladen Birds.docx' --show
   ```

   Replace with the path above to a .docx or .md file.
   (The `--show` is optional)

   You can try other format docs.
   Currently DOCX, HTML, and Markdown foramt work.
   (PDF coming soon!)

5. **View locally:** You’ll see from the above output both an `.md` and an `.html` file.
   You can look at these locally and do what you want with them.

6. **Publish:** Publish the file with:

### 3.6 Comparative Features Matrix

This line has a two-space line break.\
And this is a regular line.

The following table summarizes the native capabilities of the primary platforms
evaluated against the core requirements:

| **Feature** | **Vercel** | **Netlify** | **Cloudflare Pages** | **AWS (S3/CloudFront)** |
| --- | --- | --- | --- | --- |
| **CLI Tool Availability** | Yes (vercel) 1 | Yes (netlify) 2 | Yes (wrangler) 3 | Yes (aws) 4 |
| **Primary CLI Auth Method** | User Access Token 9 | Personal Access Token (PAT) 2 | API Token 10 | IAM Credentials / STS Token 11 |
| **Native Token/Key Scoping** | User/Team Level 24 | User/Site Level 30 | Account Level (for Pages Edit) 3 | Path/Prefix Level (via IAM) 4 |
| **Path-Based Deploy Permissions** | No Native Support 14 | No Native Support 2 | No Native Support 3 | Yes (IAM Policies) 4 |
| **Primary Native Isolation Method** | Project | Site | Project (but weak permissions) | Path Prefix (with IAM) 4 |
| **Programmatic File Delete/Update** | Deployment API 14 | Deployment API 28 | Deployment API (via Wrangler) | Direct S3 Object API 12-55 |
| **Programmatic Invalidation API** | Automatic / Limited | Automatic / Limited | Yes (Cloudflare API) | Yes (CloudFront API) 15-16 |
| **Basic Cost Model** | Per User / Usage 5 | Per User / Usage 5 | Generous Free Tier / Usage | Usage-Based Components 20-64 |

## 3. Platform\-Specific Mechanisms

Each major operating system provides its own set of system calls, APIs, and conventions
for managing temporary files and directories.

### 3.1. Linux

Linux offers a rich set of POSIX\-compliant and Linux\-specific mechanisms.

* **APIs:**

  + mkstemp(3\): Generates a unique filename based on a template (prefixXXXXXX), creates
    the file with 0600 permissions, opens it, and returns a file descriptor.
    It uses O\_EXCL for atomic creation, preventing race conditions.<sup>19</sup> The
    caller is responsible for unlinking the file.

  + mkdtemp(3\): Similar to mkstemp but creates a unique directory with 0700 permissions
    based on a template (prefixXXXXXX), returning the path.<sup>19</sup> The caller must
    remove the directory.

  + tmpfile(3\): Creates an unnamed temporary file opened in wb\+ mode (binary
    read/write), automatically deleted when closed or on process
    termination.<sup>19</sup> While convenient, POSIX notes potential permission issues
    and recommends mkstemp followed by fdopen for multithreaded apps to avoid leaking
    file descriptors.<sup>59</sup>

* **Recommended Python Approach for Atomic Writes:**

  1. **Use a Library:** Employing a dedicated library like atomicwriter or atomicfile is
     generally the most robust approach, as they handle temporary file creation in the
     correct location, atomic renaming (os.replace), and error cleanup across platforms.

  2. **Manual Implementation (if necessary):**

     + Determine the destination directory: dest\_dir = os.path.dirname(dest\_path)

     + Create the temporary file in the destination directory: temp\_file =
       tempfile.NamedTemporaryFile(mode='w', dir=dest\_dir, delete=False) (use
       appropriate mode, e.g., wb for binary).

     + Use a try … finally block to ensure cleanup:\
       Python\
       temp\_file = None\
       try:\
       temp\_file = tempfile.NamedTemporaryFile(mode='w', dir=dest\_dir, delete=False,
       prefix='tmp', suffix='.tmp')\
       # Write data to temp\_file.file (or temp\_file directly in older Pythons)\
       temp\_file.write(...)\
       # Ensure data is on disk before renaming\
       temp\_file.flush()\
       os.fsync(temp\_file.fileno())\
       # Close the file handle before renaming\
       temp\_file.close()\
       # Atomic rename/replace\
       os.replace(temp\_file.name, dest\_path)\
       temp\_file = None # Prevent cleanup in finally block if successful\
       finally:\
       if temp\_file is not None and os.path.exists(temp\_file.name):\
       try:\
       os.unlink(temp\_file.name)\
       except OSError:\
       # Log error, but continue\
       pass\

### Boldface, italics, and links

X [New York City](https://en.wikipedia.org/wiki/New_York_City). XX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City). XXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[New York City](https://en.wikipedia.org/wiki/New_York_City).

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York
City**. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New
York City**. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York
City**. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New
York City**. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New York
City**. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**New York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New
York City**.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **New
York City**.

**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City** xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
**New York City**
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or em*phases*.
And more words. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face** or
em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face**
or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face**
or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or bold**face**
or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases or
bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases
or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases
or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or *em*phases
or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face or
*em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face
or *em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face
or *em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX **bold**face
or *em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**bold**face or *em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**bold**face or *em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**bold**face or *em*phases or bold**face** or em*phases*. And more words.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
**bold**face or *em*phases or bold**face** or em*phases*. And more words.

In some cases, **bold**face or *em*phases or bold**face** or em*phases* can occur
without intervening whitespace.
In fact, **bold**face or *em*phases or bold**face** or em*phases* or **bold**face or
*em*phases or bold**face** or em*phases* or **bold**face or *em*phases or bold**face**
or em*phases* or **bold**face or *em*phases or bold**face** or em*phases* or
**bold**face or *em*phases or bold**face** or em*phases* or **bold**face or *em*phases
or bold**face** or em*phases* or **bold**face or *em*phases or bold**face** or
em*phases* or **bold**face or *em*phases or bold**face** or em*phases* can flow on and
on …

*blah blah* *blah blah* *blah blah* *blah blah* *blah blah* *blah blah* *blah blah*
*blah blah* *blah blah* *blah blah* *blah blah* *blah blah* *blah blah* *blah blah*
*blah blah* *blah blah* *blah blah* *blah blah* *blah blah* *blah blah* *blah blah*
*blah blah*

The same is true for links.
"The [Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google)." "The
[Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google)." (The
[Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google).) The
[Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google).
*The [Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google).* **The
[Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google).** The
[Bay Area](https://en.wikipedia.org/wiki/San_Francisco_Bay_Area) in
[California](https://en.wikipedia.org/wiki/California) is home to both
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.) and
[Google](https://en.wikipedia.org/wiki/Google).

[Apple](https://en.wikipedia.org/wiki/Apple_Inc.)/[Google](https://en.wikipedia.org/wiki/Google),
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.)/[Google](https://en.wikipedia.org/wiki/Google),
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.)/[Google](https://en.wikipedia.org/wiki/Google),
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.)/[Google](https://en.wikipedia.org/wiki/Google),
[Apple](https://en.wikipedia.org/wiki/Apple_Inc.)/[Google](https://en.wikipedia.org/wiki/Google).

### More URLs

* 📈 adpushup ([2017,
  Seed](https://www.slideshare.net/AlexanderJarvis/adpushup-seed-pitch-deck))

* 📈 AirBnB ([2009, Seed](http://www.slideshare.net/ryangum/airbnb-pitch-deck-from-2008))

* 📈 AppNexus ([2007,
  Seed](http://www.slideshare.net/CamilleRicketts2/appnexus-first-pitch-deck))

* 📈 Bliss ([2017, Seed](https://www.slideshare.net/AlexanderJarvis/blissai-pitch-deck))

* 📈 Boomtrain ([2014, ?](https://boomtrain.docsend.com/view/3giicsi))

* 📈 Buffer ([2011, Seed](http://www.slideshare.net/Bufferapp/buffer-seedrounddeck))

* 📈 BuzzFeed ([2008, Series
  A](https://qz.com/389752/here-is-buzzfeeds-first-pitch-deck-to-investors-in-2008/))

* 📈 Castle ([2017,
  Seed](https://www.slideshare.net/AlexanderJarvis/castle-pitch-deck-75070238))

* 📈 Coinbase ([2012,
  Seed](https://www.slideshare.net/BrianArmstrong29/coinbase-seed-round-pitch-deck));
  [Commentary](https://medium.com/@barmstrong/the-coinbase-seed-round-pitch-deck-50c8ec91d40b)
  on the round by Brian Armstrong, CEO of Coinbase.

* 📈 Contently ([2014, Series
  B](https://www.slideshare.net/GoCanvas/the-10-most-interesting-slides-that-helped-our-saas-company-raise-9-million-42566344))

* 📈 Cubeit ([2017, Seed](https://www.slideshare.net/AlexanderJarvis/cubeit-pitch-deck))

* 📈 Crew ([2015, Series
  A](https://www.slideshare.net/AlexanderJarvis/crew-pitch-deck-seriesa))

* 📈 DocSend ([2013, Seed](https://docsend.com/view/n43v89r))

* 📈 Dwolla ([2013, Series
  C](http://www.businessinsider.com/18-slide-pitch-deck-lands-payment-startup-dwolla-165-million-2013-4?op=1))

* 📈 eShares ([2014, Series
  A](https://esharesinc.app.box.com/s/fjixdt78tl9henx2c75etkx1sootwo9p));
  [Commentary](https://medium.com/eshares-blog/eshares-series-a-c6bad9ad3721#.alf0y6i99)
  on the round by [Henry Ward](https://twitter.com/henrysward), CEO of eShares

* 📈 Foursquare ([2009, Seed](http://www.slideshare.net/alkarmi/foursquare-1stpitch2009))

* 📈 Front ([2016, Series
  A](http://www.slideshare.net/MathildeCollin/front-series-a-deck-64596550?ref=https://cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.slideshare.net%2Fslideshow%2Fembed_code%2Fkey%2FFXlrFkbldHJoki&url=http%3A%2F%2Fwww.slideshare.net%2FMathildeCollin%2Ffront-series-a-deck-64596550&image=http%3A%2F%2Fcdn.slidesharecdn.com%2Fss_thumbnails%2Fdecktopublish-1-160801215931-thumbnail-4.jpg%3Fcb%3D1470090544&key=d04bfffea46d4aeda930ec88cc64b87c&type=text%2Fhtml&schema=slideshare));
  [Commentary](https://medium.com/@collinmathilde/front-series-a-deck-f2e2775a419b#.7xlz4lwxz)
  on the round by [Mathilde Collin](https://twitter.com/collinmathilde), CEO of Front

* 📈 Gaia Design ([2015,
  ?](https://www.slideshare.net/valentinelanger/presentation-gaia-design-furniture))

* 📈 Intercom ([2011,
  Seed](http://www.slideshare.net/eoghanmccabe/intercoms-first-pitch-deck))

And some dashes:

- 🔥[The Culture Cliché](https://m.signalvnoise.com/the-culture-cliche/) – Claire Lew

- 🔥[Most Company Culture Posts are Fluffy Bullshit — Here is what you actually need to
  know](https://medium.com/evergreen-business-weekly/most-company-culture-posts-are-fluffy-bullshit-here-is-what-you-actually-need-to-know-1cf8597a5c2c)
  — Eric Jorgenson – summarizing the many dimensions of culture

- 💳[The Culture Factor](https://hbr.org/2018/01/the-culture-factor) – Boris Groysberg,
  Jeremiah Lee, Jesse Price, J. Yo-Jud Cheng

- [Programming Your Culture](https://a16z.com/2012/12/18/programming-your-culture/) —
  Ben Horowitz (note this line has nonbreaking spaces)

## Footnotes and bare links

🔸 If you do send a pitch deck via email, expect materials you share with investors to
get leaked to other investors, your competitors, and the press.[^191] That doesn’t mean
you shouldn’t tell investors what they need to know, but it does mean you want to be
careful with how you share that information.
You might, for example, send investors a less sensitive version of your pitch deck via
email, but include additional slides when you actually present to them at their firm.

To create an effective story, you have to consider what motivates the recipient of your
story. Take Henry Ford, “If there is any one secret of success it lies in the ability to
get the other person’s point of view and see things from their angle as well as your
own.” [^177]

Spacing around footnotes can be confusing.[^a] Like this.[^a][^b] Or.
[^a] [^b] This. [^a][^b][^c]

And people often put them before punctuation like this[^a], or this[^a]. Or even
this[^a][^b]? Perhaps by **15% to 25%**[^freeincome.2b5cob], pretty quickly (but we’re
not complaining)[^urbanthowt.wy49lp].

❗️️️ Having multiple automatic conversion thresholds can give the investor with a higher
threshold leverage to block an IPO.[^210]

1. **Initial Scan with -X importtime:** Run the application with python -X importtime...
   \> import.log. Visualize the output using tuna import.log.<sup>42</sup> Look for
   modules with large *cumulative* times at the top level or deep in the call stack.
   These are the primary candidates for further investigation.<sup>1</sup>

[^2]: Aulet, Bill. *Disciplined Entrepreneurship*: 24 Steps to a Successful Startup (Kindle
    Location 1220). Wiley, 2013. Kindle Edition.

[^191]: http://paulgraham.com/fr.html

[^177]: Carnegie, Dale. *How To Win Friends and Influence People* (p. 35). Simon & Schuster.
    Kindle Edition.

[^207]: [https://bostonvcblog.typepad.com/vc/2009/07/in-vc-deals-price-doesnt-matter-but-the-promote-does.html](https://bostonvcblog.typepad.com/vc/2009/07/in-vc-deals-price-doesnt-matter-but-the-promote-does.html)

[^210]: FM16, p. 80

Links like these underline ones come up from some exports.
And let’s try some links with angle brackets.

[^52]: [[https://www.vox.com/2014/3/5/11624228/how-a-startup-created-the-no-1-rated-mattress-on-amazon-com]{.underline}](https://www.vox.com/2014/3/5/11624228/how-a-startup-created-the-no-1-rated-mattress-on-amazon-com)

[^53]: <https://www.fastcompany.com/90216464/the-29-billion-battle-to-own-how-america-sleeps>

[^axioscomth.1lioru]: <https://www.axios.com/the-rise-of-pre-seed-venture-capital-1513305959-13da61c8-15f8-441e-b016-d29902bff8bf.html>

[^carnegieda.327r3k]: Carnegie, Dale. *How To Win Friends and Influence People* (p. 35). Simon & Schuster.
    Kindle Edition.

[^53]: <https://www.fastcompany.com/90216464/the-29-billion-battle-to-own-how-america-sleeps>

[^217]: Testing - : Is Ketamine Contraindicated in Patients with Psychiatric Disorders?
    - REBEL EM - more words - accessed April 24, 2025,
    <https://rebelem.com/is-ketamine-contraindicated-in-patients-with-psychiatric-disorders/>

[^multiline]: The distinction between “hiring” and “recruiting” isn’t universally agreed
    upon. Some people think of hiring as a superset of recruiting, some consider it to be
    the other way around.
    However you think of it, both recruiting and hiring involve selling candidates on
    the value proposition of a company and ensuring the alignment of interests between
    the two parties.

[^multiparagraph]: This is an even longer footnote …

    Paragraph 1.

    > And even a block quote.

    Paragraph 3.

And by contrast here a bare link is like this https://www.google.com/

## Some other stuff

```javascript
// This is a code block
var x = 5;
```

```
This is
another.
```

<div align="center"> <img src="images/rounds.png" alt="awesome"> <br> Example of company
valuation, shares, fundraising, and dilution (<a
href="http://ownyourventure.com/equitySim.html">source</a>) <br> </div>

| Specific AWS Services | Basics | Tips | Gotchas |
| --- | --- | --- | --- |
| [Security and IAM](#security-and-iam) | [📗](#security-and-iam-basics) | [📘](#security-and-iam-tips) | [📙](#security-and-iam-gotchas-and-limitations) |
| [S3](#s3) | [📗](#s3-basics) | [📘](#s3-tips) | [📙](#s3-gotchas-and-limitations) |
| [EC2](#ec2) | [📗](#ec2-basics) | [📘](#ec2-tips) | [📙](#ec2-gotchas-and-limitations) |
| [CloudWatch](#cloudwatch) | [📗](#cloudwatch-basics) | [📘](#cloudwatch-tips) | [📙](#cloudwatch-gotchas-and-limitations) |
| [AMIs](#amis) | [📗](#ami-basics) | [📘](#ami-tips) | [📙](#ami-gotchas-and-limitations) |
| [Auto Scaling](#auto-scaling) | [📗](#auto-scaling-basics) | [📘](#auto-scaling-tips) | [📙](#auto-scaling-gotchas-and-limitations) |

- 📒 [FAQ](https://aws.amazon.com/cloudwatch/faqs/) ∙
  [Pricing](https://aws.amazon.com/cloudwatch/pricing/) - 🔹Blahxxx - ❗Blahxxx

**Related Architecture**:

- [arch-execution.md](../architecture/arch-execution.md) - Execution model context

## Corner Cases

# Markdown Corner Cases Test Suite

This document tests all discovered edge cases and formatting quirks.

* * *

## 1. Thematic Break Normalization

Thematic breaks should be preserved as `* * *` not normalized to dashes.

Test: Three asterisks with spaces should stay as `* * *` not become `-----`.

* * *

## 2. Numbered Heading Escaping

Numbered headings like “## 1. Introduction” should not have the period escaped.

### 1. First Section

Content here.

### 2. Second Section

More content.

## 3. Underscore Escaping

Technical terms with underscores should not be escaped in normal text:

- x86_64 architecture

- ARM64 (aarch64) platforms

- Linux x86_64 (glibc and musl/static)

- macOS Intel (x86_64)

- Windows x86_64

## 4. Less-Than Escaping

Comparison operators should not be escaped:

- Startup time: < 10ms

- Binary size < 10MB

- Processing speed < 50ms

## 5. Hash Escaping

Hash symbols in inline strings should not be escaped:

> The string `##` should not become `\#\#` in quotes.

## 6. Code Fence with Indented Lists

YAML code blocks with indented lists should be preserved correctly:

```yaml
jobs:
  fmt:
    name: Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt

      - name: Check formatting
        run: cargo fmt --all -- --check
```

## 7. Quote Block Formatting

Quote blocks should have correct blank line spacing:

> **Completion Gate:** Acceptance requires exact 100% passing of every test, exact 100%
> parity with every original Python test, and exact byte-for-byte matching on all
> comparisons (zero diffs).
> This includes:
> 
> - Test output and processing results
>
> - CLI command output (help, errors, warnings, status messages)
>
> - Cross-validation across all fixtures
>
> - File outputs (no whitespace or encoding differences unless documented)

## 8. Badge Link Wrapping

Badge links should each be on separate lines:

[![CI](https://github.com/jlevy/flowmark-rs/workflows/CI/badge.svg)](https://github.com/jlevy/flowmark-rs/actions)
[![Release](https://github.com/jlevy/flowmark-rs/workflows/Release/badge.svg)](https://github.com/jlevy/flowmark-rs/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 9. Paragraph Wrapping

Regular paragraphs should join lines and wrap at the configured width:

First line of text. Second line of text.
Third line of text that continues here.

## 10. Quote Block Line Joining

Quote blocks should join lines within paragraphs:

> First line in quote.
> Second line in quote.
> Third line in quote.

## 11. Link Wrapping

Regular links should be joined on the same line if they fit:

[Link one](https://example.com/first) [Link two](https://example.com/second)

## 12. Inline Image Wrapping

Inline images should be joined on the same line if they fit:

![Image one](image1.png) ![Image two](image2.png)

## 13. Heading Spacing

Headings should have consistent blank line spacing.

### Subheading Test

Paragraph after heading.

### Another Subheading

> Quote after heading.

### A Third Subheading

```markdown
A fenced block.
```

### List After Heading

- List item one

- List item two

## 14. Nested Fenced Code Blocks

Fenced code blocks that contain other fenced code blocks need extra backticks.

### Markdoc Style (4 backticks)

````value {% process=false %}
Use {% callout %} for emphasis.
````

### Nested Markdown Code (4 backticks)

````markdown
This is a code block with nested markdown:

```python
print('hello')
```
````

### Deeply Nested (5 backticks)

`````markdown
Here's an example with 4-backtick code block:

````python
print('hello')
````
`````

### Tilde Fences Preserved

~~~markdown
Here's some code:

```python
print('hello')
```
~~~

## Summary

All these corner cases should format consistently and predictably.

# Fruits of Love and Truth: character profiles (V0 DRAFT, for David to correct)

The Fruits (love) and the Truth Engine (truth) are read together as one layer, because "speaking the truth in love"
(Eph 4:15) needs both, and "full of grace and truth" (John 1:14) is the benchmark. The machine rules are in
`character_profiles.json`; this page says what they mean. Every match is a proposal, never a verdict on a person.

## Scored automatically from the sentences (David, 2026-09-27)

Every sentence gets 9 values from -2 to +2 (the per-sentence pass). For each fruit the profile uses its **net points per
100 sentences**: the sum of that fruit's sentence values x 100 / number of sentences. About 10 is a strong lean.
The paper-level verdict (0-4) is shown only as a second opinion.

## Axis 1: LOVE (0-1)

0.5 + 0.5 x tanh(mean of the nine net values / 10). Love is the root; the other eight are its dimensions, so all nine count.

## Axis 2: TRUTH (0-1)

The mean of the parts that are available:
- Truth Engine lexicon score, squashed to 0-1: (fruit×1 + grounding×2) − (anti_fruit×1.5 + contradiction×0.5 + jargon×0.3 + propaganda×2), per 100 words
- coherence overall / 10 (coherence station)
- the Fruits truth/evidence gate: PASS 1 · WARN 0.66 · UNKNOWN 0.5 · FAIL 0

## The four quadrants (cut at 0.5 on each axis)

| | Truth high | Truth low |
|---|---|---|
| **Love high** | **Grace and Truth**: tells the truth for the reader's good | **Sentimentalist**: warmth that won't correct; love without truth |
| **Love low** | **Clanging Cymbal** (1 Cor 13:1): accurate but cold; truth without love | **Propagandist / Fear Merchant**: neither |

A paper whose fruit scores are almost all 2 with low confidence lands near the middle: that is **No Signal**, not a quadrant.

## Profile shapes: what it means when certain fruits come out high or low

A shape is read from each fruit's distance above or below the paper's own average. That way a quiet paper and a warm
paper can have the same shape. A shape matches when its "high" fruits sit clearly above its "low" fruits (a gap of 3 or more
net points per 100 sentences) and at least 3 sentences engage its high fruits. The best two matches are reported with their gap.

| Profile | High | Low | Baseline picture | Counterfeit to watch |
|---|---|---|---|---|
| **Shepherd** | patience, gentleness, kindness | (none low) | Walks the reader step by step, fair to opponents, lowers barriers | Softness that never lands the point |
| **Prophet** | faithfulness, goodness, self_control | peace, gentleness | Holds the line on truth and evidence, and disturbs the peace to do it | Harshness called courage |
| **Pharisee** | self_control, faithfulness | love, kindness, gentleness | Rigor and rule-keeping without care for the person | Correctness as a weapon |
| **Stoic** | self_control, patience | joy, love | Disciplined and measured, emotionally flat | Detachment called maturity |
| **Zealot** | faithfulness, joy | patience, gentleness, self_control | All in, loud, and in a hurry | Overclaiming for the cause |
| **Peacemaker** | peace, gentleness, patience | (none low) | Names the conflict and moves toward reconciling it | False peace: avoiding the issue (check goodness/faithfulness) |
| **Peacekeeper (false peace)** | peace, gentleness | goodness, faithfulness | Keeps things calm by not saying the hard thing | Silence called peace |
| **Enthusiast** | joy, love | patience, self_control | Delight and hope that runs ahead of the argument | Euphoria that skips steps |
| **Servant** | kindness, goodness | (none low) | Practical help and benefit to the reader | Niceness that refuses correction |
| **Witness** | faithfulness, love | (none low) | Keeps faith with the evidence and with the reader | (rare) |

**Absent is not negative (2026-09-27).** Pharisee, Zealot and Enthusiast describe a vice, so they only match when their
"low" fruits actually score below zero. A paper that simply never engages love is not a cold paper. For Stoic, Prophet and
Peacekeeper, absence is enough (`low_means` in the JSON).

## Level profiles (absolute, checked first)

| Profile | Rule | Meaning |
|---|---|---|
| **Mature Fruit** | every fruit ≥ +10 net per 100 sentences | All nine present and balanced: the Galatians 5 picture |
| **Anti-Fruit** | 5 or more fruits ≤ −5 | Anti-fruit mechanisms dominate |
| **No Signal** | fewer than 5% of sentences engage any fruit | Too little behaviour in the text to read character (typical of pure exposition) |

## Truth Engine characterizations (kept from the workbook, lexicon-based)

These are the workbook's 10 patterns (Grounded Truth-Teller, Sophisticated Propagandist, Fear Merchant, Pure Fruit ...),
evaluated on lexicon densities. They are reported beside the profiles as a second read, because they measure words
while the profiles measure mechanism. Where they disagree, that disagreement is the counterfeit signal.

## Open questions for David

1. Are these the right ten shapes, and the right names? Add, rename or delete freely: the JSON is the only source.
2. Should the Prophet be allowed low peace, or is low peace always a flag?
3. Should the Love axis weight love itself more heavily than the other eight?
4. Should the profiles also run on the per-sentence curve (a profile per paragraph), not only the paper verdict?

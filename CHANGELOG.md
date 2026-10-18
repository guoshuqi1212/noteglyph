# Changelog

## 1.4.0

- **Card count follows the content.** No fixed number of cards. The agent maps every chapter into `outline_entries`, ranks each claim as core / important / minor, cards every core claim, and aims for about 80% of core + important claims as cards. Long books may ship in batches, but the first batch covers the whole book's main line. 张数按内容决定：核心观点全部制卡，整套覆盖约八成要点。
- **Coverage check** before drawing and at delivery: every chapter with real content has a card, and the delivery note lists important claims left uncarded.
- README example prompts no longer ask for a fixed eight cards.

## 1.3.0

- **English decks.** `book.lang: "en"` switches UI text, topic-label rules (one or two words) and quotation labels. Validation messages follow the deck language.
- **`book.kind`**: `book`, `paper` or `article`, used in page titles.
- **Quotation fields.** `quote.kind` now uses `quote`, `quote_translation`, `paraphrase`, `editorial`; `quote.text` and `quote.original` replace `zh` and `en`. v1.2 files still validate unchanged.
- **Single-card PNG export.** A “Save PNG / 存图” button on every card exports a 2x image in the current theme, offline and without dependencies.
- **Fixed unique-ability shape.** Diagrams reference it with `<use href="#ng-unique">` so its outline can no longer drift.
- **Legend** shows only the symbols a deck actually uses, and now includes the tinted “foundation” box.
- **Visual grammar** split into a core layer (any material) and an optional value layer (only when the source makes a value judgment).
- **Examples:** *The Analects* (zh) and *Meditations*, tr. George Long (en), with every quotation checked against the source; the original demo became `examples/starter.json`.
- **GitHub Pages** site in `docs/`; CI now checks that the demo pages are up to date.

## 1.2.0

- First packaged release: SKILL.md, references, HTML template, stdlib renderer with SVG allow-list, tests and CI.

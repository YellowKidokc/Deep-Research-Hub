# 49_ARGUMENT_GRADE

Every argument in a source gets **Strength** and **Originality**, each 0-8. The scores are computed from checklist
answers; the model never gives a number, and a check with no quote from the source scores 0.

- Strength: 8 checks (conclusion, premises, support, inference, objection, scope, falsifiable, convergence), each
  0/1/2, summed and halved.
- Originality: the model first names the closest prior art, then answers 4 checks (not restated, new support, new
  bridge, new structure), each 0/1/2.
- Two independent gradings (temperature 0.7) of the same argument list. The score is their mean; checks where they
  differ are shown.
- Machine ceiling 8. David's human review adds +1 and a Lean receipt adds +1, for a maximum of 10. Enter these in
  the ledger's `human_review (0/1)` and `lean_receipt` columns. They are kept when the ledger is rebuilt.
- Every argument is tagged to David's case map (`prompts/CASE_MAP.md`: K01-K18, F1-F4). The **Develop next** sheet
  lists the arguments the case needs whose strength is below 5.

    ONE_MENU.bat 49 --item paper.md            (or drop files into INBOX\49_ARGUMENT_GRADE)
    ONE_MENU.bat D  --item paper.md            (routine D: API Deep chain, then argument grades)

Outputs: `RUNS\49_ARGUMENT_GRADE\<source>\<stamp>\ARGUMENTS.html` + `arguments.json`, and across every source
`RUNS\49_ARGUMENT_GRADE\ARGUMENT_LEDGER.xlsx` (sheets: Arguments, Develop next, Case coverage) + `LEDGER.html`.

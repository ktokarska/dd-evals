# dd-evals report

**overall: fail**

## Gates

| Gate | Verdict |
|------|---------|
| G1 | pass |
| G2 | fail |
| G3 | pass |
| G4 | pass |
| G5 | pass |

## Fields

| id | metric | gate | score | threshold | success | reason |
|----|--------|------|-------|-----------|---------|--------|
| q01 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q02 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q03 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q04 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q05 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q06 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q07 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q08 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q09 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q10 | deterministic | G1 | 1.00 | 1.00 | True | match |
| q11 | deterministic | G1 | 1.00 | 1.00 | True | within tolerance |
| q12 | Faithfulness | G2 | 1.00 | 0.98 | True | All claims supported by the cited registry extract: two directors named, Helen Marsh (Managing Director) and Tomas Reuben (Finance Director), with roles matching the source. |
| q13 | Faithfulness | G2 | 0.50 | 0.98 | False | Two of four atomic claims are unsupported by the cited press release: the award year 2019 and the overall verified score of 95.2 points do not appear in the source. The certification body and the ESG evaluation are supported. Unsupported numeric and date claims fail the faithfulness bar. |
| q14 | Faithfulness | G2 | 1.00 | 0.98 | True | All claims supported: two designated members, Ciara Flannagan (Managing Partner) and Ondrej Blaha (Operations Partner), match the cited registry extract. |
| q15 | Faithfulness | G2 | 1.00 | 0.98 | True | All claims supported by the cited adverse media screen: the FMOA investigation, the February 2026 timing, the disclosure-practice subject, and the no-charges-filed, investigation-ongoing status. |
| q16 | Faithfulness | G2 | 1.00 | 0.98 | True | All claims supported: two board members, Franz Hofer (Chairman) and Priya Venkataraman (Executive Director), match the cited registry extract. |
| q17 | Faithfulness | G2 | 1.00 | 0.98 | True | All claims supported by the cited sanctions check: the match on Dorian Salgrave, the 55% controlling interest, the ORE listing, the company not being a named entry, and the indirect-exposure flag. |
| q18 | Faithfulness | G2 | 1.00 | 0.98 | True | All claims supported by the cited press release: B Corp status applies to the full legal entity Northwind Restoration Ltd, with the correct registration number, following the ESG evaluation. |
| q19 | deterministic | G3 | 1.00 | 1.00 | True | rendered the not-found sentinel |
| q20 | deterministic | G3 | 1.00 | 1.00 | True | rendered the not-found sentinel |
| q21 | deterministic | G4 | 1.00 | 1.00 | True | binary match |
| q22 | deterministic | G4 | 1.00 | 1.00 | True | binary match |
| q23 | deterministic | G4 | 1.00 | 1.00 | True | binary match |
| q24 | Answer Relevancy | G5 | 1.00 | 0.90 | True | Every statement addresses the beneficial-ownership compliance risk asked about and is drawn from the two cited documents; the answer is fully on-topic with no irrelevant content. |
| q25 | Answer Relevancy | G5 | 1.00 | 0.90 | True | The answer addresses both parts of the question, the adverse-media finding and whether charges were filed, with no off-topic statements; fully relevant. |

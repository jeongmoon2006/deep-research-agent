---
name: paper-analysis
description: 'Analyze a scientific paper: extract metadata, hypothesis, methods, results, and limitations. Evaluate whether claims are causal or correlational. Use when reading, reviewing, or critiquing an academic paper, or when extracting structured data from a PDF.'
argument-hint: 'Path to a paper PDF or URL to analyze'
---

# Scientific Paper Analysis

## When to Use

- Reviewing a scientific paper for a literature survey
- Extracting structured metadata (title, authors, journal, year, abstract)
- Evaluating the strength of evidence behind specific claims
- Checking whether a study supports causal or merely correlational conclusions
- Building a citation graph from a paper's references

## Procedure

### Step 1: Parse the PDF

Run [parse_pdf.py](./scripts/parse_pdf.py) to extract full text from the paper. If the input is a URL, fetch the PDF first, then parse.

### Step 2: Extract Metadata

From the parsed text, identify:
- **Title**
- **Authors** (all listed)
- **Journal / venue**
- **Publication year**
- **Abstract**

### Step 3: Extract Core Scientific Content

Identify and extract:
- **Hypothesis**: What the authors set out to test or explore
- **Dataset description**: Source, size, population, collection method, time period
- **Statistical methods**: Models used, software, significance thresholds

### Step 4: Extract Key Results

For each major finding:
- State the result
- Include the **p-value**, **confidence interval**, or **effect size** if reported
- Note the **sample size** — flag if underpowered or if significance is marginal relative to sample size

### Step 5: Evaluate Causal vs. Correlational Claims

For each claim in the paper:
- **Causal**: Supported by RCT, intervention, instrumental variable, difference-in-differences, or established mechanism
- **Correlational**: Observational association, cross-sectional, survey-based without causal identification
- **Overclaimed**: Language implies causation but study design only supports correlation — flag this explicitly

Check:
- What **controls** were used (covariates, fixed effects, matching)
- Whether **confounders** were identified and addressed
- Whether the authors acknowledge remaining endogeneity

### Step 6: Read the Limitations Section

Extract the authors' stated limitations verbatim. Then assess:
- Are there unstated limitations visible from the methods?
- Do the conclusions overreach relative to the stated limitations?

### Step 7: Extract Citations

Run [extract_citations.py](./scripts/extract_citations.py) to pull the reference list. Identify the most-cited references and any self-citations.

## Patterns (Good Practices)

- Always check sample size before trusting statistical significance
- Cross-reference claims in the results section against the methodology section
- Flag papers that claim causation from observational data
- Prefer systematic reviews and meta-analyses over single studies when assessing field consensus
- Look for pre-registration or registered report status as a quality signal
- Check data and code availability statements

## Anti-patterns (Bad Practices)

- Never accept abstract conclusions without reading the methods section
- Never treat correlation language ("associated with", "linked to") as evidence of causation
- Never skip the limitations section
- Never trust a single paper's conclusion without checking its citations and replication status
- Never ignore conflicts of interest or funding source disclosures

## Output Format

Return a structured summary:

```markdown
## Paper Analysis

**Title**: ...
**Authors**: ...
**Journal**: ...
**Year**: ...

### Abstract
[verbatim abstract]

### Hypothesis
[extracted hypothesis]

### Dataset
- Source: ...
- Sample size: ...
- Population: ...
- Collection method: ...

### Methods
- Statistical model(s): ...
- Software: ...
- Significance threshold: ...

### Key Results
| Finding | Statistic | Sample | Causal/Correlational |
|---------|-----------|--------|----------------------|
| ...     | p=...     | n=...  | ...                  |

### Controls & Confounders
- Controls used: ...
- Confounders addressed: ...
- Confounders unaddressed: ...

### Limitations
- Stated: ...
- Unstated: ...

### Flags
- [ ] Causation claimed from observational data
- [ ] Small sample size relative to effect
- [ ] Limitations section missing or inadequate
- [ ] No data/code availability
```

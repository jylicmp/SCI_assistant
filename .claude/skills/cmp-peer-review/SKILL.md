---
name: cmp-peer-review
description: "Systematic peer review toolkit for Condensed Matter Physics. Evaluate experimental setups, theoretical models (DFT/tight-binding), sample characterization, data analysis, and reporting standards for physics manuscripts."
allowed-tools: [Read, Write, Edit, Bash]
---

# Condensed Matter Physics Critical Evaluation and Peer Review

## Overview

Peer review is a systematic process for evaluating scientific manuscripts. Apply this skill for manuscript and grant review in Condensed Matter Physics (CMP), encompassing experimental solid-state physics, materials science, quantum materials, and theoretical/computational physics.

## When to Use This Skill

This skill should be used when:
- Conducting peer review of CMP manuscripts for journals (e.g., Physical Review Letters, Nature Physics, PRB, Applied Physics Letters).
- Evaluating theoretical formulations, Hamiltonians, and computational approaches (e.g., DFT, many-body methods).
- Assessing experimental rigor (e.g., sample synthesis, transport, spectroscopy, scattering techniques).
- Checking compliance with physics reporting guidelines (e.g., structural CIF files, data availability, error analysis).

## Peer Review Workflow

Conduct peer review systematically through the following stages:

### Stage 1: Initial Assessment
**Key Questions:**
- What is the central physics question (e.g., new phase of matter, novel transport phenomenon, improved theoretical model)?
- Are the claims physically sound and consistent with thermodynamic/quantum mechanical laws?
- Is the work appropriate for the intended venue's impact level?

### Stage 2: Detailed Section-by-Section Review

#### Abstract and Introduction
- **Context:** Does it clearly state the physical problem (e.g., symmetry breaking, correlation effects, topological properties)?
- **Literature:** Are foundational papers and competing theories/experiments appropriately cited?

#### Theoretical/Computational Methods
- **Approximations:** Are physical approximations (e.g., Born-Oppenheimer, mean-field, tight-binding limits) justified?
- **Parameters:** Are all computational parameters (k-point mesh, energy cutoffs, pseudopotentials, Hubbard $U$) detailed?
- **Equations:** Are Hamiltonians and derivations mathematically sound and clearly defined?

#### Experimental Methods
- **Sample Quality:** Is sample synthesis and characterization (XRD, EDX, RRR) adequately reported?
- **Setup:** Are measurement setups detailed (e.g., 2-probe vs. 4-probe, contact methods, cooling rates, magnetic field orientation)?
- **Calibration:** Are background signals, instrumental limits, and calibrations accounted for?

#### Results and Discussion
- **Data Integrity:** Are raw data vs. smoothed data clearly distinguished?
- **Error Analysis:** Are statistical (random) and systematic errors strictly separated and propagated?
- **Interpretation:** Are experimental observations uniquely tied to the proposed mechanism, or are there alternative physical explanations (e.g., heating effects, impurities)?
- **Theory-Experiment Match:** Is the comparison between theory and experiment quantitative, or merely qualitative?

### Stage 3: Rigor and Reproducibility Assessment
- **Data Availability:** Are raw datasets, custom codes, or structural files (CIF) deposited in repositories (Zenodo, arXiv, ICSD)?
- **Code:** Are scripts for custom data analysis or theoretical modeling accessible?

## Structuring Peer Review Reports

Organize feedback in a hierarchical structure:

### Summary Statement (1-2 paragraphs)
- Brief synopsis of the physical findings.
- Overall recommendation (Accept, Minor, Major, Reject).
- Key strengths and weaknesses.

### Major Comments
Critical issues impacting validity (number sequentially). Examples:
- "The claim of superconductivity lacks a measurement of the Meissner effect (diamagnetic susceptibility)."
- "The DFT calculations use standard GGA for a strongly correlated cuprate without justifying the neglect of on-site Coulomb repulsion (Hubbard U)."
- "The thermal transport data does not account for radiation losses at high temperatures."

### Minor Comments
Issues improving clarity (number sequentially). Examples:
- "Equation 3 is missing a summation index."
- "The axes in Figure 2b need physical units."
- "Provide the RRR (Residual Resistivity Ratio) to quantify sample purity."

## Resources
- `references/reporting_standards.md`: Physics-specific reporting guidelines.
- `references/common_issues.md`: Common methodological flaws in CMP.
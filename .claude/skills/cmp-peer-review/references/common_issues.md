# Common Methodological and Interpretational Issues in Condensed Matter Physics

This document catalogs frequent issues encountered during the peer review of Condensed Matter Physics (CMP) manuscripts. 

## Experimental Design and Execution Issues

### 1. Inadequate Sample Characterization
**Common Problems:**
- Claiming intrinsic physical properties without proving sample purity or single-crystal quality.
- Failing to quantify defects, doping levels, or off-stoichiometry.
- Ignoring phase separation or polycrystalline grain boundary effects.

**What to Recommend:**
- Require basic characterization data (e.g., powder/single-crystal XRD, EDX, XPS, or Laue diffraction).
- For transport, require the Residual Resistivity Ratio (RRR) as a proxy for sample quality.

### 2. Transport Measurement Artifacts
**Common Problems:**
- Using 2-probe measurements to claim zero resistance (ignoring contact resistance).
- Ignoring Joule heating effects at low temperatures or high currents.
- Misaligning magnetic fields in Hall effect or anisotropic magnetoresistance (AMR) measurements.
- Failing to separate symmetric (longitudinal) and antisymmetric (Hall) components of resistivity.

**What to Recommend:**
- Explicitly demand 4-probe or van der Pauw geometries for resistivity.
- Ask for current-dependence (I-V curves) to rule out Joule heating.
- Require proper tensor (symmetrization/antisymmetrization) analysis for magnetotransport.

### 3. Overclaiming Exotic Phases (Superconductivity/Topology/Magnetism)
**Common Problems:**
- Claiming superconductivity solely based on a resistivity drop (without proving zero resistance and the Meissner effect).
- Claiming a topological state (e.g., Dirac/Weyl semimetal) based solely on non-saturating magnetoresistance or a generic band structure.
- Claiming Quantum Spin Liquid (QSL) behavior without ruling out structural disorder or glassiness.

**What to Recommend:**
- Require thermodynamic evidence (specific heat, magnetization) to support transport claims.
- For topological claims, demand spectroscopic evidence (ARPES, STM) or distinct quantum oscillations (Shubnikov-de Haas) with proper Berry phase extraction.

## Theoretical and Computational Issues

### 4. Under-converged or Inappropriate DFT Calculations
**Common Problems:**
- Failing to perform convergence tests for k-point grids and plane-wave energy cutoffs.
- Using standard LDA/GGA functionals for strongly correlated electron systems (e.g., transition metal oxides, f-electron systems).
- "Tuning" the Hubbard $U$ parameter arbitrarily to match experiment without physical justification.
- Ignoring spin-orbit coupling (SOC) in heavy element compounds.

**What to Recommend:**
- Require explicit reporting of all convergence parameters.
- Suggest DFT+U, hybrid functionals (HSE), or dynamical mean-field theory (DMFT) for correlated systems.
- Require linear-response calculation of $U$ or references to established literature.

### 5. Finite-Size and Boundary Effects in Simulations
**Common Problems:**
- Using supercells that are too small, leading to unphysical interactions between defects or artificial momentum quantization.
- Imposing incorrect periodic boundary conditions for surface or 2D material simulations (insufficient vacuum gap).

**What to Recommend:**
- Request finite-size scaling analysis.
- Require validation that the vacuum region in slab models prevents spurious interactions.

## Data Analysis and Presentation Issues

### 6. Flawed Error Analysis
**Common Problems:**
- Confusing statistical errors (noise) with systematic errors (calibration, misalignment, geometry uncertainties).
- Fitting complex models (e.g., multi-band Drude models) with too many free parameters, resulting in over-fitting.
- Extracting parameters (like effective mass from Lifshitz-Kosevich formulas) without showing the error bounds of the fit.

**What to Recommend:**
- Require explicit separation of statistical and systematic uncertainties.
- Request confidence intervals for all extracted physical parameters.
- Ask for residuals of the fits to verify model suitability.

### 7. Inappropriate Data Manipulation
**Common Problems:**
- Aggressive data smoothing (e.g., adjacent averaging, FFT filtering) without showing the raw data or stating the algorithm.
- Subtracting arbitrary "backgrounds" (especially in spectroscopy like ARPES, Raman, or STM) to artificially enhance peaks.

**What to Recommend:**
- Require raw data to be shown, either in the main text or supplementary materials.
- Demand exact mathematical definitions of any background subtraction applied.

### 8. Visualization Issues
**Common Problems:**
- Using non-linear or rainbow color maps (e.g., "jet") for 2D data (STM maps, ARPES spectra) which introduce artificial visual boundaries.
- Missing physical units on axes, or using arbitrary units (a.u.) when absolute calibration is possible.
- Unclear Brillouin zone paths in band structure plots.

**What to Recommend:**
- Suggest perceptually uniform colormaps (e.g., viridis, plasma).
- Demand standard SI or common physics units (e.g., meV, $\mu\Omega\cdot$cm, Tesla).
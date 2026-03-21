# Scientific Reporting Standards for Condensed Matter Physics

This document catalogs major reporting standards across physics disciplines. When reviewing manuscripts, verify that authors have followed the appropriate guidelines for their methodology.

## Experimental Condensed Matter Physics

### General APS/IOP Experimental Guidelines
**Purpose:** Ensure reproducibility of table-top and facility-based experiments.
**Key Requirements:**
- **Apparatus:** Detailed description of custom equipment; manufacturer/model for commercial instruments.
- **Environment:** Precise conditions during measurement (Temperature ranges, cooling rates, vacuum levels, applied magnetic fields).
- **Calibration:** Details of reference samples, background subtraction, and instrument limits (e.g., noise floor).
- **Uncertainty:** Explicit separation of random (statistical) and systematic (geometric, thermal) uncertainties.

### Crystallography and Structure Reporting
**Purpose:** Standardize the reporting of crystal structures.
**Key Requirements:**
- **CIF Files:** Crystallographic Information Files (CIF) must be provided as supplementary material or deposited in databases (e.g., ICSD, CCDC).
- **Refinement:** R-factors ($R_1$, $wR_2$, Goodness-of-Fit) must be explicitly reported.
- **Data Collection:** X-ray/Neutron wavelength, temperature of measurement, and absorption corrections must be documented.

### Spectroscopy and Microscopy (ARPES, STM, TEM, NMR)
**Purpose:** Ensure transparency in complex spectral and imaging data.
**Key Requirements:**
- **Resolution:** Explicitly state energy, momentum, and spatial resolutions.
- **Probe Specs:** Photon energy, polarization, tip material, tunneling setpoint (voltage/current).
- **Processing:** Complete transparency on background subtraction, smoothing, and Fourier filtering.
- **Raw Data:** Representative raw spectra must be available to validate processed maps.

## Theoretical and Computational Physics

### First-Principles / DFT Reporting
**Purpose:** Ensure ab initio calculations can be exactly replicated.
**Key Requirements:**
- **Codebase:** Software name and specific version (e.g., VASP 6.3.0, Quantum Espresso 7.1).
- **Functionals:** Exchange-correlation functional precisely defined (e.g., PBE, SCAN, HSE06).
- **Pseudopotentials:** Type and valence electron configurations used (e.g., PAW, norm-conserving).
- **Convergence:** Energy cutoffs, k-point mesh density (e.g., $\Gamma$-centered $12\times12\times12$), and force/energy convergence criteria.
- **Corrections:** Details of Hubbard $U$ values, Spin-Orbit Coupling (SOC), or van der Waals corrections (e.g., DFT-D3).

### Many-Body Theory and Models (Tight-Binding, DMFT)
**Purpose:** Ensure phenomenological and correlated models are well-defined.
**Key Requirements:**
- **Hamiltonian:** Explicit mathematical statement of the model Hamiltonian.
- **Basis:** Definition of the orbital/spin basis used.
- **Parameters:** A table of all hopping parameters ($t, t'$), interaction strengths ($U, J$), and chemical potentials.
- **Solver Details:** For DMFT or Quantum Monte Carlo, details on the impurity solver, temperature, and analytical continuation methods (e.g., MaxEnt) to the real axis.

## Data and Code Availability

### Physics Data Repositories
**Purpose:** Long-term preservation of datasets.
**Key Requirements:**
- **Raw Data:** Deposit raw and processed data corresponding to figures in repositories (Zenodo, Figshare, Dryad, or university archives).
- **DOIs:** Provide a specific DOI linked to the dataset in the "Data Availability" statement.
- **Preprints:** Cross-reference with arXiv postings where applicable.

### Software and Custom Code
**Purpose:** Reproducibility of custom simulations or data analysis pipelines.
**Key Requirements:**
- **Accessibility:** Custom scripts (Python, MATLAB, Julia) used for fitting or theoretical modeling should be available via GitHub or Zenodo.
- **Documentation:** Code must include a README and dependencies.
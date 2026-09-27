# H2-PRISM Scientific Assumptions Register

This document tracks all physical, mathematical, and data assumptions made across Person 1, Person 2, and Person 3.

## Classification System:
- **VERIFIED**: Directly confirmed from source files or official documentation.
- **DERIVED**: Calculated from verified data.
- **ASSUMED**: Introduced by the team for modeling purposes.
- **UNKNOWN**: Not established or cannot be observed.

---

### 1. Temperature Availability
- **Status**: ASSUMED / UNVERIFIED
- **Source**: Dataset schema inspection
- **Evidence**: Temperature channels are not present in standard H2-SimNet files.
- **Effect on prototype**: Isothermal assumption (T = 293.15 K) or nominal approximation used in density calculations.

### 2. Hydrogen Compressibility & Density
- **Status**: ASSUMED
- **Source**: Hydrogen Equation of State (EOS)
- **Evidence**: Compressibility factor Z is pressure-dependent (Z ~ 1 + 0.00058 * P_bar).
- **Effect on prototype**: Used in line-pack mass estimation.

### 3. Line-Pack Mass Approximation
- **Status**: ASSUMED
- **Source**: Pipeline engineering approximation M_line = A * L * rho_mean.
- **Evidence**: Internal density profile rho(x, t) cannot be measured from two end stations.
- **Effect on prototype**: Line-pack correction carries quantifiable uncertainty, propagated into z_MB.

### 4. Acoustic Wave Speed & Propagation Delay
- **Status**: ASSUMED
- **Source**: Speed of sound in gaseous hydrogen (~1250 - 1350 m/s depending on P, T).
- **Evidence**: Acoustic pressure wave travels pipe length L in tau = L / a seconds.
- **Effect on prototype**: Binds the theoretical localization resolution floor delta = a * dt / 2.

### 5. Sensor Fault Labels
- **Status**: ASSUMED / SYNTHETIC
- **Source**: H2-SimNet dataset limitations
- **Evidence**: Raw dataset does not include labeled sensor drift/bias.
- **Effect on prototype**: Injected synthetically and kept strictly separated from primary validation metrics.

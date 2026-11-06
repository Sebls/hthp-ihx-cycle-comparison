# Development audit: S0 versus S4 IHX heat pump

Audit date: 6 November 2026. Scope: the project assignment, Python script, notebook,
LaTeX source and compiled report, dependency configuration, bundled Caldis 0.4.1
wheel, adjacent Caldis source, and nested repository status. This is an assessment;
the model and report have not been changed.

## Overall assessment

The project is at the specification and partial implementation stage. The assignment
and reference diagrams are available, the report defines the intended case correctly
in most respects, and property lookups and sink-water mass flow are working.
Neither cycle has a demonstrated design solve. S0 stops during component creation;
S4 has no implementation. No comparison, parameter study, energy/exergy analysis,
or results export is implemented.

The main risk is interpreting the IHX incorrectly. Under the specified idealizations,
the nominal S4 case cannot improve COP over S0: the compressor inlet, discharge,
and condenser outlet states are identical. It can change the distribution of duties
and the approximate exchanger sizes. Changing suction superheat, rather than just
evaporator quality, changes COP and discharge temperature.

## Requirements and current coverage

| Assignment requirement | Current evidence | Remaining work |
| --- | --- | --- |
| Common water-to-water, 100 kW design case | Report and initial inputs match | Replace air-side evaporator code |
| R1233zd(E), efficiency 0.70, prescribed film coefficients | Report correct | Remove efficiency override and coefficients copied from another case |
| Baseline S0 using shared components | Partial component assembly | Resolve names, boundaries, closures, initialization, and solve |
| S4 with quality 0.90 and suction superheat 5 K | Report specifies both | Implement complete six-state cycle and IHX |
| Heating COP, discharge temperature, exchanger areas, pressure ratio | Described in report | Compute, validate, export, and compare |
| Energy and exergy balances | Mentioned in report/library discussion | Implement both with clear system boundaries and reference state |
| Parametric analysis and physical interpretation | Intended quality/superheat sweep | Build feasible-domain sweep and quantify trade-offs |
| Single commented code file | Matching `.py` and notebook currently exist | Select authoritative submission and maintain synchronization |
| Report at most 10 pages | Source builds to 5 pages | Replace placeholders and allocate room for results |
| Reproducible execution | README and requirements exist | Repair entry point, Caldis installation, and environment instructions |

## Blocking and high-priority findings

### 1. S0 cannot run to a solve

`Project_IHX.py:90-92` uses undefined `p_w`, `T_w_in`, and `T_w_out`.
A run with the bundled Caldis 0.4.1 wheel stops at line 91 with
`NameError: name 'p_w' is not defined`.

Further undefined names remain: `T_a_in`, `T_a_out`, `comp`, `cond`, `evap`,
`T_cd`, `p_cd`, `p_ev`, and `T_ev`. Components were created as `compressor`,
`condensor`, and `evaporator`, while assembly uses different identifiers
at lines 107-130. Fixing the first exception alone will not make the model runnable.

The file parses successfully. This is an incomplete implementation, not a syntax
problem. The notebook contains the same executable code and has not executed the
component/solve cell. Its saved outputs establish only property lookups and water
flow, not a converged cycle.

### 2. Implemented inputs diverge from the specification

- Lines 78-79 insert `mdot_r = 0.03` and overwrite `eta_is = 0.70` with `0.85`.
  The mass-flow variable is currently unused; it must not become an additional
  fixed closure because the 100 kW condenser duty determines refrigerant flow.
- Lines 82-88 use refrigerant film coefficient 2500 rather than 3000 W/(m² K).
- Lines 95-101 build an air-source evaporator with coefficients 2500/50 and an
  area ratio of 1/15. The assigned source is water at 3 bar, cooling 35 to 30°C,
  with coefficients 3000/3000 and area ratio 1:1.
- Lines 43-44 label subcooling and superheat at the wrong outlets. Subcooling is
  at the condenser outlet; S0 superheat is at the evaporator outlet.

### 3. S4 is absent

The S4 heading at line 144 is followed by an empty section. It needs an IHX whose
hot side connects condenser outlet to valve inlet, and whose cold side connects
evaporator outlet to compressor inlet. Use the refrigerant backend on both sides.
Impose evaporator outlet quality separately from compressor suction superheat.
No new custom component is required for S4: the assigned single-zone `SizingHX`
can represent the IHX.

### 4. The report contains an incorrect limiting-case statement

`report/report.tex:100` says the IHX duty vanishes at quality 1 and suction superheat
5 K. Saturated vapor entering the IHX still needs heat to become superheated by
5 K. The assignment itself says S4 reduces to S0 at this point; the report adds
the stronger, incorrect zero-duty explanation.

Use more precise wording: **at the default suction superheat, S4 matches S0 in
compressor/condenser states, COP, compressor power, and discharge temperature;
the evaporator and IHX duties and sizes can differ.** This performance equivalence
also holds for other feasible evaporator qualities at the same suction superheat,
under the specified fixed-pressure, fixed-subcooling, zero-loss assumptions.

Let 1 be compressor inlet, 2 compressor outlet, 3 condenser outlet, 4 IHX liquid
outlet/valve inlet, 5 valve outlet, and 6 evaporator outlet. Then

\[
h_4=h_3-(h_1-h_6),\qquad h_5=h_4,
\]
\[
\dot Q_{evap}=\dot m(h_6-h_5)=\dot m(h_1-h_3).
\]

Thus varying quality at state 6 changes internal duty, not external evaporator duty,
when states 1 and 3 are fixed. Also

\[
\dot m=\frac{100000}{h_2-h_3},\quad
W_{in}=\dot m(h_2-h_1),\quad
COP_h=\frac{h_2-h_3}{h_2-h_1}.
\]

Quality does not appear in these expressions. Do not promise a COP increase from
quality alone. Pressure drops, compressor-efficiency variation, or other extensions
could alter this conclusion, but are outside the prescribed nominal model.

### 5. Reproducibility depends on the interpreter and launch directory

The default Python 3.12 interpreter lacks NumPy, CoolProp, SciPy, and Matplotlib.
An existing environment at `../examples/code/.venv` has these dependencies, but is
not a project installation. Running from the parent workspace imports adjacent
Caldis source reporting version 0.4.0. Explicitly selecting the supplied wheel
loads 0.4.1. The two versions differ, including their exergy interfaces.

`requirements.txt` omits the now-available Caldis wheel and has no version pins.
Create a dedicated environment, install the supplied wheel, record tested dependency
versions, and print both Caldis version and import path during verification. Do not
modify the shared library to compensate for project wiring or closure errors.

### 6. Library output conventions need explicit handling

The supplied compressor reports absorbed power as **negative** `comp.Wdot`.
For reporting, define positive input power as `W_in = -comp.Wdot`, then use
`COP_h = Q_cond / W_in` with a verified positive condenser heat-delivery convention.
The report's current nomenclature does not explain this distinction.

`SizingHX.A_total` means **hot-side area plus cold-side area**. With area ratio 1,
it is twice `A_hot`. Its hot-side overall coefficient at film coefficients
3000/3000 is 1500 W/(m² K). Clearly distinguish each exchanger's `A_total` from
the sum across condenser, evaporator, and IHX; count the IHX once.

The solver's default `strict_physical=False` can leave numerical success true
despite a physical warning. Its LMTD calculation floors nonpositive terminal
approaches. Require successful convergence, physical validity, and explicitly
positive terminal approaches before accepting or plotting a point. An apparently
finite area is not sufficient evidence of feasibility.

## Independent numerical cross-check

These are direct CoolProp 8.0.0 property calculations using the specified
isentropic compressor and enthalpy balances. They are **verification targets,
not results produced by the unfinished Caldis model**. No nonlinear system solve
was completed during this audit.

| Quantity | S0 | Nominal S4: quality 0.90, suction superheat 5 K |
| --- | ---: | ---: |
| Condensing pressure | 20.9874 bar | same |
| Evaporating pressure | 1.30336 bar | same |
| Pressure ratio | 16.1025 | same |
| Sink-water flow | 2.35281 kg/s | same |
| Refrigerant flow | 0.786728 kg/s | same |
| Compressor input | 57.0084 kW | same |
| Heating COP | 1.75413 | same |
| Discharge temperature | 145.055°C | same |
| External evaporator duty | 42.9916 kW | same |
| Source-water flow | 2.05753 kg/s | same |
| IHX duty | absent | 18.2060 kW |

At quality 1 and suction superheat 5 K, the calculated IHX duty is still
3.18668 kW. The first-law residual of the direct reference calculation is below
1e-8 W; this verifies its algebra, not the accuracy of the assigned exchanger
approximation.

Using the assigned endpoint LMTD sizing equations, the approximate summed
two-sided area is 22.2558 m² for S0 and 18.9938 m² for nominal S4, including its
IHX. These are useful comparison targets, but a reduction here concerns this
single-zone approximation, not demonstrated hardware savings. It does not include
pressure losses, cost, detailed temperature profiles, or variable film coefficients.

A preliminary suction-superheat check gives COP/discharge temperature pairs of
1.78919/149.767°C at 10 K, 1.85803/159.471°C at 20 K, and
1.92388/169.540°C at 30 K. These are algebraic reference points, not a fully
screened sweep or operating recommendations. They show why the analysis should
quantify the COP-versus-discharge-temperature trade-off without assuming its sign.

## Report assessment

The latest source compiles to five pages. Pages 2-4 were rendered and visually
inspected. One minor overfull box of 1.66 pt occurs in the nomenclature table.
The existing PDF predates the latest source modification, so rebuild it after
the substantive corrections.

The introduction, fixed specification, diagrams, and assumptions are largely
ready. However, sections 2-5 are instructions/placeholders, not completed research.
The report describes implementation and post-processing that do not yet exist.
Use planned/future wording until those calculations are demonstrated.

The nomenclature occupies about a page and the introductory specification occupies
most of the current report. Reduce these to preserve space for state tables,
equations, results, parameter plots, balances, limitations, and conclusions.
The `main.ipynb` reference at line 149 is obsolete.

Keep the mandated single-zone approximation. The assignment calls it constant-cp;
the actual `SizingHX` implementation uses real-fluid enthalpy balances and an
endpoint LMTD, without directly evaluating cp. Explain both the prescribed
approximation and the implementation rather than claiming detailed phase-change
resolution or a guaranteed minimum pinch throughout the exchanger.

Exergy analysis needs a documented common dead state `(T0, p0)`, component entropy
generation/destruction, and a whole-system check. Include both water streams:
source-water exergy depletion plus compressor work supplies sink-water exergy
gain and destruction. The IHX duty is internal and must not be counted as useful
heat supplied externally. Verify library balances independently from signed stream
states before relying on summary tables.

## Repository and documentation state

The project is an independent nested Git repository. Its last two commits are
scaffold commits; current substantive development is not committed. Git shows
`main.ipynb` deleted, the Python/notebook files untracked, report modifications,
and the assignment/library/assets untracked. Local work exists, but the current
revision cannot be reconstructed from committed history alone.

The README still says no advanced cycle is selected, the shared library must be
obtained, and execution uses `main.ipynb`. Those statements are obsolete. Correct
the file tree, S4 selection, installation steps, authoritative entry point, run
instructions, generated-output locations, and report build instructions. Make a
reviewed checkpoint commit after deciding which bundled materials belong in Git.

The notebook and script currently have equal executable syntax trees. That is a
good starting point, but there is no documented mechanism to keep them synchronized.
Choose the `.py` as the authoritative file or the notebook as the authoritative
file; submit one self-contained commented file as required.

## Recommended development sequence

### Milestone 1: reproducible S0

1. Establish the dedicated environment and explicit Caldis 0.4.1 import.
2. Consolidate the common specification and consistent names.
3. Replace the air loop with the specified source-water loop.
4. Assemble S0 with two pressure closures, condenser subcooling, evaporator
   superheat, and the 100 kW condenser duty. Leave mass flows to the solve.
5. Use direct property states as initialization and cross-checks; confirm zero
   remaining degrees of freedom before solving.
6. Export a state table and the complete nominal metric set.

**Completion gate:** clean execution from the documented location, successful and
physical Caldis solve, agreement with direct property references, positive heat/work
magnitudes, and a documented scaled energy-balance tolerance. A reasonable initial
target is relative energy residual below 1e-6 of the 100 kW duty.

### Milestone 2: nominal S4 and conservation checks

1. Reuse the S0 inputs and comparison basis in a separate cycle-building function
   within the same submission file.
2. Add the IHX and six named states. Use an enthalpy closure derived from `(p, x)`
   for the two-phase evaporator outlet; temperature alone cannot fix its quality.
3. Enforce suction superheat at the compressor inlet, not the evaporator outlet.
4. Check the IHX balance, valve enthalpy equality, mass conservation, water duties,
   and whole-cycle first law. Confirm the nominal COP equality explained above.
5. Add component and system exergy checks with a stated dead state.

**Completion gate:** validated S0/S4 metric and state tables, including each area,
IHX duty, energy residuals, and exergy destruction; no unsupported performance claims.

### Milestone 3: feasible quality/superheat study

Start with a quality range such as 0.80-1.00 and positive suction superheat such as
5-30 K; these are proposed exploratory ranges, not assignment limits or guaranteed
feasible operating conditions. Expand only after screening. Rebuild independent
systems or carefully reset state; use continuation from neighboring valid points
when useful, and record failures rather than silently dropping them.

Screen for valid property calls, forward duties/flows, positive evaporator effect,
dry compressor suction, positive terminal temperature approaches, finite positive
areas, solver residuals, and nonnegative entropy generation within tolerance.
Use a discharge-temperature cap only if it is sourced or explicitly labelled as
a study assumption; the assignment supplies no numerical hard limit.

Prioritize three figures: COP and discharge temperature versus suction superheat;
total area and IHX duty versus quality at fixed suction superheat; and a feasible
two-parameter map or Pareto comparison of COP, temperature, and area. Pressure
ratio is invariant under this fixed-pressure sweep; show it as a common metric,
not an expected optimization outcome.

**Completion gate:** repeatable exported sweep data and plots, marked infeasible
points, explained trends, and a justified trade-off rather than a single unconstrained
claim of an optimum.

### Milestone 4: complete the submission

Replace report placeholders with equations, selected state/metric tables, balance
checks, the key sweep figures, qualified conclusions, and references. Generate plots
and tables from the same saved calculations to avoid transcription drift. Target
roughly 1 page for the case/assumptions, 2 for models and validation, 2 for nominal
comparison/balances, 3 for parameter analysis, and 1 for conclusions/references,
leaving layout margin below the 10-page maximum. Rebuild and visually inspect the
entire final PDF, then run the authoritative code from a clean session and save a
reviewed repository checkpoint.

## Immediate priority

Finish and verify S0 before adding more report prose or extending the cycle.
Then implement S4 and use its expected nominal COP equality as a regression check.
The meaningful larger investigation is how suction superheat trades efficiency
against discharge temperature, and how evaporator quality redistributes exchanger
duty and approximate area.

# Strategy Library Expansion Plan

## Overview
Expand `strategy_library.py` with 44 new strategies (total 56) and create 4 YAML strategy files.

## Step 1: Modify `strategy_library.py` — Top of file changes
- Add `import os` 
- Add try/except for yaml (fallback to json)

```python
import os

try:
    import yaml
except ImportError:
    yaml = None
```

## Step 2: Add 44 new strategies to `_BUILT_IN_STRATEGIES` (after existing 12)

### Math Algebra (10 strategies)
1. `strat_math_alg_linear_eq_concept` — linear_equations, concept_clarification
2. `strat_math_alg_linear_eq_error` — linear_equations, error_analysis  
3. `strat_math_alg_linear_eq_guided` — linear_equations, guided_discovery
4. `strat_math_alg_quadratic_concept` — quadratic_equations, concept_clarification
5. `strat_math_alg_quadratic_error` — quadratic_equations, error_analysis
6. `strat_math_alg_quadratic_counter` — quadratic_equations, counter_example
7. `strat_math_alg_functions_analogy` — functions, analogy
8. `strat_math_alg_functions_explain` — functions, self_explanation
9. `strat_math_alg_ineq_concept` — inequalities, concept_clarification
10. `strat_math_alg_ineq_guided` — inequalities, guided_discovery

### Math Geometry (6 strategies)
11. `strat_math_geo_triangle_concept` — triangles, concept_clarification
12. `strat_math_geo_triangle_guided` — triangles, guided_discovery
13. `strat_math_geo_circle_analogy` — circles, analogy
14. `strat_math_geo_circle_explain` — circles, self_explanation
15. `strat_math_geo_coord_error` — coordinate_geometry, error_analysis
16. `strat_math_geo_coord_counter` — coordinate_geometry, counter_example

### Math Number Theory (3 strategies)
17. `strat_math_nt_divisibility_concept` — divisibility, concept_clarification
18. `strat_math_nt_primes_guided` — primes, guided_discovery
19. `strat_math_nt_gcd_analogy` — gcd_lcm, analogy

### Physics (8 strategies)
20. `strat_phys_mechanics_concept` — mechanics, concept_clarification
21. `strat_phys_mechanics_error` — mechanics, error_analysis
22. `strat_phys_motion_guided` — motion, guided_discovery
23. `strat_phys_motion_explain` — motion, self_explanation
24. `strat_phys_forces_analogy` — forces, analogy
25. `strat_phys_forces_counter` — forces, counter_example
26. `strat_phys_energy_concept` — energy, concept_clarification
27. `strat_phys_energy_guided` — energy, guided_discovery

### Chemistry (3 strategies)
28. `strat_chem_reactions_concept` — reactions, concept_clarification
29. `strat_chem_mole_error` — mole_concept, error_analysis
30. `strat_chem_periodic_analogy` — periodic_table, analogy

### Biology (3 strategies)
31. `strat_bio_cell_concept` — cell_structure, concept_clarification
32. `strat_bio_genetics_guided` — genetics, guided_discovery
33. `strat_bio_ecology_explain` — ecology, self_explanation

### Chinese (5 strategies)
34. `strat_chn_reading_concept` — reading_comprehension, concept_clarification
35. `strat_chn_reading_explain` — reading_comprehension, self_explanation
36. `strat_chn_essay_guided` — essay_writing, guided_discovery
37. `strat_chn_essay_counter` — essay_writing, counter_example
38. `strat_chn_classical_analogy` — classical_chinese, analogy

### English (3 strategies)
39. `strat_eng_grammar_error` — grammar, error_analysis
40. `strat_eng_grammar_counter` — grammar, counter_example
41. `strat_eng_vocab_analogy` — vocabulary, analogy

### Programming (3 strategies)
42. `strat_prog_debug_error` — debugging, error_analysis
43. `strat_prog_debug_counter` — debugging, counter_example
44. `strat_prog_algo_guided` — algorithm, guided_discovery

## Step 3: Add `load_from_yaml()` and `load_from_directory()` methods to `StrategyLibrary`

## Step 4: Update `__init__` to auto-load from YAML directory

## Step 5: Create YAML files
- `apps/backend/app/data/strategies/yaml_strategies/math_algebra.yaml` (10 strategies)
- `apps/backend/app/data/strategies/yaml_strategies/math_geometry.yaml` (6 strategies)
- `apps/backend/app/data/strategies/yaml_strategies/physics.yaml` (8 strategies)
- `apps/backend/app/data/strategies/yaml_strategies/chinese.yaml` (5 strategies)

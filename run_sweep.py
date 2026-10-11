import pandas as pd

from preprocessing.schema import profile_dataset
from preprocessing.pipeline import Preprocessor, train_test_split_no_leakage
from experiments.config import SweepConfig
from experiments.runner import run_single_experiment, compute_trtr_once

print("Loading dataset...")
df = pd.read_csv("data/example_dataset.csv")

print("Profiling dataset...")
profile = profile_dataset(df)

numerical_cols = [
    c.name for c in profile.columns
    if c.inferred_type == "numerical"
]

categorical_cols = [
    c.name for c in profile.columns
    if c.inferred_type == "categorical"
]

# The README explicitly includes income as the target categorical column
if "income" not in categorical_cols:
    categorical_cols.append("income")

print("Splitting dataset...")
train_df, test_df = train_test_split_no_leakage(
    df,
    test_size=0.2,
    random_seed=42,
    stratify_column="income"
)

print("Preparing preprocessor...")
pp = Preprocessor(
    rare_threshold=0.01,
    n_bins=10,
    random_seed=42
)

pp.fit(
    train_df,
    numerical_columns=numerical_cols,
    categorical_columns=categorical_cols,
    target_column="income",
    sensitive_column="sex"
)

print("Computing TRTR reference...")
compute_trtr_once(
    train_df,
    test_df,
    pp,
    numerical_cols,
    categorical_cols,
    "income"
)

print("Building experiment sweep...")
sweep = SweepConfig(dataset_name="adult_example")

configs = sweep.build_run_configs()
print(f"Total configurations: {len(configs)}")

for i, config in enumerate(configs, start=1):
    print(
        f"\n[{i}/{len(configs)}] "
        f"{config.method} epsilon={config.epsilon} seed={config.random_seed}"
    )

    try:
        result = run_single_experiment(
            config,
            train_df,
            test_df,
            pp,
            numerical_cols,
            categorical_cols,
            target_column="income",
            sensitive_column="sex",
        )

        print("Result:", result)

    except Exception as e:
        print("Experiment crashed:", repr(e))

print("\nFULL SWEEP SCRIPT FINISHED")
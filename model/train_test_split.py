#!/usr/bin/env python3
import pandas as pd
from sklearn.model_selection import train_test_split
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Split augmented data CSV into train, test, and validation CSV files."
    )
    parser.add_argument(
        "--input_csv", type=str, default="model/augmented_training_data.csv",
        help="Path to the augmented data CSV file."
    )
    parser.add_argument(
        "--train_csv", type=str, default="model/train.csv",
        help="Output path for the training CSV file."
    )
    parser.add_argument(
        "--test_csv", type=str, default="model/test.csv",
        help="Output path for the test CSV file."
    )
    parser.add_argument(
        "--valid_csv", type=str, default="model/valid.csv",
        help="Output path for the validation CSV file."
    )
    parser.add_argument(
        "--test_size", type=float, default=0.15,
        help="Fraction of data to use for the test set (default: 0.15)."
    )
    parser.add_argument(
        "--valid_size", type=float, default=0.15,
        help="Fraction of data to use for the validation set (default: 0.15)."
    )
    args = parser.parse_args()

    # Load the augmented CSV file.
    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} examples from '{args.input_csv}'.")

    # Ensure that test_size + valid_size is less than 1.
    if args.test_size + args.valid_size >= 1.0:
        raise ValueError("The sum of test_size and valid_size must be less than 1.")

    # Calculate the training fraction.
    train_fraction = 1.0 - (args.test_size + args.valid_size)

    # First split: train set and temp set (temp will be split into test and valid).
    train_df, temp_df = train_test_split(df, test_size=(args.test_size + args.valid_size), random_state=42)
    print(f"Initial split: {len(train_df)} train examples, {len(temp_df)} temp examples.")

    # Calculate the ratio for splitting temp into test and validation.
    # For example, if test_size and valid_size are both 0.15, then test_ratio = 0.15 / (0.15+0.15) = 0.5.
    test_ratio = args.test_size / (args.test_size + args.valid_size)

    # Second split: temp set into test and valid.
    test_df, valid_df = train_test_split(temp_df, test_size=(1 - test_ratio), random_state=42)
    print(f"Final split: {len(train_df)} train examples, {len(test_df)} test examples, {len(valid_df)} validation examples.")

    # Save the splits to CSV files.
    train_df.to_csv(args.train_csv, index=False)
    test_df.to_csv(args.test_csv, index=False)
    valid_df.to_csv(args.valid_csv, index=False)
    print(f"Saved train data to '{args.train_csv}', test data to '{args.test_csv}', and validation data to '{args.valid_csv}'.")

if __name__ == "__main__":
    main()

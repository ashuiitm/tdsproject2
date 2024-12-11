import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import argparse
import numpy as np

# Ensure API key is set
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable is not set.")
    sys.exit(1)


def load_data(file_path):
    try:
        df = pd.read_csv(file_path , encoding="ISO-8859-1")
        print(f"Successfully loaded {file_path}")
        return df
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        sys.exit(1)

def basic_analysis(df):
    summary = df.describe(include="all").to_dict()
    missing_values = df.isnull().sum().to_dict()
    dtypes = df.dtypes.astype(str).to_dict()
    sample_data = df.head().to_dict(orient="records")
    return {
        "summary": summary,
        "missing_values": missing_values,
        "dtypes": dtypes,
        "sample_data": sample_data
    }

def correlation_analysis(df):
    numeric_cols = df.select_dtypes(include=["float", "int"])
    if numeric_cols.shape[1] > 1:
        corr_matrix = numeric_cols.corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        plt.savefig("correlation_matrix.png")
        plt.close()
        return corr_matrix.to_dict()
    return None

def outlier_detection(df):
    numeric_cols = df.select_dtypes(include=["float", "int"])
    outliers = {}
    for col in numeric_cols.columns:
        q1 = numeric_cols[col].quantile(0.25)
        q3 = numeric_cols[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers[col] = numeric_cols[(numeric_cols[col] < lower_bound) | (numeric_cols[col] > upper_bound)][col].tolist()
    return outliers

def visualize_data(df):
    numeric_cols = df.select_dtypes(include=["float", "int"])
    if not numeric_cols.empty:
        for col in numeric_cols.columns:
            plt.figure(figsize=(6, 4))
            sns.histplot(df[col], kde=True, bins=30, color="blue")
            plt.title(f"Distribution of {col}")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            filename = f"{col}_distribution.png"
            plt.savefig(filename)
            plt.close()

def get_llm_analysis(df_info, charts):
    prompt = f"""
    You are analyzing a dataset. Below are its details:
    Data Types: {df_info['dtypes']}
    Missing Values: {df_info['missing_values']}
    Summary Statistics: {df_info['summary']}
    Sample Data: {df_info['sample_data']}
    Charts Generated: {charts}
    
    Write a story summarizing:
    1. A description of the dataset.
    2. Key analyses performed.
    3. Insights derived.
    4. Implications and possible actions.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error with LLM analysis: {e}")
        sys.exit(1)

def save_story(story):
    with open("README.md", "w") as f:
        f.write(story)
    print("Story saved to README.md.")

def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Automated data analysis and storytelling.")
    parser.add_argument("csv_file", help="Path to the CSV file.")
    args = parser.parse_args()

    # File loading
    file_path = args.csv_file
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        sys.exit(1)

    # Data loading
    df = load_data(file_path)

    # Basic analysis
    df_info = basic_analysis(df)

    # Correlation analysis
    correlation_data = correlation_analysis(df)
    if correlation_data:
        df_info["correlation"] = correlation_data

    # Outlier detection
    outliers = outlier_detection(df)
    df_info["outliers"] = outliers

    # Visualization
    visualize_data(df)
    generated_charts = ["correlation_matrix.png"] + [f"{col}_distribution.png" for col in df.select_dtypes(include=["float", "int"]).columns]

    # LLM storytelling
    story = get_llm_analysis(df_info, generated_charts)

    # Save story
    save_story(story)

if __name__ == "__main__":
    main()

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "numpy",
#   "matplotlib",
#   "seaborn",
#   "openai",
#   "tenacity",
# ]
# ///

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tenacity import retry, stop_after_attempt, wait_exponential
import openai

# Environment variable for AI Proxy Token
API_TOKEN = os.environ.get("AIPROXY_TOKEN")

# OpenAI API Configuration
openai.api_key = API_TOKEN

# Define function to validate and read the dataset
def load_dataset(filename):
    try:
        df = pd.read_csv(filename)
        print(f"Dataset loaded successfully: {filename}")
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        exit(1)

# Perform initial analysis
def analyze_dataset(df):
    summary = df.describe(include="all").transpose()
    missing_values = df.isnull().sum()
    return summary, missing_values

# Visualize results
def create_charts(df, output_prefix):
    # Example: Correlation heatmap
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        corr_matrix = numeric_df.corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")
        plt.title("Correlation Matrix")
        plt.savefig(f"{output_prefix}_correlation.png")
        plt.close()

# Generate narrative using LLM
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_narrative(summary, missing_values, charts):
    prompt = f"""
    I analyzed a dataset and found the following summary statistics and missing value information:
    Summary Statistics:
    {summary.to_string()}
    
    Missing Values:
    {missing_values.to_string()}
    
    Here are the charts created:
    {charts}
    
    Write a concise narrative summarizing the dataset, the analysis performed, and the key insights.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Main execution
def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        exit(1)
    
    input_file = sys.argv[1]
    df = load_dataset(input_file)
    summary, missing_values = analyze_dataset(df)
    
    # Create charts
    create_charts(df, output_prefix="output")
    
    # Generate narrative
    narrative = generate_narrative(summary, missing_values, ["output_correlation.png"])
    
    # Write README.md
    with open("README.md", "w") as f:
        f.write("# Analysis Report\n\n")
        f.write(narrative)
        f.write("\n\n![Correlation Matrix](output_correlation.png)\n")
    
    print("Analysis completed. Results saved to README.md.")

if __name__ == "__main__":
    main()

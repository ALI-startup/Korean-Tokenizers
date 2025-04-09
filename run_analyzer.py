import os
import sys
import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any
from token_analyzer import token_analysis 
import numpy as np

def run_analysis_for_models(model_ids: List[str], output_dir: str = "tokenizer_analysis_results"):
    """
    Run tokenizer analysis for multiple models and save results to specified directory.
    
    Args:
        model_ids: List of model IDs to analyze
        output_dir: Directory to save individual analysis results
    
    Returns:
        List of paths to the analysis result files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    result_files = []
    
    # Run analysis for each model
    for model_id in model_ids:
        model_name = model_id.split('/')[-1]
        output_file = os.path.join(output_dir, f"{model_name}_analysis.json")
        
        print(f"\n{'='*80}")
        print(f"Analyzing tokenizer: {model_id}")
        print(f"{'='*80}")
        
        # Run analysis
        token_analysis(model_id, output_file)
        
        result_files.append(output_file)
    
    return result_files


def load_analysis_results(result_files: List[str]) -> List[Dict[str, Any]]:
    """
    Load analysis results from JSON files.
    
    Args:
        result_files: List of paths to analysis result files
    
    Returns:
        List of analysis result dictionaries
    """
    results = []
    
    for file_path in result_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            results.append(json.load(f))
    
    return results


def create_comparison_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a pandas DataFrame with comparison data.
    
    Args:
        results: List of analysis result dictionaries
    
    Returns:
        DataFrame with comparison data
    """
    comparison_data = []
    
    for result in results:
        model_id = result['model_id']
        stats = result['statistics']
        
        row = {
            'Model': model_id.split('/')[-1],
            'Total Tokens': stats['total_tokens'],
            'Pure English': stats['pure_english'],
            'Pure English (%)': round(stats['pure_english'] / stats['total_tokens'] * 100, 2),
            'Hangul Possible': stats['hangul_possible'],
            'Hangul Possible (%)': round(stats['hangul_possible'] / stats['total_tokens'] * 100, 2),
            'Complete Hangul': stats['complete_hangul'],
            'Complete Hangul (%)': round(stats['complete_hangul'] / stats['total_tokens'] * 100, 2),
            'Special Chars': stats['special_char'],
            'Special Chars (%)': round(stats['special_char'] / stats['total_tokens'] * 100, 2),
            'Uncategorized': stats['uncategorized'],
            'Uncategorized (%)': round(stats['uncategorized'] / stats['total_tokens'] * 100, 2),
        }
        
        comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)


def create_absolute_count_histogram(df: pd.DataFrame, output_dir: str):
    """
    Create histograms comparing absolute token counts across models.
    
    Args:
        df: DataFrame with comparison data
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(15, 10))
    
    # Prepare data for plotting
    plot_df = df.melt(
        id_vars=['Model'],
        value_vars=['Pure English', 'Hangul Possible', 'Complete Hangul', 'Special Chars', 'Uncategorized'],
        var_name='Category',
        value_name='Count'
    )
    
    # Create grouped bar chart
    ax = sns.barplot(x='Model', y='Count', hue='Category', data=plot_df, palette='viridis')
    
    plt.title('Absolute Token Count Comparison by Category', fontsize=16)
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Number of Tokens', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Token Category', title_fontsize=12, fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%d', fontsize=8)
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'absolute_token_count_comparison.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Absolute count histogram saved to: {output_path}")


def create_percentage_histogram(df: pd.DataFrame, output_dir: str):
    """
    Create histograms comparing percentage distribution of tokens across models.
    
    Args:
        df: DataFrame with comparison data
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(15, 10))
    
    # Prepare data for plotting
    plot_df = df.melt(
        id_vars=['Model'],
        value_vars=['Pure English (%)', 'Hangul Possible (%)', 'Complete Hangul (%)', 'Special Chars (%)', 'Uncategorized (%)'],
        var_name='Category',
        value_name='Percentage'
    )
    
    # Create grouped bar chart
    ax = sns.barplot(x='Model', y='Percentage', hue='Category', data=plot_df, palette='mako')
    
    plt.title('Percentage Distribution of Token Categories', fontsize=16)
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Percentage of Total Tokens', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Token Category', title_fontsize=12, fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', fontsize=8)
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'percentage_token_distribution_comparison.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Percentage histogram saved to: {output_path}")


def create_stacked_percentage_chart(df: pd.DataFrame, output_dir: str):
    """
    Create stacked bar chart showing percentage distribution of token categories.
    
    Args:
        df: DataFrame with comparison data
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(15, 8))
    
    # Extract required columns
    plot_df = df[['Model', 'Pure English (%)', 'Hangul Possible (%)', 
                 'Complete Hangul (%)', 'Special Chars (%)', 'Uncategorized (%)']]
    
    # Create stacked bar chart
    ax = plot_df.set_index('Model').plot(kind='bar', stacked=True, figsize=(15, 8), 
                                         colormap='viridis', width=0.7)
    
    plt.title('Distribution of Token Categories by Model', fontsize=16)
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Percentage', fontsize=14)
    plt.legend(title='Token Category', title_fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on bars
    # This is more complex for stacked bars
    for i, model in enumerate(plot_df['Model']):
        bottom = 0
        for j, column in enumerate(plot_df.columns[1:]):  # Skip 'Model' column
            height = plot_df.iloc[i][column]
            if height > 5:  # Only show percentages for segments that are big enough
                plt.text(i, bottom + height/2, f'{height:.1f}%', 
                         ha='center', va='center', fontsize=9, 
                         color='white' if j in [0, 2] else 'black')
            bottom += height
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'stacked_percentage_distribution.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Stacked percentage chart saved to: {output_path}")


def create_radar_chart(df: pd.DataFrame, output_dir: str):
    """
    Create radar chart comparing token category distributions.
    
    Args:
        df: DataFrame with comparison data
        output_dir: Directory to save the plot
    """
    # Set up variables for the chart
    categories = ['Pure English (%)', 'Hangul Possible (%)', 
                 'Complete Hangul (%)', 'Special Chars (%)', 'Uncategorized (%)']
    
    # Number of variables
    N = len(categories)
    
    # What will be the angle of each axis in the plot
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Create figure
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)
    
    # Draw one axis per variable and add labels
    plt.xticks(angles[:-1], [cat.replace(' (%)', '') for cat in categories], size=12)
    
    # Draw y-labels
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80], ["20%", "40%", "60%", "80%"], color="grey", size=10)
    plt.ylim(0, 100)
    
    # Plot each model
    for i, row in df.iterrows():
        model_name = row['Model']
        values = row[categories].values.tolist()
        values += values[:1]  # Close the loop
        
        # Plot values
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=model_name)
        ax.fill(angles, values, alpha=0.1)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title('Token Category Distribution Comparison (Radar Chart)', size=15, y=1.1)
    
    # Save plot
    output_path = os.path.join(output_dir, 'radar_chart_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Radar chart saved to: {output_path}")


def create_detailed_table(df: pd.DataFrame, output_dir: str):
    """
    Create a detailed HTML table with all comparison data.
    
    Args:
        df: DataFrame with comparison data
        output_dir: Directory to save the HTML file
    """
    # Style the DataFrame for better visualization
    styled_df = df.style.background_gradient(cmap='Blues', subset=[col for col in df.columns if '%' in col]) \
                       .format({col: '{:,.0f}' for col in df.columns if 'Total' in col or col in ['Pure English', 'Hangul Possible', 'Complete Hangul', 'Special Chars', 'Uncategorized']}) \
                       .format({col: '{:.2f}%' for col in df.columns if '%' in col}) \
                       .set_caption('Detailed Tokenizer Analysis Comparison')
    
    # Convert to HTML
    html_table = styled_df.to_html()
    
    # Add some CSS for better styling
    css = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
        }
        th, td {
            text-align: right;
            padding: 8px;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        caption {
            font-size: 1.5em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
    </style>
    """
    
    # Create complete HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tokenizer Analysis Comparison</title>
        {css}
    </head>
    <body>
        <h1>Tokenizer Analysis Comparison</h1>
        <p>This table shows a detailed comparison of token category distributions across different tokenizers.</p>
        {html_table}
        <div style="margin-top: 20px;">
            <h3>Explanation of Categories:</h3>
            <ul>
                <li><strong>Pure English:</strong> Tokens containing only English characters (A-Z, a-z)</li>
                <li><strong>Hangul Possible:</strong> Tokens that might contain Korean Hangul characters</li>
                <li><strong>Complete Hangul:</strong> Tokens that definitely contain complete Korean Hangul characters</li>
                <li><strong>Special Chars:</strong> Tokens containing only special characters (no alphanumeric characters)</li>
                <li><strong>Uncategorized:</strong> Tokens that don't fit into any of the above categories</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    # Save to file
    output_path = os.path.join(output_dir, 'detailed_comparison_table.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Detailed HTML table saved to: {output_path}")
    
    # Also save as CSV for easy import into other tools
    csv_path = os.path.join(output_dir, 'tokenizer_comparison_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"CSV data saved to: {csv_path}")


def generate_summary_report(df: pd.DataFrame, output_dir: str):
    """
    Generate a summary report in markdown format.
    
    Args:
        df: DataFrame with comparison data
        output_dir: Directory to save the report
    """
    # Calculate averages
    avg_row = {
        'Model': 'AVERAGE',
        'Total Tokens': df['Total Tokens'].mean(),
        'Pure English': df['Pure English'].mean(),
        'Pure English (%)': df['Pure English (%)'].mean(),
        'Hangul Possible': df['Hangul Possible'].mean(),
        'Hangul Possible (%)': df['Hangul Possible (%)'].mean(),
        'Complete Hangul': df['Complete Hangul'].mean(),
        'Complete Hangul (%)': df['Complete Hangul (%)'].mean(),
        'Special Chars': df['Special Chars'].mean(),
        'Special Chars (%)': df['Special Chars (%)'].mean(),
        'Uncategorized': df['Uncategorized'].mean(),
        'Uncategorized (%)': df['Uncategorized (%)'].mean(),
    }
    
    # Find model with highest percentages in each category
    best_models = {
        'Pure English': df.loc[df['Pure English (%)'].idxmax()]['Model'],
        'Hangul Possible': df.loc[df['Hangul Possible (%)'].idxmax()]['Model'],
        'Complete Hangul': df.loc[df['Complete Hangul (%)'].idxmax()]['Model'],
        'Special Chars': df.loc[df['Special Chars (%)'].idxmax()]['Model'],
        'Uncategorized': df.loc[df['Uncategorized (%)'].idxmax()]['Model'],
    }
    
    # Create summary report
    report = f"""# Tokenizer Analysis Summary Report

## Overview

This report provides a comparison of token category distributions across {len(df)} different tokenizers. The analysis categorizes tokens into several groups:

- **Pure English**: Tokens containing only English alphabetic characters
- **Hangul Possible**: Tokens that potentially contain Korean Hangul characters
- **Complete Hangul**: Tokens that definitely contain complete Korean Hangul characters
- **Special Characters**: Tokens consisting only of special characters (non-alphanumeric)
- **Uncategorized**: Tokens that don't fit into any of the above categories

## Key Findings

- Average vocabulary size: {avg_row['Total Tokens']:,.0f} tokens
- On average, {avg_row['Pure English (%)']:.2f}% of tokens are pure English
- {best_models['Pure English']} has the highest percentage of pure English tokens ({df['Pure English (%)'].max():.2f}%)
- {best_models['Complete Hangul']} has the highest percentage of complete Hangul tokens ({df['Complete Hangul (%)'].max():.2f}%)
- {best_models['Special Chars']} has the highest percentage of special character tokens ({df['Special Chars (%)'].max():.2f}%)

## Visualization Summary

Various visualizations were created to help understand the differences between tokenizers:

1. **Absolute Token Count Comparison**: Shows the raw counts of tokens in each category
2. **Percentage Distribution Chart**: Shows the relative distribution as percentages
3. **Stacked Percentage Chart**: Shows how each tokenizer's vocabulary is composed
4. **Radar Chart**: Provides a multi-dimensional view of category distributions

## Detailed Results

For detailed results, please refer to:
- The HTML table at `detailed_comparison_table.html`
- The CSV data at `tokenizer_comparison_data.csv`
- The individual JSON analysis files for each tokenizer

## Recommendations

Based on the analysis:

- For English language tasks, consider using {best_models['Pure English']} which has the highest proportion of English tokens
- For Korean language tasks, {best_models['Complete Hangul']} might offer better tokenization
- The high proportion of uncategorized tokens in some models ({best_models['Uncategorized']}: {df['Uncategorized (%)'].max():.2f}%) suggests potential for further investigation

"""
    
    # Save to file
    output_path = os.path.join(output_dir, 'tokenizer_analysis_summary.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Summary report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Tokenizer Analysis and Comparison Tool")
    
    parser.add_argument('--models', type=str, 
                        default='meta-llama/Llama-4-Maverick-17B-128E meta-llama/Llama-4-Scout-17B-16E'
                        ' deepseek-ai/DeepSeek-V3-0324 Qwen/QwQ-32B mistralai/Mistral-Small-3.1-24B-Base-2503 google/gemma-3-27b-it',
                        help="List of model IDs to analyze and compare")
    parser.add_argument('--output_dir', type=str, default="results/tokenizer_comparison_results",
                        help="Directory to save results and visualizations")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    models = args.models.split()
    print(f"Starting analysis of {len(models)} tokenizers...")
    
    # Run analysis for all models
    result_files = run_analysis_for_models(models, args.output_dir)
    
    # Load results
    results = load_analysis_results(result_files)
    
    # Create comparison DataFrame
    comparison_df = create_comparison_dataframe(results)
    
    # Print summary to console
    print("\n=== Tokenizer Comparison Summary ===")
    print(comparison_df.to_string())
    
    # Create visualizations
    print("\nGenerating comparison visualizations...")
    create_absolute_count_histogram(comparison_df, args.output_dir)
    create_percentage_histogram(comparison_df, args.output_dir)
    create_stacked_percentage_chart(comparison_df, args.output_dir)
    create_radar_chart(comparison_df, args.output_dir)
    
# Create detailed table
    print("\nGenerating detailed comparison table...")
    create_detailed_table(comparison_df, args.output_dir)
    
    # Generate summary report
    print("\nGenerating summary report...")
    generate_summary_report(comparison_df, args.output_dir)
    
    print(f"\nAnalysis complete! All results saved to: {os.path.abspath(args.output_dir)}")
    print(f"\nTo view the full comparison, open: {os.path.join(os.path.abspath(args.output_dir), 'detailed_comparison_table.html')}")


if __name__ == "__main__":
    main()

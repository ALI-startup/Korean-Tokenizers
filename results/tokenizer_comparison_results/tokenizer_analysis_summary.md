# Tokenizer Analysis Summary Report

## Overview

This report provides a comparison of token category distributions across 6 different tokenizers. The analysis categorizes tokens into several groups:

- **Pure English**: Tokens containing only English alphabetic characters
- **English Containing**: Tokens containing any English alphabetic characters
- **Pure Hangul**: Tokens containing only Korean Hangul characters
- **Hangul Containing**: Tokens containing any Korean Hangul characters 
- **Special Characters**: Tokens consisting only of special characters (non-alphanumeric)
- **Uncategorized**: Tokens that don't fit into any of the above categories

## Key Findings

- Average vocabulary size: 179,226 tokens
- On average, 54.33% of tokens are pure English
- Mistral-Small-3.1-24B-Base-2503 has the highest percentage of pure English tokens (57.62%)
- Mistral-Small-3.1-24B-Base-2503 has the highest percentage of pure Hangul tokens (3.36%)
- QwQ-32B has the highest percentage of special character tokens (4.15%)

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

- For English language tasks, consider using Mistral-Small-3.1-24B-Base-2503 which has the highest proportion of English tokens
- For Korean language tasks, Mistral-Small-3.1-24B-Base-2503 might offer better tokenization
- The high proportion of uncategorized tokens in some models (DeepSeek-V3-0324: 40.72%) suggests potential for further investigation


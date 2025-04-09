# Tokenizer Analysis Summary Report

## Overview

This report provides a comparison of token category distributions across 6 different tokenizers. The analysis categorizes tokens into several groups:

- **Pure English**: Tokens containing only English alphabetic characters
- **Hangul Possible**: Tokens that potentially contain Korean Hangul characters
- **Complete Hangul**: Tokens that definitely contain complete Korean Hangul characters
- **Special Characters**: Tokens consisting only of special characters (non-alphanumeric)
- **Uncategorized**: Tokens that don't fit into any of the above categories

## Key Findings

- Average vocabulary size: 179,226 tokens
- On average, 18.17% of tokens are pure English
- gemma-3-27b-it has the highest percentage of pure English tokens (20.26%)
- Mistral-Small-3.1-24B-Base-2503 has the highest percentage of complete Hangul tokens (3.43%)
- gemma-3-27b-it has the highest percentage of special character tokens (3.13%)

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

- For English language tasks, consider using gemma-3-27b-it which has the highest proportion of English tokens
- For Korean language tasks, Mistral-Small-3.1-24B-Base-2503 might offer better tokenization
- The high proportion of uncategorized tokens in some models (Mistral-Small-3.1-24B-Base-2503: 50.36%) suggests potential for further investigation


import transformers
import json
import argparse
import os
import unicodedata
from typing import Dict, List, Any, Tuple
from tqdm import tqdm

def is_hangul_char(char):
    """Check if a character is Hangul (Korean)"""
    # Hangul Unicode blocks:
    # Hangul Syllables: U+AC00-U+D7A3
    # Hangul Jamo: U+1100-U+11FF
    # Hangul Jamo Extended-A: U+A960-U+A97F
    # Hangul Jamo Extended-B: U+D7B0-U+D7FF
    code = ord(char)
    return (0xAC00 <= code <= 0xD7A3) or \
           (0x1100 <= code <= 0x11FF) or \
           (0xA960 <= code <= 0xA97F) or \
           (0xD7B0 <= code <= 0xD7FF)

def is_english_char(char):
    """Check if a character is English (Latin alphabet)"""
    # Basic Latin alphabet
    return ('a' <= char <= 'z') or ('A' <= char <= 'Z')

def is_special_char_token(token: str) -> bool:
    """Check if the token consists only of special characters."""
    return all(not (c.isalnum() or c.isspace()) for c in token)

def analyze_token_categories(model_id: str, min_token_id: int = 102) -> Dict[str, Any]:
    """Analyze tokens in each category for the tokenizer's entire vocabulary."""

    print(f"Analyzing tokens for model: {model_id}")
    # Load tokenizer
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
    vocab = tokenizer.get_vocab()

    max_token_id = len(vocab.values())

    # Token_id and string dictionaries for each category
    pure_english_tokens = {}
    english_containing_tokens = {}
    pure_hangul_tokens = {}
    hangul_containing_tokens = {}
    special_char_tokens = {}
    uncategorized_tokens = {}

    # Include only token IDs from min_token_id to max_token_id-1
    all_token_ids = {token_id for token_id in vocab.values() if min_token_id < token_id < max_token_id}
    all_tokens = {token_id: token for token, token_id in vocab.items() if min_token_id < token_id < max_token_id}

    print(f"Analyzing {len(all_token_ids)} tokens (ID > {min_token_id} and ID < {max_token_id})...")
    for token, token_id in tqdm(vocab.items()):
        # Skip tokens outside our range
        if token_id <= min_token_id or token_id >= max_token_id:
            continue

        try:
            # Get string representation of the token
            token_string = tokenizer.decode([token_id])
            
            # English analysis
            english_chars = sum(1 for c in token_string if is_english_char(c))
            if english_chars > 0:
                english_containing_tokens[token_id] = token_string
                if all(is_english_char(c) or c.isspace() or c.isdigit() or c in ".,;:!?-'\"()" for c in token_string):
                    pure_english_tokens[token_id] = token_string
            
            # Hangul analysis
            hangul_chars = sum(1 for c in token_string if is_hangul_char(c))
            if hangul_chars > 0:
                hangul_containing_tokens[token_id] = token_string
                if all(is_hangul_char(c) or c.isspace() or c.isdigit() or c in ".,;:!?-'\"()" for c in token_string):
                    pure_hangul_tokens[token_id] = token_string
            
            # Special character analysis
            if is_special_char_token(token_string):
                special_char_tokens[token_id] = token_string
                
        except Exception as e:
            print(f"Error analyzing token {token} (ID: {token_id}): {str(e)}")
            continue

    # Save tokens to JSON files
    save_token_categories(model_id, pure_english_tokens, english_containing_tokens, 
                         pure_hangul_tokens, hangul_containing_tokens, special_char_tokens)

    # Get all categorized token IDs
    pure_english_ids = set(pure_english_tokens.keys())
    english_containing_ids = set(english_containing_tokens.keys())
    pure_hangul_ids = set(pure_hangul_tokens.keys())
    hangul_containing_ids = set(hangul_containing_tokens.keys())
    special_char_ids = set(special_char_tokens.keys())

    # Token IDs in all categories
    categorized_ids = (pure_english_ids | english_containing_ids |
                       pure_hangul_ids | hangul_containing_ids |
                       special_char_ids)

    print(f"categorized_ids {len(categorized_ids)}")
    token_list = []
    for token_id in sorted(categorized_ids):
        token_list.append(str(token_id))
    print(f"len(token_list) {len(token_list)}")
    f = open("categorized_token_ids.txt", "wt")
    ids_string = ",".join(token_list)
    f.write(f"token_bias = [{ids_string}]")
    f.close()

    # Also save the token strings alongside the IDs
    f = open("categorized_tokens.json", "wt", encoding="utf-8")
    categorized_tokens = {}
    for token_id in sorted(categorized_ids):
        if token_id in all_tokens:
            token_string = tokenizer.decode([token_id])
            categorized_tokens[str(token_id)] = token_string
    json.dump(categorized_tokens, f, ensure_ascii=False, indent=2)
    f.close()

    # Token IDs that don't belong to any category
    uncategorized_ids = all_token_ids - categorized_ids
    for token_id in uncategorized_ids:
        if token_id in all_tokens:
            uncategorized_tokens[token_id] = tokenizer.decode([token_id])

    # Save uncategorized tokens
    save_uncategorized_tokens(model_id, uncategorized_tokens)

    return {
        'model_id': model_id,
        'max_token_id': max_token_id,
        'vocab_size': len(all_token_ids),
        'statistics': {
            'total_tokens': len(all_token_ids),
            'pure_english': len(pure_english_ids),
            'english_containing': len(english_containing_ids),
            'pure_hangul': len(pure_hangul_ids),
            'hangul_containing': len(hangul_containing_ids),
            'special_char': len(special_char_ids),
            'uncategorized': len(uncategorized_ids)
        },
        'token_ids': {
            'pure_english': sorted(list(pure_english_ids)),
            'english_containing': sorted(list(english_containing_ids)),
            'pure_hangul': sorted(list(pure_hangul_ids)),
            'hangul_containing': sorted(list(hangul_containing_ids)),
            'special_char': sorted(list(special_char_ids)),
            'uncategorized': sorted(list(uncategorized_ids))
        }
    }


def save_token_categories(model_id: str, pure_english: Dict[int, str], english_containing: Dict[int, str],
                         pure_hangul: Dict[int, str], hangul_containing: Dict[int, str], special_char: Dict[int, str]):
    """Save all token categories to separate JSON files."""
    # Create tokens directory if it doesn't exist
    tokens_dir = "tokens"
    if not os.path.exists(tokens_dir):
        os.makedirs(tokens_dir)
    
    # Extract model name from model_id for filename
    model_name = model_id.split('/')[-1] if '/' in model_id else model_id
    
    # Save each category
    categories = {
        "pure_english": pure_english,
        "english_containing": english_containing,
        "pure_hangul": pure_hangul,
        "hangul_containing": hangul_containing,
        "special_char": special_char
    }
    
    for category_name, tokens_dict in categories.items():
        # Convert dictionary keys to strings for JSON serialization
        tokens_str = {str(k): v for k, v in tokens_dict.items()}
        
        # Save to file
        category_file = os.path.join(tokens_dir, f"{model_name}_{category_name}.json")
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(tokens_str, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(tokens_dict)} {category_name} tokens to {category_file}")


def save_uncategorized_tokens(model_id: str, uncategorized: Dict[int, str]):
    """Save uncategorized tokens to a JSON file."""
    tokens_dir = "tokens"
    if not os.path.exists(tokens_dir):
        os.makedirs(tokens_dir)
    
    # Extract model name
    model_name = model_id.split('/')[-1] if '/' in model_id else model_id
    
    # Convert dictionary keys to strings
    tokens_str = {str(k): v for k, v in uncategorized.items()}
    
    # Save to file
    uncategorized_file = os.path.join(tokens_dir, f"{model_name}_uncategorized.json")
    with open(uncategorized_file, 'w', encoding='utf-8') as f:
        json.dump(tokens_str, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(uncategorized)} uncategorized tokens to {uncategorized_file}")
    
    # Also save as plain txt file with IDs
    print(f"uncategorized_ids {len(uncategorized)}")
    token_list = []
    for token_id in sorted(uncategorized.keys()):
        token_list.append(str(token_id))
    print(f"len(token_list) {len(token_list)}")
    f = open("uncategorized_token_ids.txt", "wt")
    ids_string = ",".join(token_list)
    f.write(f"token_bias = [{ids_string}]")
    f.close()


def print_uncategorized_tokens(model_id: str, token_data: Dict[int, str], max_tokens: int = 20):
    """Print uncategorized tokens."""
    print(f"\n=== Uncategorized Token Examples (max {max_tokens}) ===")
    for token_id in sorted(token_data.keys())[:max_tokens]:
        token = token_data[token_id]
        token_bytes = token.encode('utf-8')
        print(f"Token ID: {token_id:6d} | Token: {token:20s} | Bytes: {' '.join(hex(b) for b in token_bytes)}")


def save_analysis_results(analysis_result: Dict[str, Any], output_file: str = 'token_category_analysis.json'):
    """Save analysis results to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)


def print_analysis_summary(analysis_result: Dict[str, Any]):
    """Print key statistics of the analysis results."""
    stats = analysis_result['statistics']
    print(f"\n=== Tokenizer Category Analysis Results ===")
    print(f"Model: {analysis_result['model_id']}")
    print(f"Maximum Token ID analyzed: {analysis_result['max_token_id']}")
    print(f"Number of tokens analyzed: {stats['total_tokens']:,}")
    print(f"Pure English tokens: {stats['pure_english']:,}")
    print(f"Tokens containing English: {stats['english_containing']:,}")
    print(f"Pure Hangul tokens: {stats['pure_hangul']:,}")
    print(f"Tokens containing Hangul: {stats['hangul_containing']:,}")
    print(f"Special character tokens: {stats['special_char']:,}")
    print(f"Uncategorized tokens: {stats['uncategorized']:,}")


def token_analysis(model_id: str, output_file: str = 'token_category_analysis.json'):
    # Run complete analysis
    analysis_result = analyze_token_categories(model_id)

    # Save results
    save_analysis_results(analysis_result, output_file)

    # Print statistics
    print_analysis_summary(analysis_result)

    # Get tokenizer to decode uncategorized tokens
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
    uncategorized_tokens = {tid: tokenizer.decode([tid]) for tid in analysis_result['token_ids']['uncategorized']}
    
    # Print uncategorized tokens
    print_uncategorized_tokens(model_id, uncategorized_tokens)


def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description="LLaMA Token Editor - Language Model Tokenizer Analysis and Weight Adjustment Tool")

    parser.add_argument('--model_id', type=str, required=True,
                        help="Path or HuggingFace ID of the model to analyze")
    parser.add_argument('--min_token_id', type=int, default=102,
                        help="Minimum token ID to analyze (default: 102)")
    parser.add_argument('--output_file', type=str, default='token_category_analysis.json',
                        help="Path to save the JSON analysis results (default: token_category_analysis.json)")

    # Parse arguments
    args = parser.parse_args()

    # Run token analysis
    token_analysis(args.model_id, args.output_file)


if __name__ == "__main__":
    main()
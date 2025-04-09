# taken with respect from https://github.com/sionic-ai/Llama4-Token-Editor/blob/main/token_analyzer.py
import transformers
import json
import argparse
from typing import Dict, List, Any
from tqdm import tqdm

def can_be_hangul_utf8(byte_or_sequence):
    if isinstance(byte_or_sequence, int):
        # Check single byte
        return (0xEA <= byte_or_sequence <= 0xED) or (0x80 <= byte_or_sequence <= 0xBF)
    elif len(byte_or_sequence) == 1:
        # Check 1-byte sequence
        return can_be_hangul_utf8(byte_or_sequence[0])
    elif len(byte_or_sequence) == 2:
        # Check 2-byte sequence
        return (0x80 <= byte_or_sequence[0] <= 0xBF) and (0x80 <= byte_or_sequence[1] <= 0xBF)
    elif len(byte_or_sequence) >= 3:
        # Check sequence of 3 bytes or more
        return is_complete_hangul_utf8(byte_or_sequence[:3])
    else:
        return False


def is_complete_hangul_utf8(byte_sequence):
    if len(byte_sequence) != 3:
        return False

    first_byte, second_byte, third_byte = byte_sequence

    # Basic range check
    if not (0xEA <= first_byte <= 0xED):
        return False
    if not (0x80 <= second_byte <= 0xBF):
        return False
    if not (0x80 <= third_byte <= 0xBF):
        return False

    # Detailed range check
    if first_byte == 0xEA:
        return second_byte >= 0xB0
    elif first_byte == 0xED:
        return second_byte <= 0x9F

    return True


def is_special_char_token(token: str) -> bool:
    """Check if the token consists only of special characters."""
    return all(not (c.isalnum() or c.isspace()) for c in token)


def analyze_token_categories(model_id: str, min_token_id: int = 102) -> Dict[str, Any]:
    """Analyze tokens in each category for the tokenizer's entire vocabulary."""

    print(model_id)
    # Load tokenizer
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
    vocab = tokenizer.get_vocab()

    max_token_id = len(vocab.values())

    # Token_id sets for each category
    pure_english_ids = set()
    english_containing_ids = set()
    hangul_possible_ids = set()
    complete_hangul_ids = set()
    special_char_ids = set()

    # Include only token IDs from 102 to 128000-1
    all_token_ids = {token_id for token_id in vocab.values() if min_token_id < token_id < max_token_id}

    print(f"Analyzing tokens (ID <= {max_token_id})...")
    for token, token_id in tqdm(vocab.items()):
        # Skip tokens larger than max_token_id
        if token_id > max_token_id:
            continue

        try:
            # Get byte representation of the token
            token_bytes = tokenizer.decode([token_id]).encode('utf-8')

            # 1. Analyze English tokens
            english_bytes = sum(1 for b in token_bytes if (0x41 <= b <= 0x5A) or (0x61 <= b <= 0x7A))
            if english_bytes > 0:
                #english_containing_ids.add(token_id)
                if all((0x41 <= b <= 0x5A) or (0x61 <= b <= 0x7A) for b in token_bytes):
                    pure_english_ids.add(token_id)

            # 2. Analyze Korean
            # Check complete Hangul first
            for i in range(len(token_bytes) - 2):
                seq = token_bytes[i:i + 3]
                if len(seq) == 3 and is_complete_hangul_utf8(seq):
                    complete_hangul_ids.add(token_id)
                    break

            # Check possible Hangul
            for i in range(len(token_bytes)):
                remaining_sequence = token_bytes[i:]
                if can_be_hangul_utf8(remaining_sequence):
                    hangul_possible_ids.add(token_id)
                    break

            # 3. Check special character tokens
            if is_special_char_token(token):
                special_char_ids.add(token_id)

        except Exception as e:
            print(f"Error analyzing token {token} (ID: {token_id}): {str(e)}")
            continue

    # Token IDs in all categories
    categorized_ids = (pure_english_ids | english_containing_ids |
                       hangul_possible_ids | complete_hangul_ids |
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

    # Token IDs that don't belong to any category
    uncategorized_ids = all_token_ids - categorized_ids

    return {
        'model_id': model_id,
        'max_token_id': max_token_id,
        'vocab_size': len(all_token_ids),  # Number of tokens below max_token_id
        'statistics': {
            'total_tokens': len(all_token_ids),
            'pure_english': len(pure_english_ids),
            'english_containing': len(english_containing_ids),
            'hangul_possible': len(hangul_possible_ids),
            'complete_hangul': len(complete_hangul_ids),
            'special_char': len(special_char_ids),
            'uncategorized': len(uncategorized_ids)
        },
        'token_ids': {
            'pure_english': sorted(list(pure_english_ids)),
            'english_containing': sorted(list(english_containing_ids)),
            'hangul_possible': sorted(list(hangul_possible_ids)),
            'complete_hangul': sorted(list(complete_hangul_ids)),
            'special_char': sorted(list(special_char_ids)),
            'uncategorized': sorted(list(uncategorized_ids))
        }
    }


def print_uncategorized_tokens(model_id: str, token_ids: List[int], max_tokens: int = 20):
    """Print uncategorized tokens."""
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)

    print(f"uncategorized_ids {len(token_ids)}")
    token_list = []
    for token_id in sorted(token_ids):
        token_list.append(str(token_id))
    print(f"len(token_list) {len(token_list)}")
    f = open("uncategorized_token_ids.txt", "wt")
    ids_string = ",".join(token_list)
    f.write(f"token_bias = [{ids_string}]")
    f.close()

    print(f"\n=== Uncategorized Token Examples (max {max_tokens}) ===")
    for token_id in sorted(token_ids)[:max_tokens]:
        token = tokenizer.decode([token_id])
        token_bytes = tokenizer.decode([token_id]).encode('utf-8')
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
    #print(f"Tokens containing English: {stats['english_containing']:,}")
    print(f"Possible Hangul tokens: {stats['hangul_possible']:,}")
    print(f"Tokens with Complete Hangul: {stats['complete_hangul']:,}")
    print(f"Special character tokens: {stats['special_char']:,}")
    print(f"Uncategorized tokens: {stats['uncategorized']:,}")


def token_analysis(model_id: str, output_file: str = 'token_category_analysis.json'):
    # Run complete analysis
    analysis_result = analyze_token_categories(model_id)

    # Save results
    save_analysis_results(analysis_result, output_file)

    # Print statistics
    print_analysis_summary(analysis_result)

    # Print uncategorized tokens
    print_uncategorized_tokens(model_id, analysis_result['token_ids']['uncategorized'])


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
import os
import sys
import argparse
import pandas as pd
import json
from typing import List, Dict, Any
from transformers import AutoTokenizer
import matplotlib.pyplot as plt
import seaborn as sns
import codecs

def decode_utf8_garbage(token):
    try:
        return bytes(token, 'latin1').decode('utf-8')
    except:
        return token


def load_tokenizers(model_ids: List[str]) -> Dict[str, AutoTokenizer]:
    """
    Load tokenizers for the specified models.
    
    Args:
        model_ids: List of model IDs to load tokenizers for
        
    Returns:
        Dictionary mapping model names to tokenizer objects
    """
    tokenizers = {}
    
    for model_id in model_ids:
        model_name = model_id.split('/')[-1]
        print(f"Loading tokenizer for {model_id}...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            tokenizers[model_name] = tokenizer
            print(f"✓ Successfully loaded tokenizer for {model_name}")
        except Exception as e:
            print(f"✗ Failed to load tokenizer for {model_id}: {str(e)}")
    
    return tokenizers
    
from typing import Dict, List, Any
from transformers import AutoTokenizer

def tokenize_sentences(tokenizers: Dict[str, AutoTokenizer], sentences: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Tokenize each sentence with each tokenizer while attempting to output readable Korean tokens.

    This function uses offset mappings when available to extract the exact substrings from the original sentence.
    If offset mappings are not available or the result looks garbled, it falls back to re-encoding the tokens.

    Args:
        tokenizers: Dictionary mapping model names to tokenizer objects.
        sentences: List of sentences to tokenize.

    Returns:
        Dictionary mapping model names to lists of tokenization results.
        Each result includes:
          - 'sentence': original sentence
          - 'tokens': tokenizer tokens
          - 'token_ids': token IDs from the tokenizer
          - 'readable_tokens': human-friendly tokens (attempting to recover original substrings)
          - 'token_map': list of mappings for each token with token string, readable text, and token id
          - 'decoded_sentence': the full sentence decoded from token IDs (skips special tokens)
    """

    def fix_token_encoding(token: str) -> str:
        """
        If the token appears as garbled bytes (e.g. using byte-level BPE), try to re-encode it.
        """
        try:
            # Try encoding as Latin-1 and decode as UTF-8
            return token.encode('latin1').decode('utf-8')
        except Exception:
            return token

    tokenization_results = {}

    for model_name, tokenizer in tokenizers.items():
        print(f"\n--- Tokenizing with {model_name} ---")
        model_results = []

        for sentence in sentences:
            # Get encoding with offset mapping if available.
            encoding = tokenizer(sentence, return_offsets_mapping=True, add_special_tokens=True)
            token_ids = encoding["input_ids"]
            offsets = encoding.get("offset_mapping", None)
            tokens = tokenizer.convert_ids_to_tokens(token_ids)
            readable_tokens = []

            # Use offset mapping to extract original substrings if they exist.
            if offsets:
                for (start, end) in offsets:
                    # Some special tokens might have offset (0, 0)
                    if start == 0 and end == 0:
                        readable_tokens.append("")
                    else:
                        readable_tokens.append(sentence[start:end])
            
            # Fallback: decode individual tokens and try to clean them up
            if not offsets or any(rt == "" for rt in readable_tokens):
                # Attempt to convert tokens to string and fix encoding if needed
                readable_tokens = [tokenizer.convert_tokens_to_string([tok]).strip() for tok in tokens]
                readable_tokens = [fix_token_encoding(tok) for tok in readable_tokens]

            # Create token mapping (token, token id, recovered readable text)
            token_map = []
            for tok, tok_id, read_tok in zip(tokens, token_ids, readable_tokens):
                token_map.append({
                    "old_token": tok,
                    "token": read_tok,
                    "id": tok_id
                })

            # Full decoded sentence (skips special tokens)
            decoded_sentence = tokenizer.decode(token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)

            model_results.append({
                "sentence": sentence,
                "old_tokens": tokens,
                "token_ids": token_ids,
                "tokens": readable_tokens,
                "token_map": token_map,
                "decoded_sentence": decoded_sentence
            })

        tokenization_results[model_name] = model_results

    return tokenization_results


    return tokenization_results

def create_comparison_dataframe(tokenization_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, pd.DataFrame]:
    """
    Create comparison DataFrames for each sentence.
    
    Args:
        tokenization_results: Dictionary mapping model names to lists of tokenization results
        
    Returns:
        Dictionary mapping sentence indices to DataFrames with comparison data
    """
    dataframes = {}
    
    # Get all model names
    model_names = list(tokenization_results.keys())
    
    # Get the number of sentences
    num_sentences = len(tokenization_results[model_names[0]])
    
    for sentence_idx in range(num_sentences):
        sentence = tokenization_results[model_names[0]][sentence_idx]["sentence"]
        
        # Create a list to store rows for this sentence's comparison
        rows = []
        
        # Find the maximum number of tokens for this sentence across all models
        max_tokens = max(len(tokenization_results[model_name][sentence_idx]["token_map"]) 
                          for model_name in model_names)
        
        # Create a row for each token position
        for token_idx in range(max_tokens):
            row = {"Position": token_idx + 1}
            
            # Add token and ID for each model
            for model_name in model_names:
                token_map = tokenization_results[model_name][sentence_idx]["token_map"]
                
                if token_idx < len(token_map):
                    row[f"{model_name}_Token"] = token_map[token_idx]["token"]
                    row[f"{model_name}_ID"] = token_map[token_idx]["id"]
                else:
                    row[f"{model_name}_Token"] = ""
                    row[f"{model_name}_ID"] = ""
            
            rows.append(row)
        
        # Create DataFrame for this sentence
        df = pd.DataFrame(rows)
        dataframes[sentence_idx] = df
    
    return dataframes

def save_comparison_tables(dataframes: Dict[int, pd.DataFrame], 
                          sentences: List[str],
                          output_dir: str) -> None:
    """
    Save comparison tables as HTML and CSV files.
    
    Args:
        dataframes: Dictionary mapping sentence indices to DataFrames
        sentences: List of sentences
        output_dir: Directory to save the tables
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for sentence_idx, df in dataframes.items():
        sentence = sentences[sentence_idx]
        safe_sentence = sentence[:30].replace(' ', '_').replace('.', '').replace(',', '')
        
        # Save as CSV
        csv_path = os.path.join(output_dir, f"sentence_{sentence_idx+1}_{safe_sentence}_comparison.csv")
        df.to_csv(csv_path, index=False)
        
        # Save as styled HTML
        styled_df = df.style.set_caption(f"Tokenization Comparison for: \"{sentence}\"")
        html_path = os.path.join(output_dir, f"sentence_{sentence_idx+1}_{safe_sentence}_comparison.html")
        
        # Add CSS styling
        css = """
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }
            th, td {
                text-align: left;
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
            .token-cell {
                background-color: #e6f2ff;
            }
            .id-cell {
                background-color: #fff2e6;
            }
        </style>
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tokenization Comparison</title>
            {css}
        </head>
        <body>
            <h1>Tokenization Comparison</h1>
            <p>Sentence: "{sentence}"</p>
            {styled_df.to_html()}
        </body>
        </html>
        """
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"- Saved comparison for sentence {sentence_idx+1} to {html_path}")

def create_combined_report(dataframes: Dict[int, pd.DataFrame], 
                          sentences: List[str],
                          output_dir: str) -> None:
    """
    Create a combined HTML report with all sentences.
    
    Args:
        dataframes: Dictionary mapping sentence indices to DataFrames
        sentences: List of sentences
        output_dir: Directory to save the report
    """
    # Add CSS styling
    css = """
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #2980b9;
            margin-top: 30px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 30px;
        }
        th, td {
            text-align: left;
            padding: 8px;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .sentence-container {
            margin-bottom: 40px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        .sentence-text {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        .token-cell {
            background-color: #e6f2ff;
        }
        .id-cell {
            background-color: #fff2e6;
        }
    </style>
    """
    
    # Start building the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tokenizer Comparison Report</title>
        {css}
    </head>
    <body>
        <h1>Tokenizer Comparison Report</h1>
        <p>This report shows how different tokenizers process the same sentences.</p>
    """
    
    # Add each sentence and its comparison table
    for sentence_idx, df in dataframes.items():
        sentence = sentences[sentence_idx]
        
        html_content += f"""
        <div class="sentence-container">
            <div class="sentence-text">Sentence {sentence_idx+1}: "{sentence}"</div>
            {df.to_html(index=False)}
        </div>
        """
    
    # Close the HTML content
    html_content += """
    </body>
    </html>
    """
    
    # Save the combined report
    report_path = os.path.join(output_dir, "tokenizer_comparison_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nCombined report saved to: {report_path}")

def visualize_token_counts(tokenization_results: Dict[str, List[Dict[str, Any]]], 
                          sentences: List[str],
                          output_dir: str) -> None:
    """
    Create visualizations comparing token counts across tokenizers.
    
    Args:
        tokenization_results: Dictionary mapping model names to lists of tokenization results
        sentences: List of sentences
        output_dir: Directory to save the visualizations
    """
    # Extract token counts for each model and sentence
    model_names = list(tokenization_results.keys())
    token_counts = []
    
    for sentence_idx, sentence in enumerate(sentences):
        for model_name in model_names:
            token_count = len(tokenization_results[model_name][sentence_idx]["tokens"])
            token_counts.append({
                "Sentence": f"Sentence {sentence_idx+1}",
                "Model": model_name,
                "Token Count": token_count
            })
    
    # Create DataFrame for visualization
    df = pd.DataFrame(token_counts)
    
    # Create bar chart
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x='Sentence', y='Token Count', hue='Model', data=df)
    
    plt.title('Token Count Comparison by Model and Sentence', fontsize=16)
    plt.xlabel('Sentence', fontsize=14)
    plt.ylabel('Number of Tokens', fontsize=14)
    plt.legend(title='Model', title_fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Rotate x-axis labels if there are many sentences
    if len(sentences) > 5:
        plt.xticks(rotation=45, ha='right')
    
    # Add value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%d', fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    plot_path = os.path.join(output_dir, "token_count_comparison.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    print(f"Token count visualization saved to: {plot_path}")

def analyze_token_overlap(tokenization_results: Dict[str, List[Dict[str, Any]]],
                         sentences: List[str],
                         output_dir: str) -> None:
    """
    Analyze token overlap between different tokenizers.
    
    Args:
        tokenization_results: Dictionary mapping model names to lists of tokenization results
        sentences: List of sentences
        output_dir: Directory to save the analysis
    """
    model_names = list(tokenization_results.keys())
    num_models = len(model_names)
    
    # Skip if only one model
    if num_models <= 1:
        return
    
    # For each sentence, analyze token overlap
    for sentence_idx, sentence in enumerate(sentences):
        overlap_data = []
        
        # Compare each pair of models
        for i in range(num_models):
            model1 = model_names[i]
            tokens1 = set(tokenization_results[model1][sentence_idx]["tokens"])
            
            for j in range(i+1, num_models):
                model2 = model_names[j]
                tokens2 = set(tokenization_results[model2][sentence_idx]["tokens"])
                
                # Calculate intersection and unique tokens
                common_tokens = tokens1.intersection(tokens2)
                only_model1 = tokens1 - tokens2
                only_model2 = tokens2 - tokens1
                
                # Calculate Jaccard similarity
                jaccard = len(common_tokens) / len(tokens1.union(tokens2)) if tokens1 or tokens2 else 0
                
                overlap_data.append({
                    "Model 1": model1,
                    "Model 2": model2,
                    "Common Tokens": len(common_tokens),
                    "Unique to Model 1": len(only_model1),
                    "Unique to Model 2": len(only_model2),
                    "Jaccard Similarity": jaccard
                })
        
        # Create DataFrame
        overlap_df = pd.DataFrame(overlap_data)
        
        # Save as CSV
        csv_path = os.path.join(output_dir, f"sentence_{sentence_idx+1}_token_overlap.csv")
        overlap_df.to_csv(csv_path, index=False)
        
        print(f"- Token overlap analysis for sentence {sentence_idx+1} saved to {csv_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Tokenizer Comparison Tool for Sentences")
    
    parser.add_argument('--models', type=str, 
                        default='meta-llama/Llama-4-Maverick-17B-128E meta-llama/Llama-4-Scout-17B-16E'
                        ' deepseek-ai/DeepSeek-V3-0324 Qwen/QwQ-32B mistralai/Mistral-Small-3.1-24B-Base-2503 google/gemma-3-27b-it',
                        help="List of model IDs to analyze and compare")
        
    parser.add_argument(
        '--sentences',
        type=str,
        default=(
            'This is a test English sentence. |'
            '다양한 토크나이저가 어떻게 처리하는지 보고 싶습니다. |'
            '오늘은 날씨가 좋아서 산책하기 딱 좋아요. |'
            '하늘이 정말 맑고 기분이 상쾌하네요. |'
            '요즘 딥러닝 모델의 성능이 눈에 띄게 향상되고 있어요. |'
            '하지만 그만큼 학습에 필요한 자원도 많이 필요하죠. |'
            '저는 아침에 일어나자마자 커피를 마시는 습관이 있어요. |'
            '하루를 시작할 때 커피 향이 꼭 필요하거든요. |'
            '이 프로젝트는 처음부터 다시 계획을 세워야 할 것 같아요. |'
            '기존의 방식으로는 효율이 너무 떨어져요. |'
            '그 영화는 스토리도 좋았지만 배우들의 연기도 훌륭했어요. |'
            '특히 주인공의 감정 표현이 인상 깊었어요. |'
            '다음 주까지 보고서를 제출해야 한다는 걸 깜빡했어요. |'
            '지금부터라도 열심히 작성해야겠네요. |'
            '모든 조건을 만족하는 해를 찾는 건 쉽지 않은 일이에요. |'
            '수학적으로도 굉장히 복잡한 문제거든요. |'
            '회의 중에 갑자기 인터넷이 끊겨서 당황했어요. |'
            '다행히 금방 다시 연결됐지만 중요한 내용을 놓쳤죠. |'
            '친구들과 함께 떠난 여행은 정말 잊을 수 없는 추억이에요. |'
            '자연 속에서 보낸 시간이 마음을 편안하게 해줬어요.'
        ),
        help="Sentences to tokenize, separated by pipe character |"
    )
    
    parser.add_argument('--output_dir', type=str, default="results/tokenizer_sentence_comparison",
                        help="Directory to save results and visualizations")
    
    parser.add_argument('--file', type=str, 
                        help="Path to a text file containing sentences (one per line)")
    
    args = parser.parse_args()
    
    # Get sentences either from command line or file
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]
    else:
        sentences = args.sentences.split('|')
    
    # Strip whitespace from sentences
    sentences = [sentence.strip() for sentence in sentences]
    
    # Get models
    models = args.models.split()
    
    print(f"Starting tokenization analysis for {len(sentences)} sentences using {len(models)} tokenizers...")
    
    # Load tokenizers
    tokenizers = load_tokenizers(models)
    
    if not tokenizers:
        print("Error: No tokenizers were successfully loaded. Exiting.")
        return
    
    # Tokenize sentences
    tokenization_results = tokenize_sentences(tokenizers, sentences)
    
    # Create comparison DataFrames
    print("\nCreating comparison tables...")
    comparison_dfs = create_comparison_dataframe(tokenization_results)
    
    # Save comparison tables
    print("\nSaving comparison tables:")
    save_comparison_tables(comparison_dfs, sentences, args.output_dir)
    
    # Create combined report
    create_combined_report(comparison_dfs, sentences, args.output_dir)
    
    # Visualize token counts
    print("\nGenerating visualizations...")
    visualize_token_counts(tokenization_results, sentences, args.output_dir)
    
    # Analyze token overlap
    print("\nAnalyzing token overlap...")
    analyze_token_overlap(tokenization_results, sentences, args.output_dir)
    
    print(f"\nAnalysis complete! All results saved to: {os.path.abspath(args.output_dir)}")
    print(f"To view the full comparison report, open: {os.path.join(os.path.abspath(args.output_dir), 'tokenizer_comparison_report.html')}")

if __name__ == "__main__":
    main()
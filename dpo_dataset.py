from argparse import ArgumentParser
import threading
from datasets import load_dataset
from tqdm import tqdm
import random
import json
import os


def dpo_dataset_from_rs(rs_dataset, output_dir, index=0, pbar=None):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f"dpo_data_{index}.jsonl"), "w") as file:
        for sample in rs_dataset:
            if all(score == sample["scores"][0] for score in sample["scores"]):
                if pbar is not None:
                    pbar.update(1)
                continue
            
            messages = sample["messages"]
            conversation = messages[:-1]
            
            chosen = sample["top_responses"][0]

            # best vs random strategy
            best_score = sample["scores"][0]
            rejected_scores = [score for score in sample["scores"] if score != best_score]
            rejected_score = random.choice(rejected_scores)
            rejected_idx = sample["scores"].index(rejected_score)
            rejected = sample["top_responses"][rejected_idx]
        
            item = {
                "instruction": "",
                "input": "",
                "output": "",
                "conversation": conversation,
                "chosen": chosen,
                "rejected": rejected
            }

            file.write(json.dumps(item) + "\n")
            
            if pbar is not None:
                pbar.update(1)
            
            
def main(args):
    data_files = os.path.join(args.data, "*.jsonl")
    rs_dataset = load_dataset("json", data_files=data_files, split="train").to_list()
    
    pbar = tqdm(total=len(rs_dataset), position=1)
    
    threads = [
        threading.Thread(
            target=dpo_dataset_from_rs,
            args=(rs_dataset[i::args.nprocs], args.output, i, pbar)
        )
        for i in range(args.nprocs)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data", type=str)
    parser.add_argument("--output", type=str)
    parser.add_argument("--nprocs", type=int)
    
    args = parser.parse_args()
    
    main(args)
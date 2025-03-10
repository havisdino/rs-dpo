import os
import logging
import numpy as np
from datasets import load_dataset
import json
import threading
from argparse import ArgumentParser
from tqdm import tqdm
from time import sleep

import api
import api.gemini
import api.gpt
import api.dummy
from scoring_prompts_vi import create_scoring_prompt, parse_score


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S"
)


MODEL_NAME_CALLER_MAPPING = {
    "gpt-4o-std": api.gpt,
    "gpt-4o-mini-std": api.gpt,
    "o3-mini": api.gpt,
    "gemini-2.0-pro-exp-02-05": api.gemini,
    "gemini-2.0-flash": api.gemini,
    "gemini-2.0-flash-lite": api.gemini,
    "dummy": api.dummy,
}
        

def scoring_thread(index, model, timeout, output_dir, dataset, pbar=None):
    os.makedirs(output_dir, exist_ok=True)

    with (
        open(os.path.join(output_dir, f"rejection_sampled_{index}.jsonl"), "w") as rs_file,
        open(os.path.join(output_dir, f"failed_questions_{index}.jsonl"), "w") as fq_file
    ):
        for sample in dataset:
            messages = sample["messages"]
            responses = sample["output"]
            scores = []
            
            caller = MODEL_NAME_CALLER_MAPPING[model]
            for response in responses:
                max_tries = 5
                # Try 5 times
                for _ in range(max_tries):
                    try:
                        gpt_response = caller.get_completion(
                            prompt=create_scoring_prompt(messages, response),
                            model=model
                        )
                        scores.append(gpt_response)
                        break
                    
                    except Exception as e:
                        if "RESOURCE_EXHAUSTED" in repr(e):
                            logger.warning("Resource exhausted. The process will be sleeping in 60s")
                            sleep(60)
                        else:
                            raise e
                else:
                    logger.warning("Max tries exceeded. The current response will be skipped")
            
            scores = [parse_score(score) for score in scores]
            top_idxs = np.argsort(scores)[::-1]
            top_responses = [responses[i] for i in top_idxs]
            
            if all(score == 0 for score in scores):
                fq_file.write(json.dumps({"failed_id": sample["id"]}) + "\n")
                continue
            
            item = {
                "id": sample["id"],
                "type": sample["source"],
                "messages": messages,
                "top_responses": top_responses,
                "scores": sorted(scores)[::-1]
            }
            
            rs_file.write(json.dumps(item) + "\n")
            sleep(timeout)
            
            if pbar is not None:
                pbar.update(1)
    
    logger.info(f"[proc_{index}] Finished execution")
        

def main(args):
    data_files = os.path.join(args.data, "*.jsonl")
    dataset = load_dataset("json", data_files=data_files, split="train").to_list()
    
    pbar = tqdm(total=len(dataset), position=1)
    
    threads = [
        threading.Thread(
            target=scoring_thread,
            args=(i, args.model, args.timeout, args.output, dataset[i::args.nprocs], pbar)
        )
        for i in range(args.nprocs)
    ]
    
    for i, thread in enumerate(threads):
        thread.start()
        logger.info(f"Process {i} has started")
    
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data", type=str)
    parser.add_argument("--nprocs", type=int)
    parser.add_argument("--model", type=str)
    parser.add_argument("--timeout", type=float, default=0.5)
    parser.add_argument("--output", type=str, default="output_rs")
    
    args = parser.parse_args()
    
    main(args)
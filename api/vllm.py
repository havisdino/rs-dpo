from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.auto import tqdm
from openai import OpenAI


DEFAULT_MODEL = "Vi-Llama-3.3-70B-Instruct"
SERVER_HOST = "http://0.0.0.0:8148"
TEMPERATURE = 0.7
TOP_P = 0.9
MAX_TOKENS = 4096


def get_completion(
    input_prompt,
    num_responses,
    system_prompt=None,
    model=DEFAULT_MODEL,
    temperature=TEMPERATURE,
    top_p=TOP_P,
    max_tokens=MAX_TOKENS,
    server_host=SERVER_HOST,
):
    client = OpenAI(
        api_key="EMPTY",
        base_url=f"{server_host}/v1",
    )
    messages = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": input_prompt})
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            seed=0,
            top_p=top_p,
            temperature=temperature,
            max_tokens=max_tokens,
            n=num_responses
        )
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return None


def multi_thread_task_dict(task_dictionary, num_workers=1, show_progress=True):
    final_results = {}
    futures = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for id_, task in task_dictionary.items():
            futures.append(
                executor.submit(
                    lambda id_=id_, task=task: {"id": id_, "task_result": task()}
                )
            )

        if show_progress:
            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    final_results[result["id"]] = result["task_result"]
                    pbar.update(1)
        else:
            for future in as_completed(futures):
                result = future.result()
                final_results[result["id"]] = result["task_result"]

    return final_results
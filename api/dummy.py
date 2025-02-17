from random import randint


def get_completion(prompt, model):
    score = randint(0, 10)
    return f"<score>{score}</score>"
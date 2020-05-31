import numpy as np
import random


def train_test_split(data: dict, seed):
    train_set = {}
    test_set = {}
    for user, games in data.items():
        games = list(games.copy())
        random.Random(seed).shuffle(games)
        train = games[:int(0.8 * len(games))]
        test = games[int(0.8 * len(games)):]
        train_set[user] = set(train)
        test_set[user] = set(test)
    return train_set, test_set

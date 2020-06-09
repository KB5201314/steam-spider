#!/bin/python

import math
import os
import pickle
from collections import defaultdict

import numpy as np

import db
import train_and_test


# def cal_item_sim(train_set):
#     c = np.zeros((len(all_gameid), len(all_gameid)))
#     for user, games_ind in train_set.items():
#         print("user round {}".format(user))
#         games_ind_list = list(games_ind)
#         for gi in range(len(games_ind_list)):
#             indi = games_ind_list[gi]
#             c[indi, indi] += 1
#             for gj in range(gi + 1, len(games_ind_list)):
#                 indj = games_ind_list[gj]
#                 c[indi, indj] += 1
#                 c[indj, indi] += 1
#     w = np.zeros((len(all_gameid), len(all_gameid)))
#     for i in range(len(all_gameid)):
#         print("round {}".format(i))
#         for j in range(len(all_gameid)):
#             w[i, j] = (c[i, j] / math.sqrt(c[i, i] * c[j, j])) if c[i, i] != 0 and c[j, j] != 0 else 0
#     return w

def cal_item_sim(train_set, all_gameid):
    game_to_users = defaultdict(set)
    for user, games_ind in train_set.items():
        for g_ind in games_ind:
            game_to_users[g_ind].add(user)
    w = np.zeros((len(all_gameid), len(all_gameid)))
    for i in range(len(all_gameid)):
        print("round {}".format(i))
        w[i, i] = 1
        for j in range(i + 1, len(all_gameid)):
            w[i, j] = (len(game_to_users[i] & game_to_users[j]) / math.sqrt(
                len(game_to_users[i]) * len(game_to_users[j]))) if len(game_to_users[i]) != 0 and len(
                game_to_users[j]) != 0 else 0
    return w


def load_and_calculate_internal():
    db.init()
    all_owned_games = db.find_all_owned_games()

    data = {owned_games['_id']: set([g['appid'] for g in owned_games['games']] if 'games' in owned_games else []) for
            owned_games in all_owned_games}
    all_gameid = set()
    for games in data.values():
        all_gameid.update(games)
    all_gameid_list = list(all_gameid)
    gameid_to_ind = dict(zip(all_gameid_list, list(range(len(all_gameid)))))

    data = {user: set([gameid_to_ind[game_id] for game_id in game_ids]) for user, game_ids in data.items()}
    train_set, test_set = train_and_test.train_test_split(data, 144)
    w = cal_item_sim(train_set, all_gameid)

    return w, (train_set, test_set, gameid_to_ind)


def load_and_calculate():
    print("start cal_item_sim()")
    cache_file = 'out/item-based-cf.pickle'
    if not os.path.exists('./out'):
        os.makedirs('./out')
    try:
        with open(cache_file, 'rb') as f:
            result = pickle.load(f)
    except:
        print('[info] error load cache, rebuild it')
        result = load_and_calculate_internal()
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f, protocol=4)
    return result


w, (train_set, test_set, gameid_to_ind) = load_and_calculate()

K = 10
steamid = '76561199022440128'

user_to_games_ind = defaultdict(set)
for user, games_inds in train_set.items():
    user_to_games_ind[user].update(games_inds)
for user, games_inds in test_set.items():
    user_to_games_ind[user].update(games_inds)
game_ind_to_game_id = {v: k for k, v in gameid_to_ind.items()}

already_items = list(train_set[steamid])
scores = np.mean(w[already_items, :], axis=0)
scores_ind = np.argsort(-scores)
j = 0
for _ in range(K):
    while True:
        i = scores_ind[j]
        j += 1
        game_ind = i
        if not game_ind in user_to_games_ind[steamid]:  # print new games only
            print(
                "steamid({}) -> gameid({}) result({}) score({})".format(steamid,
                                                                        game_ind_to_game_id[game_ind],
                                                                        1,
                                                                        scores[i]))
            break

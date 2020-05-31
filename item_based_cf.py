#!/bin/python

import db
import train_and_test
from collections import defaultdict
import numpy as np
import math
import operator
import os
import pickle
import gc

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

if not os.path.exists('./out'):
    os.makedirs('./out')


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

def cal_item_sim(train_set):
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


def recommend(user, w, train_set, k):
    rank = defaultdict(int)
    already_items = train_set[user]
    score = np.zeros(w.shape[0], )
    for i in already_items:
        score += w[gameid_to_ind[i]]
    return sorted(score, key=operator.itemgetter(1), reverse=True)[:k][0]


# 物品间的相似性矩阵
print("start cal_item_sim()")
cache_file = 'out/item-based-cf-w.npy'
try:
    with open(cache_file, 'rb') as f:
        w = pickle.loads(f.read())
except:
    print('[info] error load cache, rebuild it')
    w = cal_item_sim(train_set)
    np.save(cache_file, w)

print("end cal_item_sim()")
print(recommend(data.keys()[0]))

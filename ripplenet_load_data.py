import os
import pickle
from collections import defaultdict
import random

import numpy as np
import py2neo


def get_incer():
    x = [-1]

    def inner():
        x[0] += 1
        return x[0]

    return inner


def load_kg_from_neo4j(args):
    # try to read from cache
    kg_file = './out/load_kg_from_neo4j_result.pickle'
    if os.path.exists(kg_file):
        return pickle.load(open(kg_file, 'rb'))
    else:
        result = load_kg_from_neo4j_internal(args)
        pickle.dump(result, open(kg_file, 'wb'))
        return result


def load_kg_from_neo4j_internal(args):
    print('[info] load_kg_from_neo4j() start')
    relation_type_to_ind = defaultdict(get_incer())
    user_to_ind = defaultdict(get_incer())
    notuser_to_ind = defaultdict(get_incer())

    graph = py2neo.Graph(password='Dynamic Synergized grey 65')

    # calculate train_data, eval_data, test_data, player_to_games
    print('[info] setp 1')
    owneds = graph.relationships.match(r_type='Owned')
    owned_np = np.array([[user_to_ind[r.start_node.identity], notuser_to_ind[r.end_node.identity], 1] for r in owneds])
    owned_np_pairs = set([(owned_np[own][0], owned_np[own][1]) for own in range(owned_np.shape[0])])
    users = list(set(owned_np[:, 0]))
    games = list(set(owned_np[:, 1]))
    print('[info] build negative data set')
    neg_user_game_pairs = set()
    for _ in range(len(owned_np)):
        while True:
            user_ind = random.choice(users)
            game_ind = random.choice(games)
            if (user_ind, game_ind) not in owned_np_pairs and (user_ind, game_ind) not in neg_user_game_pairs:
                neg_user_game_pairs.add((user_ind, game_ind))
                break
    neg_owned_np = np.array([[n[0], n[1], 0] for n in neg_user_game_pairs])
    owned_np = np.vstack((owned_np, neg_owned_np))
    print('[info] shuffle')
    np.random.shuffle(owned_np)
    train_data, eval_data, test_data, player_to_games = dataset_split(owned_np)

    # calculate n_entity, n_relation, kg_dic
    print('[info] setp 2')
    kg_np = np.empty((0, 3))
    relations = graph.relationships.match(r_type='Developed By')
    kg_np = np.vstack((kg_np, np.array(
        [[notuser_to_ind[r.start_node.identity], relation_type_to_ind['Developed By'],
          notuser_to_ind[r.end_node.identity]] for r in relations])))
    relations = graph.relationships.match(r_type='Published By')
    kg_np = np.vstack((kg_np, np.array(
        [[notuser_to_ind[r.start_node.identity], relation_type_to_ind['Published By'],
          notuser_to_ind[r.end_node.identity]] for r in relations])))
    relations = graph.relationships.match(r_type='Marked As')
    kg_np = np.vstack((kg_np, np.array(
        [[notuser_to_ind[r.start_node.identity], relation_type_to_ind['Marked As'], notuser_to_ind[r.end_node.identity]]
         for r in relations])))
    # n_entity = len(set(kg_np[:, 0]) | set(kg_np[:, 2]))
    n_entity = len(notuser_to_ind)
    n_relation = len(set(kg_np[:, 1]))
    kg_dic = construct_kg(kg_np)

    # calculate ripple_set
    print('[info] setp 3')
    ripple_set = get_ripple_set(kg_dic, player_to_games, args.n_hop, args.n_memory)

    return train_data, eval_data, test_data, n_entity, n_relation, ripple_set


def dataset_split(rating_np):
    print('splitting dataset ...')

    # train:eval:test = 6:2:2
    eval_ratio = 0.2
    test_ratio = 0.2
    n_ratings = rating_np.shape[0]

    eval_indices = np.random.choice(n_ratings, size=int(n_ratings * eval_ratio), replace=False)
    left = set(range(n_ratings)) - set(eval_indices)
    test_indices = np.random.choice(list(left), size=int(n_ratings * test_ratio), replace=False)
    train_indices = list(left - set(test_indices))
    # print(len(train_indices), len(eval_indices), len(test_indices))

    # traverse training data, only keeping the users with positive ratings
    user_history_dict = defaultdict(list)
    for i in train_indices:
        user = rating_np[i][0]
        item = rating_np[i][1]
        owned = rating_np[i][2]
        if owned == 1:
            user_history_dict[user].append(item)

    train_indices = [i for i in train_indices if rating_np[i][0] in user_history_dict]
    eval_indices = [i for i in eval_indices if rating_np[i][0] in user_history_dict]
    test_indices = [i for i in test_indices if rating_np[i][0] in user_history_dict]
    # print(len(train_indices), len(eval_indices), len(test_indices))

    train_data = rating_np[train_indices]
    eval_data = rating_np[eval_indices]
    test_data = rating_np[test_indices]

    return train_data, eval_data, test_data, user_history_dict


def construct_kg(kg_np):
    print('constructing knowledge graph ...')
    kg = defaultdict(list)
    for head, relation, tail in kg_np:
        kg[head].append((tail, relation))
    return kg


def get_ripple_set(kg, user_history_dict, n_hop, n_memory):
    print('constructing ripple set ...')

    # user -> [(hop_0_heads, hop_0_relations, hop_0_tails), (hop_1_heads, hop_1_relations, hop_1_tails), ...]
    ripple_set = defaultdict(list)

    for user in user_history_dict:
        for h in range(n_hop):
            memories_h = []
            memories_r = []
            memories_t = []

            if h == 0:
                tails_of_last_hop = user_history_dict[user]
            else:
                tails_of_last_hop = ripple_set[user][-1][2]

            for entity in tails_of_last_hop:
                for tail_and_relation in kg[entity]:
                    memories_h.append(entity)
                    memories_r.append(tail_and_relation[1])
                    memories_t.append(tail_and_relation[0])

            # if the current ripple set of the given user is empty, we simply copy the ripple set of the last hop here
            # this won't happen for h = 0, because only the items that appear in the KG have been selected
            # this only happens on 154 users in Book-Crossing dataset (since both BX dataset and the KG are sparse)
            if len(memories_h) == 0:
                ripple_set[user].append(ripple_set[user][-1])
            else:
                # sample a fixed-size 1-hop memory for each user
                replace = len(memories_h) < n_memory
                indices = np.random.choice(len(memories_h), size=n_memory, replace=replace)
                memories_h = [memories_h[i] for i in indices]
                memories_r = [memories_r[i] for i in indices]
                memories_t = [memories_t[i] for i in indices]
                ripple_set[user].append((memories_h, memories_r, memories_t))

    return ripple_set

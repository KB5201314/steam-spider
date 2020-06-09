import itertools
import pickle

import numpy as np
import tensorflow as tf
from collections import defaultdict

# try to read from cache
kg_file = './out/load_kg_from_neo4j_result.pickle'
data_info = pickle.load(open(kg_file, 'rb'))
train_data = data_info[0]
eval_data = data_info[1]
test_data = data_info[2]
n_entity = data_info[3]
n_relation = data_info[4]
ripple_set = data_info[5]
n_games, relation_type_to_ind, user_to_ind, notuser_to_ind = data_info[6]

ind_to_notuser = {v: k for k, v in notuser_to_ind.items()}
ind_to_user = {v: k for k, v in user_to_ind.items()}

user_ind_to_games_ind = defaultdict(set)
for d in np.vstack((train_data, eval_data, test_data)):
    if d[2] == 1:
        user_ind_to_games_ind[d[0]].add(d[1])

K = 10
n_hop = 2

steamid = '76561199022440128'
eval_data = np.array(list(itertools.product([user_to_ind[steamid]], list(notuser_to_ind.values())[:n_games])))

with tf.Session() as sess:
    saver = tf.train.import_meta_graph('./out/ripplenet_model.meta')
    saver.restore(sess, tf.train.latest_checkpoint('./out/'))
    graph = tf.get_default_graph()
    model_items = graph.get_operation_by_name('items').outputs[0]

    feed_dict = dict()
    feed_dict[model_items] = eval_data[:, 1]
    for i in range(n_hop):
        feed_dict[graph.get_operation_by_name('memories_h_' + str(i)).outputs[0]] = [ripple_set[user][i][0] for user in
                                                                                     eval_data[:, 0]]
        feed_dict[graph.get_operation_by_name('memories_r_' + str(i)).outputs[0]] = [ripple_set[user][i][1] for user in
                                                                                     eval_data[:, 0]]
        feed_dict[graph.get_operation_by_name('memories_t_' + str(i)).outputs[0]] = [ripple_set[user][i][2] for user in
                                                                                     eval_data[:, 0]]
    scores_normalized = graph.get_operation_by_name('scores_normalized').outputs[0]
    (scores,) = sess.run([scores_normalized], feed_dict=feed_dict)
    predictions = [1 if i >= 0.5 else 0 for i in scores.tolist()]
    scores_ind = np.argsort(-scores)
    j = 0
    for _ in range(K):
        while True:
            i = scores_ind[j]
            j += 1
            user_ind = eval_data[i][0]
            geme_ind = eval_data[i][1]
            if not geme_ind in user_ind_to_games_ind[user_ind]:  # print new games only
                print(
                    "steamid({}) -> gameid({}) result({}) score({})".format(ind_to_user[eval_data[i][0]],
                                                                            ind_to_notuser[eval_data[i][1]],
                                                                            predictions[i],
                                                                            scores[i]))
                break

import argparse
import ripplenet_load_data
import ripplenet_train
import numpy as np

# just use the implements in this repository
# https://github.com/hwwang55/RippleNet

parser = argparse.ArgumentParser()
parser.add_argument('--dim', type=int, default=16,
                    help='dimension of entity and relation embeddings')
parser.add_argument('--n_hop', type=int, default=2, help='maximum hops')
parser.add_argument('--kge_weight', type=float,
                    default=0.01, help='weight of the KGE term')
parser.add_argument('--l2_weight', type=float, default=1e-7,
                    help='weight of the l2 regularization term')
parser.add_argument('--lr', type=float, default=0.010, help='learning rate')
parser.add_argument('--batch_size', type=int, default=1024, help='batch size')
parser.add_argument('--n_epoch', type=int, default=2,
                    help='the number of epochs')
parser.add_argument('--n_memory', type=int, default=32,
                    help='size of ripple set for each hop')
parser.add_argument('--item_update_mode', type=str, default='plus_transform',
                    help='how to update item at the end of each hop')
parser.add_argument('--using_all_hops', type=bool, default=True,
                    help='whether using outputs of all hops or just the last hop when making prediction')

args = parser.parse_args()

np.random.seed(144)

# python ./ripplenet.py --n_epoch 2
show_loss = True
data_info = ripplenet_load_data.load_kg_from_neo4j(args)
ripplenet_train.train(args, data_info, show_loss)

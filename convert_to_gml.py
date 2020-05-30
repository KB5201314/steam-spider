#!/bin/python

import networkx as nx
import db

db.init()

G = nx.Graph()

steamids = set(db.find_all_steamid())
friend_lists = db.find_all_friend_list()
G.add_nodes_from(steamids)
for friend_list in friend_lists:
    u = friend_list['_id']
    for friend in friend_list['friends']:
        v = friend['steamid']
        if v in steamids:
            G.add_edge(u, v)
nx.write_gml(G, './out/network.gml')

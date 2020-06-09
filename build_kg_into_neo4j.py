import db
import py2neo
from py2neo.cypher import cypher_escape

# read data
db.init()
all_player_summaries = db.find_all_player_summaries()
all_owned_games = db.find_all_owned_games()
all_app_details = db.find_all_app_details()

# init
graph = py2neo.Graph(password='Dynamic Synergized grey 65')


def init_constraint():
    try:
        graph.run("CREATE CONSTRAINT ON (p:Player) ASSERT p.steamid IS UNIQUE;")
        graph.run("CREATE CONSTRAINT ON (g:Game) ASSERT g.appid IS UNIQUE;")
        graph.run("CREATE CONSTRAINT ON (d:Developer) ASSERT d.name IS UNIQUE;")
        graph.run("CREATE CONSTRAINT ON (p:Publisher) ASSERT p.name IS UNIQUE;")
        graph.run("CREATE CONSTRAINT ON (g:Genre) ASSERT g.value IS UNIQUE;")
    except:
        pass


def insert_node():
    # Player
    players = [{'steamid': p['_id'], 'personaname': p['personaname']} for p in all_player_summaries]
    for r in players:
        n = py2neo.Node('Player')
        n.update(r)
        graph.create(n)
    # Game
    games = set()
    for owned_games in all_owned_games:
        if 'games' in owned_games:
            games.update([(g['appid'], g['name']) for g in owned_games['games']])
    for r in games:
        n = py2neo.Node('Game')
        n.update({'appid': r[0], 'name': r[1]})
        graph.create(n)
    # Developer
    devs = set()
    for r in all_app_details:
        if 'data' in r and 'developers' in r['data']:
            devs.update(r['data']['developers'])
    devs -= {''}
    for r in devs:
        n = py2neo.Node('Developer')
        n['name'] = r
        graph.create(n)
    # Publisher
    pubs = set()
    for r in all_app_details:
        if 'data' in r and 'publishers' in r['data']:
            pubs.update(r['data']['publishers'])
    pubs -= {''}
    for r in pubs:
        n = py2neo.Node('Publisher')
        n['name'] = r
        graph.create(n)
    # Genre
    genres = set()
    for r in all_app_details:
        if 'data' in r and 'genres' in r['data']:
            genres.update(map(lambda x: x['description'], r['data']['genres']))
    genres -= {''}
    for r in genres:
        n = py2neo.Node('Genre')
        n['value'] = r
        graph.create(n)


def insert_relation():
    # Owns
    cypher = '''
        MATCH (a:Player{{steamid:'{}'}}),(b:Game{{appid:{}}})
        CREATE r=(a)-[:Owned]->(b)
    '''
    for owned_games in all_owned_games:
        if 'games' in owned_games:
            for g in owned_games['games']:
                graph.run(cypher.format(owned_games['_id'], g['appid']))
    # Games links
    dev_cypher = '''
        MATCH (a:Game{appid:$appid}),(b:Developer{name: $name})
        CREATE r=(a)-[:`Developed By`]->(b)
    '''
    pub_cypher = '''
        MATCH (a:Game{appid:$appid}),(b:Publisher{name: $name})
        CREATE r=(a)-[:`Published By`]->(b)
    '''
    marked_cypher = '''
        MATCH (a:Game{appid:$appid}),(b:Genre{value: $value})
        CREATE r=(a)-[:`Marked As`]->(b)
    '''
    for game in all_app_details:
        if 'data' in game:
            if 'developers' in game['data']:
                for dev_name in game['data']['developers']:
                    graph.run(dev_cypher, appid=game['_id'], name=dev_name)
            if 'publishers' in game['data']:
                for pub_name in game['data']['publishers']:
                    graph.run(pub_cypher, appid=game['_id'], name=pub_name)
            if 'genres' in game['data']:
                for genre in game['data']['genres']:
                    graph.run(marked_cypher, appid=game['_id'], value=genre['description'])

import db
import py2neo

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
        n['name'] = r
        graph.create(n)


def insert_relation():
    matcher = py2neo.NodeMatcher(graph)
    # Owns
    for owned_games in all_owned_games:
        user_node = py2neo.Node('Player', steamid=owned_games['_id'])
        graph.merge(user_node, 'Player', 'steamid')
        if 'games' in owned_games:
            for g in owned_games['games']:
                game_node = py2neo.Node('Game', appid=g['appid'])
                graph.merge(game_node, 'Game', 'appid')
                relation = py2neo.Relationship(user_node, 'Owned', game_node)
                graph.create(relation)
    # Games links
    for game in all_app_details:
        if 'data' in game:
            game_node = py2neo.Node('Game', appid=game['_id'])
            graph.merge(game_node, 'Game', 'appid')
            if 'developers' in game['data']:
                for dev_name in game['data']['developers']:
                    dev_node = py2neo.Node('Developer', name=dev_name)
                    graph.merge(dev_node, 'Developer', 'name')
                    graph.create(py2neo.Relationship(game_node, 'Developed By', dev_node))
            if 'publishers' in game['data']:
                for pub_name in game['data']['publishers']:
                    pub_node = py2neo.Node('Publisher', name=pub_name)
                    graph.merge(pub_node, 'Publisher', 'name')
                    graph.create(py2neo.Relationship(game_node, 'Published By', pub_node))
            if 'genres' in game['data']:
                for genre in game['data']['genres']:
                    genre_node = py2neo.Node('Genre', value=genre['description'])
                    graph.merge(genre_node, 'Genre', 'value')
                    graph.create(py2neo.Relationship(game_node, 'Marked As', genre_node))

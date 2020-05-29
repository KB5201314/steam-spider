from pymongo import MongoClient


def init():
    global connect
    connect = MongoClient()
    global steamdb
    steamdb = connect['steam_user_net']


def insert_friend_list(steamid, data):
    data['_id'] = steamid
    steamdb['friend_list'].replace_one({'_id': steamid}, data, upsert=True)


def insert_player_summaries(steamid, data):
    data['_id'] = steamid
    steamdb['player_summaries'].replace_one({'_id': steamid}, data, upsert=True)


def insert_owned_games(steamid, data):
    data['_id'] = steamid
    steamdb['owned_games'].replace_one({'_id': steamid}, data, upsert=True)


def insert_recently_played_games(steamid, data):
    data['_id'] = steamid
    steamdb['recently_played_games'].replace_one({'_id': steamid}, data, upsert=True)


def insert_app_details(appid, data):
    data['_id'] = appid
    steamdb['app_details'].replace_one({'_id': appid}, data, upsert=True)


def find_all_friend_list():
    return steamdb['friend_list'].find()


def find_all_player_summaries():
    return steamdb['player_summaries'].find()


def find_all_owned_games():
    return steamdb['owned_games'].find()


def find_all_recently_played_games():
    return steamdb['recently_played_games'].find()


def find_all_app_details():
    return steamdb['app_details'].find()

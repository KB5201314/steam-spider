from steampy.client import SteamClient
import requests


def init(init_api_key):
    global steam_client
    global api_key
    api_key = init_api_key
    steam_client = SteamClient(api_key)


def get_friend_list(steamid):
    resp = steam_client.api_call(
        'GET', 'ISteamUser', 'GetFriendList', 'v1',
        {'key': api_key, 'steamid': steamid, 'relationship': 'friend'}).json()
    if resp != {}:
        return resp['friendslist']
    else:
        return {'friends': []}


def get_player_summaries(steamid):
    resp = steam_client.api_call(
        'GET', 'ISteamUser', 'GetPlayerSummaries', 'v2', {'key': api_key, 'steamids': steamid}).json()
    return resp['response']['players'][0]


def get_owned_games(steamid):
    resp = steam_client.api_call(
        'GET', 'IPlayerService', 'GetOwnedGames', 'v1',
        {'key': api_key, 'steamid': steamid, 'include_appinfo': 1, 'include_played_free_games': 1,
         'include_free_sub': 1}).json()
    return resp['response']


def get_recently_played_games(steamid):
    resp = steam_client.api_call(
        'GET', 'IPlayerService', 'GetRecentlyPlayedGames', 'v1', {'key': api_key, 'steamid': steamid}).json()
    return resp['response']


def get_app_details(appid):
    url = 'https://store.steampowered.com/api/appdetails?appids={}&l=english'.format(appid)
    response = requests.get(url)
    resp = response.json()
    return resp[list(resp.keys())[0]]

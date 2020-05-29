#!/bin/python3

import json
import time

import db
import steamapi
import task
import signal
import threading


def test_modules():
    print("[info] steamapi.get_friend_list(): {}".format(steamapi.get_friend_list('76561199022440128')))
    print("[info] steamapi.get_player_summaries(): {}".format(steamapi.get_player_summaries('76561199022440128')))
    print("[info] steamapi.get_owned_games(): {}".format(steamapi.get_owned_games('76561199022440128')))
    print("[info] steamapi.get_recently_played_games(): {}".format(
        steamapi.get_recently_played_games('76561199022440128')))
    print("[info] steamapi.get_app_details(): {}".format(steamapi.get_app_details('49520')))

    print("[info] db.insert_friend_list(): {}".format(
        db.insert_friend_list('76561199022440128', steamapi.get_friend_list('76561199022440128'))))
    print("[info] db.insert_player_summaries(): {}".format(
        db.insert_player_summaries('76561199022440128', steamapi.get_player_summaries('76561199022440128'))))
    print("[info] db.insert_owned_games(): {}".format(
        db.insert_owned_games('76561199022440128', steamapi.get_owned_games('76561199022440128'))))
    print("[info] db.insert_recently_played_games(): {}".format(
        db.insert_recently_played_games('76561199022440128', steamapi.get_recently_played_games('76561199022440128'))))
    print(
        "[info] db.insert_app_details(): {}".format(db.insert_app_details('49520', steamapi.get_app_details('49520'))))


with open('config.json') as f:
    config = json.load(f)

print("[info] your config: {}".format(config))


def signal_handler(sig, frame):
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    print('[info] waiting for tasks to exit')
    task.set_program_exit(True)
    global program_exit
    program_exit = True
    task.wait_finish()


steamapi.init(config['api_key'])
db.init()
task.init(20)
program_exit = False

# test_modules()
signal.signal(signal.SIGINT, signal_handler)

print('[info] load_finished_tasks_from_db()')
task.load_finished_tasks_from_db()
task.schedule_user_as_unfinished_tasks('76561199022440128')
task.print_current_info()
print('[info] schedule_all_unfinished_tasks() start')
task.schedule_all_unfinished_tasks()
print('[info] schedule_all_unfinished_tasks() end')


def print_info_interval():
    while True:
        time.sleep(5)
        task.print_current_info()


info_thread = threading.Thread(target=print_info_interval)
info_thread.start()
info_thread.join()

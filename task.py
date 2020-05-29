import time
from enum import Enum, auto
import threading
import redis
from concurrent.futures import ThreadPoolExecutor
import steamapi
import db
import pickle
import traceback


class TaskType(Enum):
    TASK_GET_FRIEND_LIST = auto()
    TASK_GET_PLAYER_SUMMARIES = auto()
    TASK_GET_OWNED_GAMES = auto()
    TASK_GET_RECENTLY_PLAYED_GAMES = auto()
    TASK_GET_APP_DETAILS = auto()


class Task:
    def __init__(self, type: TaskType, paramter: dict):
        self.type = type
        self.paramter = paramter

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Task):
            return NotImplemented
        return self.type == o.type and self.paramter == o.paramter

    def __hash__(self) -> int:
        return hash(pickle.dumps(self))


tasks_rw_lock = threading.RLock()
KEY_UNFINISHED_TASKS = "steam-user-net-unfinished-tasks"
KEY_FINISHED_TASKS = "steam-user-net-finished-tasks"
program_exit = False


def init(pool_size):
    global executor
    executor = ThreadPoolExecutor(pool_size)
    global redis_client
    redis_client = redis.Redis()


last_count_finished = 0
last_count_finished_time = 0


def print_current_info():
    global last_count_finished
    global last_count_finished_time
    print(('-' * 20) + ' tasks info ' + ('-' * 20))
    count_finished = redis_client.scard(KEY_FINISHED_TASKS)
    count_finished_time = int(time.time())
    print("[info] finished tasks: {} speed: {}/s".format(count_finished, (count_finished - last_count_finished) / (
            count_finished_time - last_count_finished_time)))
    last_count_finished = count_finished
    last_count_finished_time = count_finished_time
    print("[info] unfinished tasks: {}".format(redis_client.scard(KEY_UNFINISHED_TASKS)))
    print('-' * 50)


def schedule_user_as_unfinished_tasks(steamid):
    redis_client.sadd(KEY_UNFINISHED_TASKS, pickle.dumps(Task(TaskType.TASK_GET_FRIEND_LIST, {'steamid': steamid})))


def schedule_all_unfinished_tasks():
    for task in redis_client.smembers(KEY_UNFINISHED_TASKS):
        task = pickle.loads(task)
        executor.submit(runner, task)


def load_finished_tasks_from_db():
    redis_client.delete(KEY_FINISHED_TASKS)
    redis_client.sadd(KEY_FINISHED_TASKS, *set(
        [pickle.dumps(Task(TaskType.TASK_GET_FRIEND_LIST, {'steamid': record['_id']})) for record in
         db.find_all_friend_list()]))
    redis_client.sadd(KEY_FINISHED_TASKS, *set(
        [pickle.dumps(Task(TaskType.TASK_GET_PLAYER_SUMMARIES, {'steamid': record['_id']})) for record in
         db.find_all_player_summaries()]))
    redis_client.sadd(KEY_FINISHED_TASKS, *set(
        [pickle.dumps(Task(TaskType.TASK_GET_OWNED_GAMES, {'steamid': record['_id']})) for record in
         db.find_all_owned_games()]))
    redis_client.sadd(KEY_FINISHED_TASKS,
                      *set([pickle.dumps(Task(TaskType.TASK_GET_RECENTLY_PLAYED_GAMES, {'steamid': record['_id']})) for
                            record in
                            db.find_all_recently_played_games()]))
    redis_client.sadd(KEY_FINISHED_TASKS, *set(
        [pickle.dumps(Task(TaskType.TASK_GET_APP_DETAILS, {'appid': record['_id']})) for record in
         db.find_all_app_details()]))


def set_program_exit(status):
    global program_exit
    program_exit = status


def wait_finish():
    executor.shutdown(wait=True)


def add_task(task: Task):
    with tasks_rw_lock:
        redis_client.sadd(KEY_UNFINISHED_TASKS, pickle.dumps(task))
        executor.submit(runner, task)


def add_task_if_needed(task: Task):
    with tasks_rw_lock:
        if redis_client.sismember(KEY_UNFINISHED_TASKS, pickle.dumps(task)):
            return
        if redis_client.sismember(KEY_FINISHED_TASKS, pickle.dumps(task)):
            return
        add_task(task)


def finish_task(task: Task):
    with tasks_rw_lock:
        redis_client.smove(KEY_UNFINISHED_TASKS, KEY_FINISHED_TASKS, pickle.dumps(task))


def runner(task: Task):
    try:
        if task.type == TaskType.TASK_GET_FRIEND_LIST:
            friend_list = steamapi.get_friend_list(task.paramter['steamid'])
            db.insert_friend_list(task.paramter['steamid'], friend_list)
            for friend in friend_list['friends']:
                add_task_if_needed(Task(TaskType.TASK_GET_FRIEND_LIST, {'steamid': friend['steamid']}))
                add_task_if_needed(Task(TaskType.TASK_GET_PLAYER_SUMMARIES, {'steamid': friend['steamid']}))
                add_task_if_needed(Task(TaskType.TASK_GET_OWNED_GAMES, {'steamid': friend['steamid']}))
                add_task_if_needed(Task(TaskType.TASK_GET_RECENTLY_PLAYED_GAMES, {'steamid': friend['steamid']}))

        elif task.type == TaskType.TASK_GET_PLAYER_SUMMARIES:
            db.insert_player_summaries(task.paramter['steamid'],
                                       steamapi.get_player_summaries(task.paramter['steamid']))

        elif task.type == TaskType.TASK_GET_OWNED_GAMES:
            owned_games = steamapi.get_owned_games(task.paramter['steamid'])
            db.insert_owned_games(task.paramter['steamid'], owned_games)
            if 'games' in owned_games:
                for game in owned_games['games']:
                    add_task_if_needed(Task(TaskType.TASK_GET_APP_DETAILS, {'appid': game['appid']}))

        elif task.type == TaskType.TASK_GET_RECENTLY_PLAYED_GAMES:
            played_games = steamapi.get_recently_played_games(task.paramter['steamid'])
            db.insert_recently_played_games(task.paramter['steamid'], played_games)
            if 'games' in played_games:
                for game in played_games['games']:
                    add_task_if_needed(Task(TaskType.TASK_GET_APP_DETAILS, {'appid': game['appid']}))

        elif task.type == TaskType.TASK_GET_APP_DETAILS:
            db.insert_app_details(task.paramter['appid'], steamapi.get_app_details(task.paramter['appid']))

        finish_task(task)
    except Exception as e:
        traceback.print_exc()

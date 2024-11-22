



import discord
from discord.ext import commands, tasks
import asyncio
import subprocess
import mcrcon
import re
import time
import shutil
import os
import asyncio

# DiscordBotのトークンを設定
TOKEN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

# 各サーバーのRCON接続設定とディレクトリ設定
servers = {
    "MC001": {"ip": "127.0.0.1", "password": "XXXXXXXXXXXXXXX", "port": 60001, "directory": " /your/path/MC_001"},
    "MC002": {"ip": "127.0.0.1", "password": "XXXXXXXXXXXXXXX", "port": 60002, "directory": "/your/path/MC_002"},
    "MC003": {"ip": "127.0.0.1", "password": "XXXXXXXXXXXXXXX", "port": 60003, "directory": "/your/path/MC_003"},
}
# データパックコピー元フォルダのパス
source_folder = '/your/path/datapack'  
# データパックコピー先フォルダのパス
target_folder = '/your/path/MC_003/world/datapacks'  


# Intentsを設定（メッセージを受け取るために必要）
intents = discord.Intents.default()
intents.messages = True

# クライアントインスタンスを作成
client = discord.Client(intents=discord.Intents.all())

# 指定したセッション名が存在するか確認する関数
def is_screen_session_exists(session_name):
    result = subprocess.run("screen -ls", shell=True, capture_output=True, text=True)
    return session_name in result.stdout

# 任意のセッション名を指定してscreenを作成し、Minecraftサーバーを起動
def create_screen_and_run_commands(session_name, RUN):
    if is_screen_session_exists(session_name):
        print(f"セッション '{session_name}' は既に存在します。コマンドは実行されません。")
        return
    # screenセッションを作成してコマンドを実行
    subprocess.run(f"screen -dmS {session_name}", shell=True)
    
    # screenセッション内でコマンドを実行する
    directory = servers[session_name]["directory"]
    command = f"cd {directory} && {RUN}\n"
    subprocess.run(f"screen -S {session_name} -X stuff '{command}'", shell=True)
    print(f"セッション '{session_name}' が作成され、Minecraftサーバーを起動しています。")

# 指定したセッション名のscreenを削除（終了）する関数
def delete_screen_session(session_name):
    if not is_screen_session_exists(session_name):
        print(f"セッション '{session_name}' は存在しません。")
        return

    # screenセッションを終了
    subprocess.run(f"screen -S {session_name} -X quit", shell=True)
    print(f"セッション '{session_name}' は削除されました。")

    # MC003の場合、ワールドをリセット
    if session_name == "MC003":
        reset_world(servers[session_name]["directory"])

# サーバ内に人が居なければスクリーンを削除する関数
async def check_and_delete_screen(session_name):
    player_count = await get_player_count(session_name)
    if player_count == 0:
        delete_screen_session(session_name)
        print(f"削除リクエスト: セッション '{session_name}' は削除されました。")
    else:
        print(f"削除リクエスト: セッション '{session_name}' にはまだプレイヤーがいます。")

# RCONエラー時に3分後に再試行する関数
async def handle_rcon_error(session_name, error_message):
    print(f"Error: {session_name} でエラーが発生しました: {error_message}")
    await asyncio.sleep(180)  # 3分待機
    return await retry_get_player_count(session_name)

# 再試行してサーバ内の人数を取得する関数
async def retry_get_player_count(session_name):
    server = servers[session_name]
    try:
        # 再度Rconサーバーへの接続を試みる
        with mcrcon.MCRcon(server["ip"], server["password"], server["port"]) as mcr:
            log = mcr.command("list")
            print(f"セッション '{session_name}' において再試行 → {log}")

            # プレイヤー数の正規表現マッチング
            match = re.search(r"There are (\d+) of a max of", log)
            if match:
                player_count = int(match.group(1))
                print(f"セッション '{session_name}' の停止を回避しました。")
                return player_count
            else:
                print(f"Error: {session_name} でlistから人数の取得に失敗しました")
                delete_screen_session(session_name)  # エラー時にサーバを停止
                return None

    except mcrcon.MCRconException as e:
        print(f"Error: {session_name} で再試行時にRcon接続に失敗しました: {e}")
        delete_screen_session(session_name)  # エラー時にサーバを停止
        return None
    except Exception as e:
        print(f"Error: {session_name} で再試行時にエラーが発生しました: {e}")
        delete_screen_session(session_name)  # エラー時にサーバを停止
        return None

# サーバ内の人数を取得する関数
async def get_player_count(session_name):
    if not is_screen_session_exists(session_name):
        print(f"セッション '{session_name}' は存在しません。人数の取得をスキップします。")
        return None
    server = servers[session_name]

    try:
        # Rconサーバーへの接続
        with mcrcon.MCRcon(server["ip"], server["password"], server["port"]) as mcr:
            log = mcr.command("list")
            print(f"セッション '{session_name}' において → {log}")

            # プレイヤー数の正規表現マッチング
            match = re.search(r"There are (\d+) of a max of", log)
            if match:
                player_count = int(match.group(1))
                return player_count
            else:
                print(f"Error: {session_name} でlistから人数の取得に失敗しました")
                return None

    except mcrcon.MCRconException as e:
        return await handle_rcon_error(session_name, e)

    except Exception as e:
        return await handle_rcon_error(session_name, e)

# ワールドをリセットする関数
def reset_world(directory):
    try:
        directories_to_delete = [os.path.join(directory, "world"), os.path.join(directory, "world_nether"), os.path.join(directory, "world_the_end")]
        for dir_path in directories_to_delete:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                print(f"ワールドディレクトリ '{dir_path}' を削除しました。")
            else:
                print(f"ワールドディレクトリ '{dir_path}' は存在しません。")
    except Exception as e:
        print(f"ワールドディレクトリの削除中にエラーが発生しました: {e}")

# BOT起動時に呼び出されるイベント
@client.event
async def on_ready():
    print('  BOTが起動しました  ')
    check_player_count_1.start()
    check_player_count_2.start()
    check_player_count_3.start()


# データパックをコピペするコード
def copy_file(source_folder, target_folder, filename):
    # ソースフォルダのファイルパス
    source_file = os.path.join(source_folder, filename)
    
    # ターゲットフォルダの作成（存在しない場合）
    os.makedirs(target_folder, exist_ok=True)
    
    # コピー先のファイルパス
    target_file = os.path.join(target_folder, filename)
    
    # ファイルをコピー
    shutil.copy2(source_file, target_file)
    print(f"'{filename}'を '{target_folder}'にコピーしました。")


# メッセージを受け取ったときに呼び出されるイベント
@client.event
async def on_message(message):
    if 'on11' in message.content.lower():
        create_screen_and_run_commands("MC001", "java -Xms1G -Xmx8G -jar paper-1.20.4-493.jar nogui")
    elif 'on22' in message.content.lower():
        create_screen_and_run_commands("MC002", "java -Xms1G -Xmx10G -jar paper-1.20.4-493.jar nogui")
    elif 'on33' in message.content.lower():
        create_screen_and_run_commands("MC003", "java -Xms1G -Xmx6G -jar paper-1.20.4-493.jar nogui")
    elif 'off11' in message.content.lower():
        await check_and_delete_screen("MC001")
    elif 'off22' in message.content.lower():
        await check_and_delete_screen("MC002")
    elif 'off33' in message.content.lower():
        await check_and_delete_screen("MC003")
    elif 'data11' in message.content.lower():
        filename = 'Atrocious_ver1.1.zip'  # コピーするファイル名(データパック)
        copy_file(source_folder, target_folder, filename)


# サーバ内の人数を定期的にチェックするタスク（サーバー1）
@tasks.loop(seconds=60)
async def check_player_count_1():
    if not is_screen_session_exists("MC001"):
        print(f"セッション 'MC001' は存在しません。タスクをスキップします。")
        return
    player_count = await get_player_count("MC001")  # awaitを追加
    if player_count == 0:
        print(f"セッション 'MC001' のユーザ数が0人です。2分後にセッションを終了します。")
        await asyncio.sleep(120)  # 2分待機
        player_count = await get_player_count("MC001")  # awaitを追加
        if player_count == 0:
            delete_screen_session("MC001")

# サーバ内の人数を定期的にチェックするタスク（サーバー2）
@tasks.loop(seconds=60)
async def check_player_count_2():
    if not is_screen_session_exists("MC002"):
        print(f"セッション 'MC002' は存在しません。タスクをスキップします。")
        return
    player_count = await get_player_count("MC002")  # awaitを追加
    if player_count == 0:
        print(f"セッション 'MC002' のユーザ数が0人です。2分後にセッションを終了します。")
        await asyncio.sleep(120)  # 2分待機
        player_count = await get_player_count("MC002")  # awaitを追加
        if player_count == 0:
            delete_screen_session("MC002")

# サーバ内の人数を定期的にチェックするタスク（サーバー3）
@tasks.loop(seconds=60)
async def check_player_count_3():
    if not is_screen_session_exists("MC003"):
        print(f"セッション 'MC003' は存在しません。タスクをスキップします。")
        return
    player_count = await get_player_count("MC003")  # awaitを追加
    if player_count == 0:
        print(f"セッション 'MC003' のユーザ数が0人です。2分後にセッションを終了します。")
        await asyncio.sleep(120)  # 2分待機
        player_count = await get_player_count("MC003")  # awaitを追加
        if player_count == 0:
            delete_screen_session("MC003")


# Botの起動
client.run(TOKEN)

#!/bin/env python3

from __future__ import unicode_literals
import lyricsgenius as lg
from datetime import datetime
import os
import signal
import random
from yt_dlp import YoutubeDL, utils
import discord
from discord.ext import commands, tasks
import glob
import time
import asyncio
import subprocess
import sys
from dotenv import Dotenv
intents = discord.Intents().all()
# make the current working directory always the directory of the python script
os.chdir(os.path.dirname(sys.argv[0]))
genius = lg.Genius('dikK_AC8bpnsCUjOKGoRdmTkkGuYIqJLhyFMtmfu6MfYuaWm0ewpzAkis40JzLtv')

def startup():
    try:
        os.makedirs("Songs")
    except FileExistsError as e:
        print(e)
    cwd = os.getcwd()
    ideas = open(f'{cwd}/comments','a+')
    QUEUE = []
    return f'{cwd}/Songs'

def clear_all_songs():
    for song in glob.glob(rf'{SONG_FOLDER_PATH}/*'):
        try:
            print(f'11 REMOVING {song}')
            os.remove(song)
        except Exception as e:
            print(f'Error {e} -> Song: {song}')

CWD = os.getcwd()
SONG_FOLDER_PATH = startup()
clear_all_songs()

dotenv = Dotenv(f'{CWD}/.env')


TOKEN = dotenv.get('DISCORD_TOKEN')
CHANNEL = dotenv.get('CHANNEL_ID')
CHANNEL = int(CHANNEL)
QUEUE = []
VOICE_CHANNEL = None
NOW_PLAYING = None
LOOP = False
PAUSE = False
DOWNLOADING = False

ydl_opts = {
    'format': 'worstaudio',
    'outtmpl': rf'{SONG_FOLDER_PATH}/%(title)s.%(ext)s',
    'noplaylist':True,
    'max_downloads': 5,
    'throttled_rate': '100K',
    }

jcole = commands.Bot(command_prefix= '!', intents=intents)

def pretty_song_name(path):
    index1 = path.rfind('.')
    b = os.path.basename(os.path.normpath(path))[0:index1]
    index = b.rfind(r'.')
    return f'`{b[0:index]}`'

def get_jcole_beat(url):
    global QUEUE, DOWNLOADING
    DOWNLOADING = True
    ydl_opts['noplaylist'] = False
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            for song in glob.glob(rf'{SONG_FOLDER_PATH}/*'):
                _, ext = os.path.splitext(song)
                if ext != '.part':
                    if song not in QUEUE:
                        QUEUE.append(song)

    except utils.MaxDownloadsReached:
        for song in glob.glob(rf'{SONG_FOLDER_PATH}/*'):
            _, ext = os.path.splitext(song)
            if ext != '.part':
                if song not in QUEUE:
                    QUEUE.append(song)

        print(QUEUE)
    except Exception as e:
        print(e)
        DOWNLOADING = False
        raise Exception(f'Error while downloading song: {e}')
    return QUEUE[-1]

def get_from_song_name(*args):
    global QUEUE, DOWNLOADING
    DOWNLOADING = True
    print(args)
    ydl_opts['noplaylist'] = True
    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.extract_info(f'ytsearch:{args}', download=True)
            for song in glob.glob(rf'{SONG_FOLDER_PATH}/*'):
                _, ext = os.path.splitext(song)
                if ext != '.part':
                    if song not in QUEUE:
                        QUEUE.append(song)
                        return song # return QUEUE[-1]
        except Exception as e:
            print(e)
            DOWNLOADING = False
            raise Exception(f'Error while downloading song from title: {e}')

def play_music(vc, song=None, index=None):
    global QUEUE, NOW_PLAYING, DOWNLOADING
    DOWNLOADING = False
    if song:
        try:
            vc.play(discord.FFmpegPCMAudio(source=song))
            song = pretty_song_name(song)
            NOW_PLAYING = song
        except Exception as e:
            raise e
    if index != None:
        try:
            if QUEUE:
                vc.play(discord.FFmpegPCMAudio(source=QUEUE[index]))
                NOW_PLAYING = pretty_song_name(QUEUE[index])
                return True
            else:
                return
        except discord.errors.ClientException as e:
            if e == 'Already playing audio.':
                return "Song added to queue"
        except Exception as e:
            raise e

@tasks.loop(minutes=5)
async def dc():
    global VOICE_CHANNEL, PAUSE, DOWNLOADING, CHANNEL
    if not VOICE_CHANNEL:
        return
    if not VOICE_CHANNEL.is_connected():
        return
    start = time.time()
    while (time.time() - start < 300):
        if not VOICE_CHANNEL.is_playing() and not PAUSE and not DOWNLOADING:
            await asyncio.sleep(10)
        else:
            start = time.time()
            await asyncio.sleep(10)
    try:
        print('leaving server')
        await VOICE_CHANNEL.disconnect()
        await jcole.get_channel(CHANNEL).send('Bye Bye.')
    except Exception as e:
        print(e)

@tasks.loop(seconds=10)
async def next_song():
    global VOICE_CHANNEL, QUEUE, NOW_PLAYING, LOOP, CHANNEL, PAUSE, DOWNLOADING
    start = time.time()
    sys.stdout.flush()
    while not VOICE_CHANNEL:
        await asyncio.sleep(1)
        start = time.time()
    while (time.time() - start < 2):
        if not VOICE_CHANNEL.is_playing():
            await asyncio.sleep(2)
            if PAUSE or DOWNLOADING:
                start = time.time()
        else:
            await asyncio.sleep(1)
            start = time.time()
    try:
        if not LOOP:
            song = QUEUE.pop(0)
            print(f'14 REMOVING {song}')
            play_music(VOICE_CHANNEL, index=0)
            if QUEUE:
                await jcole.get_channel(CHANNEL).send(f'🎶  **Now playing**:  {NOW_PLAYING}')
            else:
                await jcole.get_channel(CHANNEL).send(f'🎶  **Nothing to play right now**')
            os.remove(song)
        else:
            play_music(VOICE_CHANNEL, index=0)
            if VOICE_CHANNEL.is_playing():
                print('DEBUG: 1')
                await jcole.get_channel(CHANNEL).send(f'🎶  **Now playing**:  {NOW_PLAYING}')
    except Exception as e:
        print(e)

@jcole.command(aliases=['PLAY'], help = "- Does the big play, joins the channel you're in, does other stuff also")
async def play(ctx, *args):
    global VOICE_CHANNEL, NOW_PLAYING, QUEUE, CHANNEL, CWD
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send commands in the music channel: <#{CHANNEL}>')
    command = ""
    # await ctx.send('1')
    try:
        voice_channel = ctx.author.voice.channel
        #await ctx.send(f'{voice_channel} {dir(voice_channel)} {voice_channel.members} {voice_channel.name}')
        users = []
        for member in voice_channel.members:
            users.append(member.nick)
        # await ctx.send(users)
        if len(users) > 2:
            names = ""
            for user in users[0:-1]:
                names = names + ", " + user
            names = names + ", and " + users[-1]
            command = f"gtts-cli 'Hello, {names}! Enjoy these bangers' --output out.mp3 --tld co.za"

        elif len(users) == 2:
            command = f"gtts-cli 'Hello, {users[0]}, and {users[1]}! Enjoy these bangers' --output out.mp3 --tld co.za"
        else:
            command = f"gtts-cli 'Hello, {users[0]}! Enjoy these bangers' --output out.mp3 --tld co.za"

    except AttributeError:
        return await jcole.get_channel(CHANNEL).send('Connect to a voice channel first.')

    except Exception as e:
        pass

    try:
        VOICE_CHANNEL = await voice_channel.connect()
        r = subprocess.run([f"{command}"], cwd=CWD, shell=True, capture_output=True)
        # await ctx.send(f"{command}")
        b = r.stderr
        # await ctx.send(f'{r.stderr} {r.stdout}')
        VOICE_CHANNEL.play(discord.FFmpegPCMAudio(source="out.mp3"))
        await asyncio.sleep(1)

    except discord.errors.ClientException as e:
        pass # already connected to the channel

    except Exception as e:
        await ctx.send(e)
    if len(args) == 1:
        if args[0].isnumeric(): # try to play sond at index args[0]
            play_music(VOICE_CHANNEL, index=int(args[0]))
            await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
        else: # must be a url, try to play it
            song = None
            try:
                song = get_jcole_beat(args[0])
                if song == None:
                    raise Exception("eh something went wrong but I genuinely don't know why, probably because a duplicate song was added... I didn't figure out how to do that")
                print(f'from get_jcole_beat -> {song}')
            except Exception as e:
                await ctx.send(e)
                return
            try:
                print(song)
            except Exception as e:
                await ctx.send(e)
                return
            if not VOICE_CHANNEL.is_playing() and len(QUEUE) == 1:
                try:
                    play_music(VOICE_CHANNEL, song=song)
                except Exception as e:
                    print(f'1: Error {e}')
                return await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
            else:
                play_music(VOICE_CHANNEL, index=0)
                return await ctx.send(f'🎶  **Song added to queue**: {pretty_song_name(song)}')
    if args:
        song = None
        try:
            song = get_from_song_name(*args)
            if song == None:
                raise Exception('`Some unknown error occurred when searching for a song by title`')
            if not VOICE_CHANNEL.is_playing() and len(QUEUE) == 1:
                try:
                    play_music(VOICE_CHANNEL, song=song)
                except Exception as e:
                    print(f'10: Error {e}')
                return await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
            else:
                play_music(VOICE_CHANNEL, index=0)
                return await ctx.send(f'🎶  **Song added to queue**: {pretty_song_name(song)}')

        except Exception as e:
            await ctx.send(f'Error `{e}` args: {args}')
    if not args:
        play_music(VOICE_CHANNEL, index=0)
        await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
        await ctx.send(f"`If that said None then don't worry about that`")

@jcole.command(aliases=['fs'], help = "- What do you mean? it's in the name of the command")
async def skip(ctx, *args):
    global VOICE_CHANNEL, NOW_PLAYING, QUEUE, LOOP, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        if VOICE_CHANNEL.is_playing():
            VOICE_CHANNEL.stop()
            if LOOP:
                QUEUE.pop(0)
                return await ctx.send(f"Yeah so I didn't actually figure out how to handle this, i think that skipping with loop turned on actually breaks everything so... if the bot is still working then that is amazing.")
            song_to_remove = QUEUE.pop(0)
            if play_music(VOICE_CHANNEL, index=0) == None:
                print(f'0 REMOVING {song_to_remove}')
                os.remove(song_to_remove)
                return await ctx.send(f'🎶  **Nothing to play right now**')
            await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
            await asyncio.sleep(1)
            print(f'1 REMOVING {song_to_remove}')
            os.remove(song_to_remove)
        else:
            pass
    except Exception as e:
        print(e)

@jcole.command(name='pause', help = "- Hiroshima but to the current song")
async def pause(ctx, *args):
    global VOICE_CHANNEL, CHANNEL, PAUSE
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    await ctx.send('Pausing...')
    PAUSE = True
    await VOICE_CHANNEL.pause()

@jcole.command(name='resume', help = "- all this does is tries to resume the music but so much can break")
async def resume(ctx, *args):
    global VOICE_CHANNEL, PAUSE
    await ctx.send('Viola, the music has returned')
    await VOICE_CHANNEL.resume()
    PAUSE = False

@jcole.command(name='queue', help = "- Prints an insanely ugly version of the queue")
async def queue(ctx, *args):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    entire_queue = ""
    for index, song in enumerate(QUEUE):
        if index == 0:
            entire_queue = entire_queue + f"🎶  **NOW PLAYING** - {pretty_song_name(song)}\n"
        elif index < 10:
            entire_queue = entire_queue + f"**{index}**. - {pretty_song_name(song)}\n"
        else:
            pass
    if entire_queue == "":
        entire_queue = 'No songs in the queue right now...'
    await ctx.send(entire_queue)

@jcole.command(name='shuffle', help='- Gives the queue a good mixin')
async def shuffle(ctx,):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    return await ctx.send('I broke it initially so for now it does nothing. May or may not ever fix it.')
    try:
        random.shuffle(QUEUE)
        await ctx.send(f'Successfully shuffled.')
        print(QUEUE)
    except Exception as e:
        await ctx.send(e)

@jcole.command(name='playing', help = "- Prints the current song being played")
async def playing(ctx, *args):
    global QUEUE, NOW_PLAYING, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    if len(QUEUE) > 0:
        return await ctx.send(f'🎶  **Now playing**:  {NOW_PLAYING}')
    return await ctx.send(f'Nothing is playing right now.')


@jcole.command(name='move', help = "- Moves a song from position x to position y")
async def move(ctx, x: int, y: int):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        QUEUE.insert(y, QUEUE.pop(x))
        await ctx.send(f'Successfully moved song to position {y}...')
    except Exception as e:
        await ctx.send(e)

@jcole.command(name='remove', help = "- gets rid of a song at whatever position you put, i'm getting bored of typing these though and I'm pretty sure no one is ever going to even read these")
async def remove(ctx, x: int):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        x = int(x)
        if x > 0 and x < len(QUEUE):
            song_to_remove = QUEUE.pop(x)
            print(f'2 REMOVING {song_to_remove}')
            os.remove(song_to_remove)
            await ctx.send(f'Successfully removed index {x}')
    except Exception as e:
        await ctx.send(f'You dumb, idk figure this out on your own... use this error message to figure out what you did so terribly wrong: {e}')

@jcole.command(name='clear', help = "- makes the queue go boom")
async def clear(ctx):
    global QUEUE, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    for song in glob.glob(rf'{SONG_FOLDER_PATH}/*'): # REMOVE EVERYTHING, used to be .webm
        try:
            os.remove(song)
            print(f'10 REMOVING {song_to_remove}')
        except Exception as e:
            print(f'Error {e} -> Song: {song}')
    QUEUE = []
    await ctx.send('💥⚠️  **QUEUE EMPTIED**  ⚠️💥')

@jcole.command(name='loop', help = "- why")
async def loop(ctx):
    global LOOP, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    LOOP = not LOOP
    if LOOP:
        await ctx.send('🤪 🤪  ***GET DIZZY HAHA*** 🤪🤪')
    else:
        await ctx.send('**Loop disabled**')

@jcole.command(name='leave', help = "- makey bot go bye bye 😔")
async def leave(ctx):
    global VOICE_CHANNEL, CHANNEL
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    await VOICE_CHANNEL.disconnect()

@jcole.command(name='comment', help = "- you can leave me a comment about what to add or if something went wrong")
async def comment(ctx, *args):
    global CWD
    if args:
        with open(f'{CWD}/comments', 'a') as file:
            file.write(f'{datetime.now().strftime("[%Y/%m/%d][%H:%M]-")} {ctx.message.author.name}: {" ".join(args)}\n')
        file.close()

@jcole.command(name='viewComments', help = '- shows all of the comments made so far')
async def view_comments(ctx, *args):
    text = []
    to_return = ""
    global CWD
    with open(f'{CWD}/comments' ,'r') as file:
        text.append(file.read().strip().split('\n'))
    text = text[0]
    if len(text) > 5:
        to_return = "\n".join(text[-5:])
    else:
        to_return = '\n'.join(text)
    if to_return:
        await ctx.send(to_return)

@jcole.command(name='reboot', help = "- reboots the raspberry pi, if this doesn't work then you're fucked :)")
async def reboot(ctx, *args):
    if ctx.message.channel.id != CHANNEL:
        return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    try:
        os.system('reboot')
    except Exception as e:
        await ctx.send(f'Failed to reboot -> {e}')

@jcole.command(name='lyrics', help = ' - might not work atm, trying to use rap genius to get the lyrics.')
async def lyrics(ctx, *args):
    global NOW_PLAYING
    if ctx.message.channel.id != CHANNEL:
        return
    try:
        song = genius.search_song(NOW_PLAYING)
        await ctx.send(f'Lyrics found for {NOW_PLAYING}')
        await ctx.send(f'{song.lyrics}')
    except Exception as e:
        await ctx.send(e)
    #print(song.lyrics)

@jcole.command(name='hotfix', help= "- removes duplicate instances of the bot, this seems to be what causes 99% of the bot's problems.")
async def hotfix(ctx, *args):
    if ctx.message.channel.id != CHANNEL:
         return await ctx.send(f'You can only send stuff to the music channel: <#{CHANNEL}>')
    os.system('systemctl show --property MainPID rhythm > out.txt; pidof python3 >> out.txt')

    with open('out.txt', 'r') as f:
        test = f.readlines()
        rhythm_pid = None
        extra = []
        for index, line in enumerate(test):
            if index == 0:
                rhythm_pid = line.replace('MainPID=','').strip()
            else:
                extra = line.strip().split(' ')
                extras = [x for x in extra if x != rhythm_pid]
                if extras:
                    for PID in extras:
                        print(f'Killing PID: {PID}')
                        os.kill(int(PID), signal.SIGTERM)
                        await ctx.send(f'`Main PID: {rhythm_pid}. Extra PID killed: {PID}`')
                else:
                    await ctx.send('No other instances to kill. If the bot is not working then maybe reboot. Be aware that rebooting sometimes is the cause of creating duplicate instances so you might have to run this command again. i dunno')

@jcole.event
async def on_ready():
    print(f'{jcole.user} is connected!')
    await jcole.get_channel(CHANNEL).send('give me beats.')
    # await jcole.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="mukiz"))

dc.start()
next_song.start()
jcole.run(TOKEN)

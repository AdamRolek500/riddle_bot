"""
Discord bot to give a random daily riddle

By: Adam Rolek
"""
import discord
import os
import sqlite3
import threading
import json
import asyncio
from time import sleep
from sqlite3 import Error
from random import randint

#Discord client, used for all dicord functions.
client = discord.Client()
#Harder to access when the connection isn't global
db_connection = None
lock = threading.Lock()
riddle_index = 0
riddle = ''
answer = ''
is_answered = None

database_path = "E:\Discord Bots\\riddle_bot\databases\dailyriddles.db"
sql_create_riddles_table = """ CREATE TABLE IF NOT EXISTS riddles (
                                id integer PRIMARY KEY,
                                riddle text,
                                answer text
                                ); """
sql_create_riddle = 'INSERT INTO riddles(riddle,answer) VALUES(?,?)'
sql_get_count = 'SELECT count(*) FROM riddles'
sql_get_riddle = 'SELECT * FROM riddles WHERE id = '

@client.event
async def on_message(message):
    global is_answered
    if message.content.startswith('~riddle'):
        if is_answered == None or is_answered:
            if(get_random_riddle(db_connection) == True):
                with lock:
                    is_answered = False
                await client.send_message(message.channel, '#' + str(riddle_index) + ': ' + riddle)
                print('-----Sent Riddle-----')
                print('#' + str(riddle_index) + ': ' + riddle)
                print('\nAnswer: ' + answer)
                wait_thread = threading.Thread(target = day_countdown(message.channel))
                wait_thread.deamon = True
                wait_thread.start()
                #TODO: Setup the thread for waiting a day to update is_answered
                #   - make 'time_is_up' var
            else:
                await client.send_message(message.channel, 'Could not access database!')
        else:
            print('The riddle isnt answered')
            await client.send_message(message.channel, 'Must answer the current riddle...\n')
            await client.send_message(message.channel, '#' + str(riddle_index) + ': ' + riddle)
            #TODO: The riddle isnt answered so show how long until a refresh may happen...
    if message.content.startswith('~answer'):
        #TODO:
        #   - Cant answer when is_answered == None
        #   - make answer formula
        print(answer)
        with lock:
            is_answered = True

@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user.name))

def create_connection(db_file):
    '''
    Function used to create a connection to a local database. 
    Creates the database if it does not exist
    
    params:
        bd_file: File path to the database
    returned:
        connection: The database connection object
        None: if the connect failed
    '''
    try:
        #Connecting/Making database
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    #Connection was not made at this point
    return None
    
def create_table(conn, create_table_sql):
    '''
    Function used to create the riddle table in the database.
    
    params:
        conn: Database connection
        create_table_sql: SQL statement to create the riddles table
    returned:
        Nothing is returned
    '''
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print('Creating the Riddle table if it is not present.')
    except Error as e:
        print(e)
        
def create_riddle(conn, project):
    cur = conn.cursor()
    cur.execute(sql_create_riddle, project)
    
def populate_database():
    with open('riddles.txt') as f:
        content = f.readlines()
        content = [x.strip() for x in content]
        with db_connection:
            for x in range(0, len(content), 2):
                project = (content[x], content[x + 1]);
                project_id = create_riddle(db_connection, project)
                print("({}, {})\n".format(content[x], content[x + 1]))
                
def get_random_riddle(connection):
    try:
        global riddle
        global answer
        global riddle_index
        cur = connection.cursor()
        cur.execute(sql_get_count)
        returned = cur.fetchall()
        riddle_index = randint(1, returned[0][0])
        cur.execute(sql_get_riddle + str(riddle_index))
        returned = cur.fetchall()
        riddle = returned[0][1]
        answer = returned[0][2]
        return True
    except:
        print('Error accessing the riddle database...')
        return False
        
def day_countdown(channel):
    global is_answered
    for sec in range(10):
        print(sec)
        sleep(1)
    with lock:
        is_answered = True
    print('-----Time is up!-----')
    print('The time to answer the riddle has passed!')
    print('#' + str(riddle_index) + ': ' + riddle)
    print('Answer: ' + answer)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(timeout_notify_user(channel))
    return
    
async def timeout_notify_user(channel):
    await client.send_message(channel, 'The time to answer the riddle has passed!')
    await client.send_message(channel, '#' + str(riddle_index) + ': ' + riddle)
    await client.send_message(channel, 'Answer: ' + answer)

def main():
    os.system('cls')
    global db_connection
    print('Attempting to load: {}'.format(database_path))
    db_connection = create_connection(database_path)
    if db_connection is not None:
        print('Database loaded: {}'.format(database_path))
        create_table(db_connection, sql_create_riddles_table)
    else:
        print('Could not load: {}'.format(database_path))
    with open('auth.json') as f:
        data = json.load(f)
    client.run(data["api_token"])
    
if __name__ == '__main__':
    main()
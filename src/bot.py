"""
Discord bot to give a random daily riddle

By: Adam Rolek
"""
import discord
import os
import sqlite3
import json
import asyncio
from datetime import datetime
from sqlite3 import Error
from random import randint
from difflib import SequenceMatcher

#Discord client, used for all dicord functions.
client = discord.Client()
#Harder to access when the connection isn't global
db_connection = None
riddle_index = 0
riddle = ''
answer = ''
riddle_time = None

database_path = "E:\Discord Bots\\riddle_bot\databases\dailyriddles.db"
sql_create_riddles_table = """ CREATE TABLE IF NOT EXISTS riddles (
                                id integer PRIMARY KEY,
                                riddle text,
                                answer text
                                ); """
sql_create_riddle = 'INSERT INTO riddles(riddle,answer) VALUES(?,?)'
sql_get_count = 'SELECT count(*) FROM riddles'
sql_get_riddle = 'SELECT * FROM riddles WHERE id = '

#Bot Functions

@client.event
async def on_message(message):
    """
    Function that allows the bot to see messages.
    
    params: 
        message: mesaage information from user messages in discord
    
    return:
        nothing
    """
    #lets just make sure our bot is not sending commands to us.
    if message.author == client.user:
        return
    global riddle_time
    #This may be the firtime that on_message is called, so, riddle_time is'None'
    try:
        time_difference = datetime.now() - riddle_time
    except:
        print('Could not get the time difference... Perhaps the \'riddle_time\' variable is not set?')
    #user is asking for a new riddle
    if message.content.startswith('~r'):
        #Make sure that the riddle_time is either not set or above 1 day. Accurate down to a second. 
        if riddle_time == None or time_difference.seconds >= 86400: #There are 86400 seconds in a day
            #Making sure that we were able to get a riddle form the database
            if(get_random_riddle(db_connection) == True):
                #The current time is when we got this riddle so lets store that time.
                riddle_time = datetime.now()
                #Logging
                print('-----SENT RIDDLE-----')
                print('Time: ' + str(riddle_time))
                print('\n#' + str(riddle_index) + ': ' + riddle)
                print('\nAnswer: ' + answer)
                #sending the riddle to the user
                await client.send_message(message.channel, '#' + str(riddle_index) + ': ' + riddle)
            else:
                #Letting the user know we could not access the database
                await client.send_message(message.channel, 'Could not access database!')
        else:
            #if the current riddle was not answered correctly
            print('-----CURRENT RIDDLE ISNT ANSWERED-----')
            print('\n#' + str(riddle_index) + ': ' + riddle)
            print('\nTime Remaining: ' + second_converter(time_difference.seconds))
            await client.send_message(message.channel, 'Must answer the current riddle...\n')
            await client.send_message(message.channel, '#' + str(riddle_index) + ': ' + riddle)
            await client.send_message(message.channel, 'Remaining Time: ' + second_converter(time_difference.seconds))
    if message.content.startswith('~a'):
        #Make sure that the riddle_time is either not set or above 1 day. Accurate down to a second. 
        if not riddle_time == None:
            if(time_difference.seconds <= 86400): #There are 86400 seconds in a day
                # compair the ratio of similarity between user and real ananswer, some answers are long
                if(SequenceMatcher(None, message.content, answer).ratio() >= .5):
                    await client.send_message(message.author, "Correct!")
                    riddle_time = None
                else: 
                    await client.send_message(message.author, "Incorrect!")
            else:
                await client.send_message(message.channel, 'The answer window for the current riddle has expired, ' +
                    'please request a new one.')
        else:
            await client.send_message(message.channel, 'No riddle is currently ative to be answered, please request one.')
    if message.content.startswith('~help'):
        await client.send_message(message.channel, 'Daily Riddle Bot Commands:')
        await client.send_message(message.channel, '    ~r: Request a new riddle')
        await client.send_message(message.channel, '    ~a [TEXT]: Attempt to answer the current riddle')
        await client.send_message(message.channel, '    ~help: Daily Riddle Bot Command Help Page')

@client.event
async def on_ready():
    """
    Called when tyhe bot comes online
    """
    print('Logged in as {}'.format(client.user.name))
    
#Utility Functions

def second_converter(seconds):
    """
    Helpful function for getting the time left for a riddle in a nice readable form
    Accurate down to the second.
    
    params:
        seconds: The time inseconds that the current riddle has been active
    
    return:
        result: Formated string so it is understandable (Pretty Print)
    """
    seconds = 86400 - seconds
    result = ''
    if((seconds % (60 * 60 * 24)) >= 0):
        result += str(int(seconds / (60 * 60 * 24))) + ' Days '#days
        seconds %= 60 * 60 * 24
    if((seconds % (60 * 60)) >= 0):
        result += str(int(seconds / (60 * 60))) + ' Hours '#hours
        seconds %= 60 * 60
    if(seconds % 60 >= 0):
        result += str(int(seconds / 60)) + ' Minutes '#minutes
        seconds %= 60
    result += str(seconds) + ' Seconds'#seconds
    return result

#Database Functions

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
        #Create a cursor and atemp to create the table
        c = conn.cursor()
        c.execute(create_table_sql)
        print('Creating the Riddle table if it is not present.')
    except Error as e:
        print(e)
        
def create_riddle(conn, riddle):
    """
    Helpful for entering data into the database
    
    params:
        conn: The database connection
        riddle: Riddle tuple containg the riddle and answer
    """
    cur = conn.cursor()
    cur.execute(sql_create_riddle, riddle)
    
def populate_database():
    """
    Helper function to read data from riddles.txt and insert them into dailyriddle.db
    """
    with open('riddles.txt') as f:
        content = f.readlines()
        content = [x.strip() for x in content]
        with db_connection:
            for x in range(0, len(content), 2):
                riddle = (content[x], content[x + 1]);
                riddle_id = create_riddle(db_connection, riddle)
                print("({}, {})\n".format(content[x], content[x + 1]))
                
def get_random_riddle(connection):
    """
    Used to fetch a riddle from the database at a random index
    
    params:
        connection: the database connection
        
    return:
        True: for a success
        False: For a failure
    """
    try:
        global riddle
        global answer
        global riddle_index
        cur = connection.cursor()
        #let get the count of rows in the riddls table
        cur.execute(sql_get_count)
        returned = cur.fetchall()
        #getting a random ID
        riddle_index = randint(1, returned[0][0])
        #pulling the random riddle
        cur.execute(sql_get_riddle + str(riddle_index))
        returned = cur.fetchall()
        #storing the riddle and answer
        riddle = returned[0][1]
        answer = returned[0][2]
        return True
    except:
        print('Error accessing the riddle database...')
        return False

def main():
    os.system('cls') #Lets get a clean screen
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
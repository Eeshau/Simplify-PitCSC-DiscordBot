import time
import requests
import base64
import discord
from discord.ext import commands
import os
#from keep_alive import keep_alive
#import nest_asyncio
import asyncio
#nest_asyncio.apply()
from dotenv import load_dotenv
load_dotenv()

#---------------------------------------------------------------
owner = "Eeshau"                              # replace with "pittcsc" 
repo = "Summer2024-Internships"
api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
etag = None
last_etag = None                              # Variable for tracking changes to the file
table_rows = []                               # Latest List of internship rows 
last_table_rows = []                          # List of last recorded internship rows
channel_name = "general"                      # Replace "general" with the actual channel name 
discord_token =  os.environ['DISCORD_TOKEN']  # Load environment variables from .env file
TOKEN = discord_token
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


class ButtonsRow(discord.ui.View):
  def __init__(self):
    super().__init__()
    self.value = None


#---------------------------------------------------------------
# First time the bot sets the last_etag and last_table_rows vars
response = requests.get(api_url)
if response.status_code == 200:
    data = response.json()
    last_etag = data.get("sha")
    content = data.get("content")
    decoded_content = base64.b64decode(content).decode("utf-8")
    table_start = decoded_content.find("| Name | Location | Notes |")
    table_end = decoded_content.find("|\n\n", table_start)

    if table_start != -1 and table_end != -1:
        # Extract the table content
        table_content = decoded_content[table_start:table_end]

        # Split the table content into rows
        last_table_rows = table_content.strip().split("\n")[2:]
else:
    print(f"Failed to fetch README file: {response.status_code} - {response.text}")




#---------------------------------------------------------------
# BOT SENDS the NEW or modified table rows to the Discord "general" channel for all the servers it's in
async def send_message_to_channel(new_rows):
    # Create a Discord client instance
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        # Loop through every server the bot is inside of
        for guild in client.guilds:
            # Find the server id of the "general" channel
            server = client.get_guild(guild.id)
            if server:
                channel = discord.utils.get(server.channels, name=channel_name)
                if channel is not None:
                    # Send the message to the channel
                    await channel.send("**NEW or modified postings on Simplify x PitCSC Internship List**")
                    for row in new_rows:
                        await channel.send(f'```{str(row[1:-1])}```')
                    # Buttons with Links
                    view = ButtonsRow()
                    view.add_item(discord.ui.Button(label="View Postions on Github 👀",style=discord.ButtonStyle.link,url="https://github.com/Eeshau/Summer2024-Internships/blob/dev/README.md"))
                    view.add_item(discord.ui.Button(label="Simplify.jobs",style=discord.ButtonStyle.link,url="https://simplify.jobs"))
                    await channel.send(view=view)
                else:
                    print(f"Channel with name '{channel_name}' not found in server '{server.name}'.")
            else:
                print("Server not found.")

        # Close the client connection
        await client.close()

    # Run the client
    await client.start(TOKEN)




#---------------------------------------------------------------
# GRABS CONTENTS FROM THE README FILE
# by using github api
def get_readme_content():
    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Failed to fetch README file: {response.status_code} - {response.text}")
    return response.json()



##---------------------------------------------------------------
# FINDS DIFFERENCE IN TABLES I.E NEW ROWS ADDED OR MODIFIED
# by comparing last_table_row with table_row, i.e list1 with list 2
def find_difference(list1, list2):
    difference = [item for item in list1 if item not in list2]
    return difference



#---------------------------------------------------------------
# CHECKS IF CHANGES WERE MADE TO THE README FILE BASED 
# by checking if etag hash property of the repo has changed from last_etag
async def check_readme_changes():
    global last_etag
    global last_table_rows

    readme_content = get_readme_content()
    etag = readme_content.get("sha")
    content = readme_content.get("content")
    decoded_content = base64.b64decode(content).decode("utf-8")

    if etag != last_etag:
        print("README has been modified!")
        # PUT THE ROWS OF THE README FILE INTO A LIST CALLED TABLEROWS
        table_start = decoded_content.find("| Name | Location | Notes |")
        table_end = decoded_content.find("|\n\n", table_start)

        if table_start != -1 and table_end != -1:
            # Extract the table content from the rest of the readme file
            table_content = decoded_content[table_start:table_end]

            # Split the table content into rows
            table_rows = table_content.strip().split("\n")[2:]
            
            # Identifiy and store new or modified rows in new_rows
            new_rows = []
            new_rows = find_difference(table_rows, last_table_rows)
            
            # DISCORD BOT SENDS the NEW or modified table rows to the channel 
            await send_message_to_channel(new_rows)

            # Save this table as the last /most recent table
            last_table_rows = table_rows
        else:
            print("Table not found in the content.")
    else:
        print("README UNMODIFIED!")
    last_etag = etag


#---------------------------------------------------------------
# MONITOR FOR CHANGES EVERY 5 MINUTES
# by setting interval delay and running check_readme_changes where the main code is
async def monitor_readme_changes(interval):
    while True:
        await check_readme_changes()
        time.sleep(interval)

#keep_alive()
asyncio.run(monitor_readme_changes(25))
#---------------------------------------------------------------
# Standard library imports
import asyncio
import json
import os
import queue as thread_queue
import random
import re
import sqlite3
import threading
import aiofiles
import pytz

# Related third-party imports
import aiohttp
import cachetools
import discord
from discord import Embed, commands
from discord.ext import commands, tasks
import openai
import tiktoken
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime
# Local application/library specific imports
from chat_functions import functions
from prompt import initialize_conversation
from strings import typing_indicators, image_analysis_messages, image_generation_messages, google_search_messages, scrape_web_page_messages, status_list
from utils.count_tokens_in_conversation import count_tokens_in_conversation
from utils.exponential_backoff import exponential_backoff
from utils.get_conversation import get_conversation
from utils.get_date_time import get_date_time
from utils.google_search import google_search
from utils.scrape_web_page import scrape_web_page
from utils.store_conversation import store_conversation
from utils.handle_send_to_discord import update_conversation_and_send_to_discord, send_to_discord, threaded_fetch, generate_response
# from utils.image_processing import get_detailed_caption
from utils.generate_image import generate_images
from utils.moderate_message import moderate_content
from utils.check_user_level import check_user_level
from utils.wolfram_alpha import query_wolfram_alpha, filter_relevant_info
# from code_interpreter.docker import run_code_in_docker
from utils.get_and_set_timezone import get_timezone, set_timezone

# get from environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

openAI_model = ["gpt-4", "got-3.5-turbo-16k"]
token_limit = 7000

# Load an encoding for the specific model
encoding = tiktoken.encoding_for_model("gpt-4")

db_conn = sqlite3.connect('conversations.db')
db_conn.execute("""
CREATE TABLE IF NOT EXISTS conversations
    (conversation_id INTEGER PRIMARY KEY,
    conversation TEXT,
    is_busy BOOLEAN)
""")

# Connect to SQLite database (it will create a new file if not exists)
conn = sqlite3.connect('discord_timezones.db')

# Create a cursor object to execute SQL queries
c = conn.cursor()

# Create new table
c.execute("""
CREATE TABLE IF NOT EXISTS UserTimezones (
    discord_id INTEGER PRIMARY KEY,
    timezone TEXT
);
""")

# Commit the changes
conn.commit()

# Close the connection
conn.close()

async def download_image(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filename, 'wb') as f:
                    f.write(await resp.read())
            else:
                print("Couldn't download the image!")
                
def sanitize_json_string(json_str):
    json_str = json_str.replace("\\", "\\\\")
    json_str = json_str.replace("\"", "\\\"")
    json_str = json_str.replace("\n", "\\n")
    json_str = json_str.replace("\t", "\\t")
    return json_str

class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as", self.user)
        self.loop = asyncio.get_running_loop()
        self.change_status_task = self.loop.create_task(self.change_status())
        
    async def change_status(self):
        while not self.is_closed():
            # Change Bot Status
            await self.change_presence(activity=discord.Game(name=random.choice(status_list)))
            await asyncio.sleep(300)  # wait for 10 minutes or 600 seconds

    async def on_message(self, message):
        if message.author == self.user:
            return
        

        # Use create_task to run response generation concurrently
        asyncio.create_task(self.respond_to_message(message))

    async def respond_to_message(self, message):
        conversation_id = (
            message.author.id
            if isinstance(message.channel, discord.DMChannel)
            else message.channel.id
        )
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        def delete_conversation(conversation_id):
            c = db_conn.cursor()
            c.execute("DELETE FROM conversations WHERE conversation_id=?", (conversation_id,))
            db_conn.commit()
            
        def ensure_is_busy_column_exists():
            c = db_conn.cursor()
            c.execute("PRAGMA table_info(conversations);")
            columns = [column[1] for column in c.fetchall()]
            if 'is_busy' not in columns:
                c.execute("ALTER TABLE conversations ADD COLUMN is_busy BOOLEAN")
                db_conn.commit()

        # Function to check if the bot is busy
        def is_bot_busy(conversation_id):
            ensure_is_busy_column_exists()
            c = db_conn.cursor()
            c.execute("SELECT is_busy FROM conversations WHERE conversation_id=?", (conversation_id,))
            row = c.fetchone()
            return row[0] if row else False

        # Function to set bot as busy
        def set_bot_busy(conversation_id, busy=True):
            ensure_is_busy_column_exists()
            c = db_conn.cursor()
            c.execute("UPDATE conversations SET is_busy=? WHERE conversation_id=?", (busy, conversation_id))
            db_conn.commit()
            
        async def busy_message(message, text, delay=5):
            msg = await message.reply(text)
            await asyncio.sleep(delay)
            await msg.delete()

        if is_bot_busy(conversation_id) and "byte" in message.content.lower():
            asyncio.create_task(busy_message(message, "My mind is elsewhere, I'm busy with another task! Please try again after my previous task is done."))
            return

        if message.content.strip() == '!clear':
            # Check if in a DM
            if is_dm:
                delete_conversation(conversation_id)
                await message.channel.send("Conversation has been cleared.")
                return
            else:
                # Check if the author has the "Bot Manager" role
                if any(role.name == "Bot Manager" for role in message.author.roles):
                    delete_conversation(conversation_id)
                    await message.channel.send("Conversation has been cleared.")
                    return
                else:
                    await message.channel.send("You do not have permission to clear the conversation.")
                    return
        if message.content.strip() == '!unblock':
            # Check if in a DM
            if is_dm:
                set_bot_busy(conversation_id, False)
                await message.channel.send("Conversation has been unblocked.")
                return
            else:
                # Check if the author has the "Bot Manager" role
                if any(role.name == "Bot Manager" for role in message.author.roles):
                    set_bot_busy(conversation_id, False)
                    await message.channel.send("Conversation has been unblocked.")
                    return
                else:
                    await message.channel.send("You do not have permission to unblock the conversation.")
                    return
                
        if message.content.strip().startswith('!settimezone '):
            new_timezone = message.content.strip()[13:].strip()  # Remove the command prefix and extra spaces

            # Get the Discord ID from the message author
            discord_id = message.author.id  # Replace this line with how you get the Discord ID

            # Attempt to set the new timezone
            if set_timezone(discord_id, new_timezone):
                await message.channel.send(f"Timezone has been set to {new_timezone}.")
            else:
                await message.channel.send("Invalid timezone. Please use a valid IANA Time Zone like 'UTC' or 'America/New_York'.")
            return

        conversation = get_conversation(conversation_id)
        if conversation is None:
            conversation = initialize_conversation(conversation_id, is_dm)

        content = moderate_content(message)
        print(content)

        new_message = {"role": "user", "content": content.strip()}
        conversation.append(new_message)
        store_conversation(conversation_id, conversation)

        # If the conversation exceeds the limit
        while (count_tokens_in_conversation(conversation)> token_limit):
            # Check if the earliest message is a system message
            if conversation[0]["role"] == "system":
                # If it's a system message, remove and insert it at the second last position
                system_message = conversation.pop(0)
                conversation.insert(-1, system_message)
            else:
                # If not, just remove the earliest message
                conversation.pop(0)
            store_conversation(conversation_id, conversation)

        async def edit_message_text(message, content: str):
            await message.edit(content=content)
            
        image_detected = False # Whether an image was detected
        
        # if message.attachments and message.attachments[0].content_type.startswith("image/"):
        #     image_detected = True
        #     image_analysis_message = random.choice(image_analysis_messages)
        #     temp_message = await message.channel.send(image_analysis_message)

        #     # Capture user's message text
        #     user_message_text = message.content if message.content else "No additional text provided."

        #     # Use the new function to get detailed caption and extracted text
        #     image_url = message.attachments[0].url
        #     caption = get_detailed_caption(image_url, user_message_text)
        #     print(f"Caption from img2text: {caption}")

        #     # Construct the content string with the newly extracted data and user's message
        #     content = (
        #         f"{message.author.name} said '{user_message_text}' and sent an image with the contents: '{caption}'. "
        #         "When given an image caption from a specific source, refrain from disclosing the source or mentioning it in the response. Instead, smoothly integrate the information into your conversational reply as if it was naturally occluded from your analysis of the image."
        #     )
        #     print(content)

        #     conversation.append(
        #         {
        #             "role": "function",
        #             "name": "view_image",
        #             "content": content.strip(),
        #         }
        #     )

        #     final_response = ""
        #     completion = ""
        #     response = generate_response(conversation)
        #     thread_safe_queue = thread_queue.Queue()
        #     threading.Thread(target=threaded_fetch, args=(response, thread_safe_queue, completion)).start()

        #     completion, temp_message = await send_to_discord(thread_safe_queue, 50, 2000, 0.3, temp_message, final_response, message)
        #     conversation.append(
        #         {
        #             "role": "assistant",
        #             "content": completion[:2000],
        #         }
        #     )
        #     store_conversation(conversation_id, conversation)
        #     completion = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', completion)
        #     await temp_message.edit(content=completion)

        if (("byte" in message.content.lower() or is_dm) and not image_detected):
            set_bot_busy(conversation_id, True)
            typing_indicator = random.choice(typing_indicators)
            temp_message = await message.channel.send(typing_indicator)
            if is_dm:
                print('\033[92m' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - Byte was called in a DM by " + message.author.name + '\033[0m')
            else:
                print('\033[94m' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - Byte was called in a server by " + message.author.name + '\033[0m')

            response = exponential_backoff(
                lambda model: openai.ChatCompletion.create(
                model=model,
                messages=conversation,
                functions=functions,
                stream=True,
                allow_fallback=True,
                ),
            )
            thread_safe_queue = thread_queue.Queue()
            final_response = ""
            function_name = None
            regular_response = ''
            function_arguments = ''
            for chunk in response:
                # check if response is regular response
                if chunk["choices"][0]["delta"].get("content"):
                    regular_response += chunk["choices"][0]["delta"]["content"]
                    thread_safe_queue.put(chunk["choices"][0]["delta"]["content"])
                    threading.Thread(target=threaded_fetch, args=(response, thread_safe_queue, final_response)).start()
                    completion, temp_message = await send_to_discord(thread_safe_queue, 50, 2000, 0.3, temp_message, final_response, message)
                    conversation.append(
                        {
                        "role": "assistant",
                        "content": completion[:2000],
                        }
                    )
                    store_conversation(conversation_id, conversation)
                    completion = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', completion)
                    # print(completion)
                    await temp_message.edit(content=completion[:2000])
                    set_bot_busy(conversation_id, False)
                    # print("Final reponse:" + repr(temp_message.content))
                # check if response is function call
                if chunk["choices"][0]["delta"].get("function_call"):
                    if "name" in chunk["choices"][0]["delta"]["function_call"]:
                        function_name = chunk["choices"][0]["delta"]["function_call"]["name"]
                    chunk = chunk["choices"][0]["delta"]
                    function_arguments_chunk = chunk["function_call"]["arguments"]
                    function_arguments += function_arguments_chunk
                    print(function_arguments_chunk, end='', flush=True)
            thread_safe_queue.put(None)  # Sentinel value to indicate end of response

            if (function_name == "google_search"):  #* Google search function response
                function_arguments = json.loads(function_arguments)
                search_term = function_arguments.get("search_term")
                num_results = function_arguments.get("num_results")
                temp_message_text = random.choice(google_search_messages).format(search_term)
                await edit_message_text(temp_message, temp_message_text)
                function_response = google_search(search_term=search_term,num_results=num_results,api_key=google_api_key,cse_id=google_cse_id,)
                function_response = "Give these results to the user in a conversational format, not a list. Never deliver the results in a list. Here they are: " + function_response
                await update_conversation_and_send_to_discord(function_response, function_name, temp_message, conversation, conversation_id, message)
                set_bot_busy(conversation_id, False)

            elif (function_name == "scrape_web_page"):  #* Scrape web page function response
                function_arguments = json.loads(function_arguments)
                url = function_arguments.get("url")
                temp_message_text = random.choice(scrape_web_page_messages).format(url)
                await edit_message_text(temp_message, temp_message_text)
                function_response = scrape_web_page(url)
                await update_conversation_and_send_to_discord(function_response, function_name, temp_message, conversation, conversation_id, message)
                set_bot_busy(conversation_id, False)

            elif (function_name == "ask_wolfram_alpha"):  #* Ask Wolfram Alpha function response
                function_arguments = json.loads(function_arguments)
                query = function_arguments.get("query")
                temp_message_text = "Checking my answer for " + query
                await edit_message_text(temp_message, temp_message_text)
                function_response = query_wolfram_alpha(query)
                await update_conversation_and_send_to_discord(function_response, function_name, temp_message, conversation, conversation_id, message)
                set_bot_busy(conversation_id, False)
                
            # elif (function_name == "run_python_code_in_docker"):
            #     now = datetime.now()
            #     filename = f'code_{conversation_id}_{now.strftime("%Y%m%d_%H%M%S")}.py'

            #     sanitized_arguments = re.sub(r'\\n', '\\\\n', function_arguments)
            #     sanitized_arguments = re.sub(r'\\t', '\\\\t', sanitized_arguments)

            #     try:
            #         function_arguments_dict = json.loads(sanitized_arguments)
            #     except json.JSONDecodeError as e:
            #         print(f"JSONDecodeError: {e}")
            #         await update_conversation_and_send_to_discord("The JSON arguments provided were invalid.", function_name, temp_message, conversation, conversation_id, message)
            #         set_bot_busy(conversation_id, False)
            #         return

            #     code = function_arguments_dict.get("code")

            #     temp_message_text = "Running some code for you, please wait..."
            #     await edit_message_text(temp_message, temp_message_text)

            #     # code_interpreter_output, host_image_path = run_code_in_docker(code)
            #     print(code_interpreter_output)

            #     with open(filename, 'w') as f:
                
            #         f.write('# Here is the code I generated:\n')
            #         f.write(code + '\n')

            #         if 'matplotlib' in code:
            #           f.write('\n# Output: \nA plot was saved to /tmp')
            #         else:  
            #           f.write('\n# Output: \n' + code_interpreter_output)

            #     # await message.channel.send(file=discord.File(filename))
            #     function_response = "The code that was executed was: " + code + " and the output is: " + code_interpreter_output
            #     print(function_response)

            #     await update_conversation_and_send_to_discord(function_response, function_name, temp_message, conversation, conversation_id, message)
            #     if host_image_path:
            #         await message.channel.send(file=discord.File(host_image_path))
            #         os.remove(host_image_path)# Remove the image file from the host system if needed
            #     # send the code file to the user
            #     await message.channel.send(file=discord.File(filename))
            #     set_bot_busy(conversation_id, False)
            #     os.remove(filename)# Remove the code file from the host system if needed
            
            elif (function_name == "generate_image" or function_name == "send_image"):
                function_arguments = json.loads(function_arguments)
                prompt = function_arguments.get("prompt")
                temp_message_text = random.choice(image_generation_messages).format(prompt)
                await edit_message_text(temp_message, temp_message_text)
                failed = False
                try:
                    image_url, _ = generate_images(prompt=prompt)

                    image_filename = f"{conversation_id} + {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.png"
                    await download_image(image_url, image_filename)
                    conversation.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": "Generated an image with the prompt: " + prompt + " and sent it to the user. Do not include a url in your response.",
                        }
                    )
                except openai.error.APIError as e:
                    error_message = str(e)
                    await edit_message_text(
                        temp_message,
                        f'An error occurred while generating the image. Please try again.',
                    )
                    print("Image generation failed. Error message:", error_message)
                    conversation.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": f"An error occurred while generating the image. Tell the user to try again with a different prompt. This is why it failed: {error_message}",
                        }
                    )
                    failed = True

                store_conversation(conversation_id, conversation)
                final_response = ""
                completion = ""
                response = generate_response(conversation)

                thread_safe_queue = thread_queue.Queue()
                threading.Thread(target=threaded_fetch, args=(response, thread_safe_queue, completion)).start()

                completion, temp_message = await send_to_discord(thread_safe_queue, 50, 2000, 0.3, temp_message, final_response, message)
                conversation.append(
                    {
                        "role": "assistant",
                        "content": completion[:2000],
                    }
                )
                store_conversation(conversation_id, conversation)
                completion = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', completion)
                await temp_message.edit(content=completion)
                if not failed:
                    await temp_message.channel.send(file=discord.File(image_filename))
                set_bot_busy(conversation_id, False)

    async def on_disconnect(self):
        self.change_status_task.cancel()
        print("Disconnected from Discord")
    
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
client = MyClient(intents=intents)
client.run(discord_token)  # type: ignore

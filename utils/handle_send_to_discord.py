from utils.store_conversation import store_conversation
# from bot import generate_response, threaded_fetch, send_to_discord
import queue as thread_queue
import threading
import re
import asyncio
import openai
import textwrap
from utils.exponential_backoff import exponential_backoff
import aiohttp
import aiofiles

def threaded_fetch(response, queue, completion):
    for chunk in response:
        new_content = chunk.choices[0].delta.get("content", "")
        if new_content:
            completion += new_content
            queue.put(new_content)
            # print("Added new content to queue:", new_content)
    print("Response generated from GPT-4!")
    queue.put(None)
    # print("Sentinel value added to queue.")
    return completion

async def send_to_discord(queue, min_chunk_size, max_chunk_size, delay, temp_message, final_response, message):
    async_queue = asyncio.Queue()
    full_response = ""
    is_first_chunk = True
    while True:
        # Check the queue and transfer any available content
        while not queue.empty():
            item = queue.get()
            await async_queue.put(item)

        # Try getting content from async queue with timeout to avoid blocking forever
        try:
            new_content = await asyncio.wait_for(async_queue.get(), timeout=3)
        except asyncio.TimeoutError:
            continue

        if new_content is None:  # If we've received the sentinel value, break the loop
            break

        full_response += new_content
        final_response += new_content

        while len(full_response) >= min_chunk_size:
            temp_message = await temp_message.channel.fetch_message(temp_message.id)
            current_content = full_response[:max_chunk_size]
            full_response = full_response[max_chunk_size:]

            if is_first_chunk:
                await temp_message.delete()
                current_content = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', current_content)
                temp_message = await message.channel.send(current_content)
                is_first_chunk = False
            else:
                current_content = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', current_content)
                # print(repr(current_content))
                await temp_message.edit(content=temp_message.content + current_content)
                # print("Chunked response" + repr(temp_message.content))

            await asyncio.sleep(delay)

    if full_response:  # for any remaining content
        temp_message = await temp_message.channel.fetch_message(temp_message.id)
        full_response = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', full_response)
        await temp_message.edit(content=temp_message.content + full_response)
        # print("Finished with full_response" + repr(temp_message.content))
        print("Finished with send_to_discord.")

    return final_response, temp_message

def generate_response(conversation):
    response = exponential_backoff(
        lambda model: openai.ChatCompletion.create(
        model=model,
        messages=conversation,
        stream=True,
        allow_fallback=True,
        ),
    )

    return response

async def update_conversation_and_send_to_discord(function_response, function_name, temp_message, conversation, conversation_id, message):
    conversation.append(
        {
            "role": "function",
            "name": function_name,
            "content": function_response,
        }
    )
    store_conversation(conversation_id, conversation)

    final_response = ""
    response = generate_response(conversation)

    thread_safe_queue = thread_queue.Queue()
    threading.Thread(target=threaded_fetch, args=(response, thread_safe_queue, "")).start()

    completion, temp_message = await send_to_discord(thread_safe_queue, 50, 2000, 0.3, temp_message, final_response, message)
    conversation.append(
        {
            "role": "assistant",
            "content": completion[:2000],
        }
    )
    store_conversation(conversation_id, conversation)

    completion = re.sub(r'\[([^\]]+)\]\((http[^)]+)\)', r'[\1](<\2>)', completion)
    await temp_message.edit(content=completion[:2000])
    # print("Full content:" + repr(temp_message.content))
from openai import AsyncOpenAI
from typing import AsyncIterator
from dotenv import load_dotenv
import os
import asyncio

TEST_TEXT = "Create an python code that says \"hello world\". But do not include any comments since I'm going to copy and paste every single letter on your response to the .py file.Don't use any Markdown or HTML tags. Just plain text. Thank you!"


async def fetch_response(prompt: str, model: str = "gpt-4o"):
    client = AsyncOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
    )

    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    all_content = ""

    async for chunk in stream:
        chunk_content = chunk.choices[0].delta.content
        if chunk_content is not None:
            all_content += chunk_content
            yield all_content


async def main(prompt: str):
    # generates a response
    output: str = ""
    async for content in fetch_response(prompt):
        print(content)
        output = content

    # creates a file
    with open("test.py", "w") as f:
        f.write(output)

    # executes the file
    os.system("python test.py")


load_dotenv()
# prompt_input = input("Enter any thing: ")
asyncio.run(main(TEST_TEXT))

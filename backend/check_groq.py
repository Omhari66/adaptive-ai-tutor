import asyncio
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv(".env")
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def test():
    try:
        response = await client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":"test"}],
        )
        print("Success:", response.choices[0].message.content)
    except Exception as e:
        print("Error:", str(e))

asyncio.run(test())

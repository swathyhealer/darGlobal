from openai import AsyncOpenAI


class LLMService:

    def __init__(self, api_key, base_url, model):

        self.model = model

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

    async def stream_response(self, messages):

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.2
        )

        async for chunk in stream:

            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if isinstance(content, str) and content:
                yield content
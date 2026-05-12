import asyncio
import httpx
API_KEY = "你的apikey"
BASE_URL = "https://api.minimaxi.com"
VOICE_DESIGN_PATH = "/v1/voice_design"


async def main():
    url = BASE_URL.rstrip("/") + VOICE_DESIGN_PATH

    payload = {
        "prompt": "成熟女性，声音温柔自然，普通话清晰。",
        "preview_text": "你好，这是一段声音设计的试听文本。"
    }

    print("url =", url)
    print("api_key_masked =", API_KEY[:8] + "..." + API_KEY[-6:] if API_KEY else None)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    print("http_status =", resp.status_code)
    print(resp.text[:2000])


if __name__ == "__main__":
    asyncio.run(main())
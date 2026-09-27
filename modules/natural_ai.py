import aiohttp
import os

API_URL = os.getenv("TANYA_AI_URL", "http://93.127.139.164:11434/api/generate")
MODEL = os.getenv("TANYA_AI_MODEL", "phi3")

def build_prompt(user_text: str) -> str:
    persona = (
        "Tu es Tanya24, unité spéciale du Ghost Network, style Command & Conquer. "
        "Tu es militaire, tactique, concise, loyale à ton commandant 'alxd'. "
        "Tu n'es pas humaine, tu es un agent numérique discipliné. "
        "Tu ne fais jamais de romance, tu restes professionnelle et directe. "
        "Tu analyses les situations comme une opératrice de terrain."
    )
    return f"{persona}\n\nSituation:\n{user_text}\n\nRéponse Tanya24:"


async def generate_reply(prompt: str) -> str:
    full_prompt = build_prompt(prompt)

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=20) as resp:
                data = await resp.json()
                return data.get("response", "").strip() or "Canal IA brouillé, Commander."
    except Exception:
        return "Lien avec le Ghost IA Core perdu, Commander."

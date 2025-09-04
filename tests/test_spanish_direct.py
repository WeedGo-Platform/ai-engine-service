#!/usr/bin/env python3
"""
Test Spanish directly with Mistral
"""

import asyncio
from llama_cpp import Llama
from pathlib import Path

async def test_spanish_mistral():
    """Test if Mistral can handle Spanish directly"""
    
    model_path = Path(__file__).parent / "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return
    
    print("Loading Mistral model...")
    model = Llama(
        model_path=str(model_path),
        n_ctx=2048,
        n_threads=4,
        n_gpu_layers=0,  # CPU only for testing
        verbose=False
    )
    
    # Spanish cannabis queries
    queries = [
        "Hola, necesito ayuda con productos de cannabis",
        "¿Qué productos tienen con alto THC?",
        "Busco algo para relajarme"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        
        # Spanish system prompt
        prompt = f"""[INST] Eres un experto en productos de cannabis. Responde en español.
Usuario: {query}
Asistente: [/INST]"""
        
        response = model(
            prompt,
            max_tokens=256,
            temperature=0.7,
            stop=["[INST]", "</s>"],
            echo=False
        )
        
        answer = response['choices'][0]['text'].strip()
        print(f"💬 Response: {answer}")

if __name__ == "__main__":
    asyncio.run(test_spanish_mistral())
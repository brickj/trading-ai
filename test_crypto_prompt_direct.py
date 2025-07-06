#!/usr/bin/env python3
"""
Test the new crypto prompt directly with Ollama
"""

import requests
import json

def test_crypto_prompt():
    """Test the new crypto prompt with a simple example"""
    
    # Sample crypto news for testing
    test_news = """
    Bitcoin price surges to new all-time high as institutional adoption increases.
    Major companies are now accepting Bitcoin as payment, driving mainstream adoption.
    However, regulatory concerns remain as governments consider stricter crypto regulations.
    Ethereum network upgrade shows promising results for scalability improvements.
    """
    
    # Use the new System Message Style prompt for cryptos
    system_prompt = (
        "You are a financial sentiment analyzer. You must respond with ONLY a JSON object containing "
        "sentiment_score (-1 to 1), confidence (0 to 1), and summary."
    )
    user_prompt = (
        f"Analyze the sentiment of this crypto news for BTCUSD:\n\n{test_news}\n\n"
        "Respond with ONLY this JSON format:\n"
        '{\n    "sentiment_score": 0.0,\n    "confidence": 0.0,\n    "summary": ""\n}'
    )
    
    print("🧪 Testing new crypto prompt with Ollama...")
    print(f"System prompt: {system_prompt}")
    print(f"User prompt: {user_prompt[:100]}...")
    
    try:
        # Send request to Ollama
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:latest",
            "prompt": f"<|system|>\n{system_prompt}\n</s>\n<|user|>\n{user_prompt}\n</s>\n<|assistant|>",
            "stream": False
        }
        
        print(f"📤 Sending prompt to Ollama...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result.get('response', '')
        
        print(f"📥 Ollama Response:")
        print(f"Length: {len(content)} characters")
        print(f"Content: {content}")
        
        # Try to parse as JSON
        try:
            # First try to parse as JSON directly
            try:
                parsed = json.loads(content)
                print(f"✅ SUCCESS: Parsed JSON directly: {parsed}")
                return True, parsed
            except json.JSONDecodeError:
                pass
            
            # If direct parsing fails, look for JSON in the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                print(f"✅ SUCCESS: Parsed JSON from regex: {parsed}")
                return True, parsed
            else:
                print(f"❌ FAILED: No JSON found in response")
                return False, content
                
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: JSON parsing error: {e}")
            return False, content
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, result = test_crypto_prompt()
    if success:
        print(f"\n🎉 Crypto prompt test PASSED!")
        print(f"Result: {result}")
    else:
        print(f"\n💥 Crypto prompt test FAILED!")
        print(f"Result: {result}") 
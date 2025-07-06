#!/usr/bin/env python3
"""
Test script to experiment with different Ollama prompts for crypto sentiment analysis
"""

import requests
import json
import time

def test_ollama_prompt(prompt, test_news, prompt_name):
    """Test a specific prompt with Ollama"""
    print(f"\n{'='*60}")
    print(f"Testing: {prompt_name}")
    print(f"{'='*60}")
    
    try:
        # Send request to Ollama
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:latest",
            "prompt": prompt,
            "stream": False
        }
        
        print(f"📤 Sending prompt to Ollama...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result.get('response', '')
        
        print(f"📥 Ollama Response:")
        print(f"Length: {len(content)} characters")
        print(f"Content: {content[:500]}...")
        
        # Try to parse as JSON
        try:
            # Look for JSON in the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                print(f"✅ SUCCESS: Parsed JSON: {parsed}")
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

def main():
    """Test different prompts for crypto sentiment analysis"""
    
    # Sample crypto news for testing
    test_news = """
    Bitcoin price surges to new all-time high as institutional adoption increases.
    Major companies are now accepting Bitcoin as payment, driving mainstream adoption.
    However, regulatory concerns remain as governments consider stricter crypto regulations.
    Ethereum network upgrade shows promising results for scalability improvements.
    """
    
    # Test different prompts
    prompts_to_test = [
        {
            "name": "Simple JSON Request",
            "prompt": f"""Analyze the sentiment of this crypto news and respond with ONLY a JSON object:

{test_news}

Respond with this exact JSON format:
{{
    "sentiment_score": 0.0,
    "confidence": 0.0,
    "summary": ""
}}"""
        },
        
        {
            "name": "Role-Based Prompt",
            "prompt": f"""You are a financial sentiment analyzer. Your job is to analyze crypto news sentiment.

News to analyze:
{test_news}

You must respond with ONLY a JSON object in this format:
{{
    "sentiment_score": 0.0,
    "confidence": 0.0,
    "summary": ""
}}

Do not include any other text."""
        },
        
        {
            "name": "System Message Style",
            "prompt": f"""<|system|>
You are a financial sentiment analyzer. You must respond with ONLY a JSON object containing sentiment_score (-1 to 1), confidence (0 to 1), and summary.
</s>
<|user|>
Analyze the sentiment of this crypto news:

{test_news}
</s>
<|assistant|>"""
        },
        
        {
            "name": "Direct Instruction",
            "prompt": f"""SENTIMENT ANALYSIS TASK

Input news:
{test_news}

INSTRUCTIONS:
1. Analyze the sentiment of the above crypto news
2. Respond with ONLY a JSON object
3. Use sentiment_score from -1 (very negative) to 1 (very positive)
4. Use confidence from 0 (low) to 1 (high)
5. Provide a brief summary

JSON RESPONSE:"""
        },
        
        {
            "name": "Minimal Prompt",
            "prompt": f"""News: {test_news}

JSON:"""
        },
        
        {
            "name": "Structured Analysis",
            "prompt": f"""Analyze the sentiment of this crypto news:

{test_news}

Provide your analysis in JSON format:
{{
    "sentiment_score": <number between -1 and 1>,
    "confidence": <number between 0 and 1>,
    "summary": "<brief description>"
}}"""
        }
    ]
    
    print("🧪 Testing Ollama Prompts for Crypto Sentiment Analysis")
    print("=" * 60)
    
    successful_prompts = []
    
    for prompt_data in prompts_to_test:
        success, result = test_ollama_prompt(
            prompt_data["prompt"], 
            test_news, 
            prompt_data["name"]
        )
        
        if success:
            successful_prompts.append({
                "name": prompt_data["name"],
                "prompt": prompt_data["prompt"],
                "result": result
            })
        
        time.sleep(2)  # Rate limiting
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total prompts tested: {len(prompts_to_test)}")
    print(f"Successful prompts: {len(successful_prompts)}")
    
    if successful_prompts:
        print(f"\n✅ WORKING PROMPTS:")
        for i, prompt_data in enumerate(successful_prompts, 1):
            print(f"\n{i}. {prompt_data['name']}")
            print(f"Result: {prompt_data['result']}")
            print(f"Prompt: {prompt_data['prompt'][:100]}...")
    else:
        print(f"\n❌ No working prompts found")
        print("Consider trying different Ollama models or prompt strategies")

if __name__ == "__main__":
    main() 
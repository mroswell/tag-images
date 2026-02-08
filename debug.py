import os
print(f"API Key loaded: {os.environ.get('ANTHROPIC_API_KEY') is not None}")
print(f"First 10 chars: {os.environ.get('ANTHROPIC_API_KEY', '')[:10]}")
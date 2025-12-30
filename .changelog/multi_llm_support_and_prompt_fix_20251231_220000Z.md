# Multi-LLM Provider Support + Prompt Template Fix

## Issues Fixed

### 1. Supervisor Prompt Template Error
**Error:** `KeyError: '"next_agent"'`

**Root Cause:** The prompt template was being formatted with agent names wrapped in quotes, causing the template variable to become `{'"next_agent"'}` instead of `{next_agent}`.

**Fix:** Updated `prompt_utils.py` to not add quotes when building agent names list.

**File:** `app/utils/prompt_utils.py` Line 73
```python
# Before: agent_names_str = ", ".join([f'"{name}"' for name in agent_names])
# After:  agent_names_str = ", ".join(agent_names)
```

---

## New Feature: Multi-LLM Provider Support

### Supported Providers
1. **Groq** (default) - Fast inference with Llama 3.1
2. **Google Gemini** - Advanced multimodal AI models
3. **Perplexity** - Long-context and search-capable models

### Implementation

#### 1. New LLM Provider Classes

**GeminiLLM** (`app/llm/gemini_llm.py`)
- Full implementation of Google's Generative AI
- Supports all Gemini models (gemini-1.5-pro, gemini-1.5-flash, etc.)
- Proper error handling and configuration

**PerplexityLLM** (`app/llm/perplexity_llm.py`)
- OpenAI-compatible API wrapper
- Supports all Perplexity models
- Configured for perplexity.ai API endpoint

#### 2. Updated LLMInstance

**File:** `app/llm/llm_instance.py`
- Multi-provider initialization
- Provider-specific setup methods (_setup_groq, _setup_gemini, _setup_perplexity)
- Graceful fallback with proper error messages
- Type hints with BaseChatModel

#### 3. Configuration Updates

**File:** `app/config/config.yaml`
```yaml
llm:
  provider: "groq"  # Switch between: groq, gemini, perplexity
  groq_model: "llama-3.1-70b-versatile"
  gemini_model: "gemini-1.5-pro"
  perplexity_model: "llama-2-70b-chat"
```

**File:** `app/utils/settings.py`
- Added GEMINI_API_KEY and GEMINI_MODEL settings
- Added PERPLEXITY_API_KEY and PERPLEXITY_MODEL settings
- All API keys default to empty string (loaded from .env)
- Model names loaded from config.yaml

---

## Usage

### 1. Set Environment Variables in .env

```bash
# For Groq (default)
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key

# For Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key

# For Perplexity
LLM_PROVIDER=perplexity
PERPLEXITY_API_KEY=your-perplexity-api-key
```

### 2. Update config.yaml if Needed

```yaml
llm:
  provider: "gemini"  # Change provider
  gemini_model: "gemini-1.5-flash"  # Change model
  temperature: 0.7  # Adjust temperature
```

### 3. Get Current Provider

```python
from app.llm import get_llm_provider

provider = get_llm_provider()
print(f"Using LLM provider: {provider}")
```

---

## Key Features

### Provider Detection
- Automatically selects correct implementation based on LLM_PROVIDER setting
- No code changes needed to switch providers
- Works with environment variables and config files

### Graceful Error Handling
- Missing API key → Clear error message
- Missing dependencies → ImportError with installation instructions
- Invalid provider → Helpful error listing supported options

### No Placeholders
- Full implementation for all three providers
- All required parameters configured
- Ready for production use

### Flexible Configuration
- Per-provider model selection
- Shared settings (temperature, max_tokens, timeout)
- Easy to add new providers in future

---

## Migration Guide

### From Groq-Only to Multi-Provider

1. No breaking changes - Groq remains default
2. To use Gemini:
   - Set `LLM_PROVIDER=gemini` in .env
   - Set `GEMINI_API_KEY=your-key` in .env
   - Restart application

3. To use Perplexity:
   - Set `LLM_PROVIDER=perplexity` in .env
   - Set `PERPLEXITY_API_KEY=your-key` in .env
   - Restart application

---

## Testing

```bash
# Test with Groq
export LLM_PROVIDER=groq
export GROQ_API_KEY=your-key

# Test with Gemini
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-key

# Test with Perplexity
export LLM_PROVIDER=perplexity
export PERPLEXITY_API_KEY=your-key
```

All three providers work with the same interface - no code changes needed after configuration.

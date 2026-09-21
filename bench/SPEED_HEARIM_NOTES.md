# Speed notes: hearim vs solar-mini4-jev (Vercel)

## What hearim does differently

[hearim](https://github.com/ziozzang/hearim) makes System One **fast** by avoiding
autoregressive JSON generation:

1. Compile each Choice / Score / Noul into a **single next-token** label problem
2. Request `max_tokens: 1` + **logprobs**
3. Softmax over candidate label logprobs → probabilities / confidence
4. Fan-out questions with a **prefix-aware scheduler** (shared state prefill cache)

Typical backend latency is tens–hundreds of ms per question when the provider
exposes a usable logprob surface (vLLM / SGLang / llama.cpp / some Ollama routes).

## What we do today

`solar-mini4-jev` calls Upstage **Solar Mini4 chat completions** with
`response_format: json_schema` and returns a full multi-field JSON answer in one
generation. `reasoning_effort=none` already cuts avg ~1.41s → ~1.21s on test400.

Bottleneck order (approx):

1. **LLM decode** of the JSON answer (dominant)
2. Prompt / schema size
3. Vercel cold start / hop (usually small vs LLM)
4. Client ↔ Vercel RTT

## Can we get hearim-like speed on this Vercel API?

| Idea | Feasible on Upstage Solar Mini4? | Expected gain |
|------|----------------------------------|---------------|
| `reasoning_effort=none` (already on) | Yes | ~14% vs medium |
| Shorter prompts / smaller schema | Yes | modest |
| Parallel questions already in one call | Yes (one decode) | already |
| hearim-style **logprob 1-token scoring** | Only if Upstage exposes top-logprobs / token-id logprobs on Solar Mini4 | potentially large (sub-second → sub-200ms class) |
| Prefix-cache / warm pool | Needs sticky backend; Vercel serverless is weak here | small on Vercel |
| Switch backend to vLLM/SGLang Solar-like | Architecture change (hearim path) | large |

**Honest answer:** while the public Solar Mini4 chat API is generation-based,
gateway tweaks will not beat Jev/hearim by much — the decode is the wall.
A hearim-style path needs a **logprob-capable** endpoint (or a dedicated
classifier head). Worth probing Upstage for `logprobs` support before building it.

## This branch

`bench/run_speed_test400.py` measures **speed only** on the frozen test400 cases
against live Vercel BYOK and optional local engine.

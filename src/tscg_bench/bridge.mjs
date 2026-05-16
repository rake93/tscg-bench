#!/usr/bin/env node
// Bridge from @tscg/core to Python. Reads JSON on stdin, writes JSON to stdout.
//
// Stdin:  {"schema": <openai-or-anthropic-tools-array>,
//          "profile": "balanced"|"aggressive"|"conservative"|"auto",
//          "model":   "claude-sonnet"|"claude-opus"|"gpt-4"|"gpt-5"|"phi-4"|"qwen-3"|"llama-3.1"|... }
// Stdout: {"compressed": <string>,
//          "stats": {"original_chars": int, "compressed_chars": int,
//                    "original_tokens": int, "compressed_tokens": int,
//                    "savings_pct": float, "ms": float,
//                    "profile": str, "model": str, "applied_principles": [str]}}

import { compress } from "@tscg/core";

function readStdin() {
  return new Promise((resolve, reject) => {
    let buf = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => { buf += chunk; });
    process.stdin.on("end", () => resolve(buf));
    process.stdin.on("error", reject);
  });
}

async function main() {
  const raw = await readStdin();
  if (!raw.trim()) {
    process.stderr.write("bridge: empty stdin\n");
    process.exit(2);
  }
  const req = JSON.parse(raw);
  const schema = req.schema;
  const profile = req.profile || "balanced";
  const model = req.model || "gpt-4";

  if (!Array.isArray(schema)) {
    process.stderr.write("bridge: schema must be an array of tool definitions\n");
    process.exit(2);
  }

  const result = compress(schema, { model, profile });
  const m = result.metrics;

  const out = {
    compressed: result.compressed,
    stats: {
      original_chars: m.characters.original,
      compressed_chars: m.characters.compressed,
      original_tokens: m.tokens.original,
      compressed_tokens: m.tokens.compressed,
      savings_pct: Number(m.tokens.savingsPercent.toFixed(2)),
      ms: Number(m.compressionTimeMs.toFixed(3)),
      profile,
      model,
      applied_principles: result.appliedPrinciples,
    },
  };
  process.stdout.write(JSON.stringify(out));
}

main().catch((e) => {
  process.stderr.write(`bridge: ${e.stack || e.message || e}\n`);
  process.exit(1);
});

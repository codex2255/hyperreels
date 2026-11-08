// ElevenLabs narration for a story Reel, with YOUR OWN ElevenLabs account.
//
//   npm run voice -- <spoken.txt> <out.mp3> <voiceId> [modelId]
//   npm run voices                      (lists the voices in your account: id, name, labels)
//
// (npm run voice = node --env-file=.env.local eleven_voice.mjs)
// The key is read from ELEVENLABS_API_KEY in .env.local (see .env.example). It never appears in code or output.
// The voice ID is required: choose a voice by ear in the ElevenLabs Voice Library, add it to your account, and pass
// its ID. Make spoken.txt with: python3 spoken.py props/<slug>.json > script/<slug>.spoken.txt
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream, readFileSync } from "fs";
import { Readable } from "stream";
import { finished } from "stream/promises";

const usage = "usage: npm run voice -- <spoken.txt> <out.mp3> <voiceId> [modelId]   |   npm run voices";
if (!process.env.ELEVENLABS_API_KEY) {
  console.error("No ELEVENLABS_API_KEY. Copy .env.example to .env.local and put your own key in it.");
  process.exit(1);
}
const client = new ElevenLabsClient();
const [a, out, voiceId, modelId = "eleven_v4"] = process.argv.slice(2);

if (a === "--list") {
  const r = await client.voices.search({ pageSize: 100 });
  for (const v of r.voices) console.log(`${v.voiceId}  ${v.name}  ${JSON.stringify(v.labels || {})}`);
  process.exit(0);
}
if (!a || !out || !voiceId) {
  console.error(usage);
  process.exit(1);
}
const text = readFileSync(a, "utf8").trim();
const audio = await client.textToSpeech.convert(voiceId, {
  text, modelId, outputFormat: "mp3_44100_128",
  voiceSettings: { stability: 0.4, similarityBoost: 0.75 },
  applyTextNormalization: "on",
});
await finished(Readable.fromWeb(audio).pipe(createWriteStream(out)));
console.log(`wrote ${out} (${text.length} chars, voice ${voiceId}, ${modelId})`);

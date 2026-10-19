#!/usr/bin/env node
import { resolveTheme } from "./theme.js";

interface GeneratorOptions {
  input: string;
  output: string;
  theme: string;
}

export function parseGeneratorArguments(argv: string[]): GeneratorOptions {
  const options = new Map<string, string>();

  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];

    if (!key || !value || !key.startsWith("--")) {
      throw new Error("Arguments must be supplied as --key value pairs.");
    }

    if (options.has(key)) {
      throw new Error(`Duplicate argument: ${key}`);
    }

    options.set(key, value);
  }

  const input = options.get("--input");
  const output = options.get("--output");
  const theme = options.get("--theme");

  if (!input || !output || !theme) {
    throw new Error("Missing required arguments: --input, --output, and --theme.");
  }

  if (!resolveTheme(theme)) {
    throw new Error(`Unknown theme: ${theme}`);
  }

  return { input, output, theme };
}

async function main(): Promise<void> {
  const options = parseGeneratorArguments(process.argv.slice(2));
  console.log(
    `Prepared to generate ${options.output} from ${options.input} using ${options.theme}.`,
  );
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});

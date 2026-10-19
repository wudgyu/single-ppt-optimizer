import { describe, expect, it } from "vitest";

import { parseGeneratorArguments } from "./index.js";

const validArguments = [
  "--input",
  "slide-plan.json",
  "--output",
  "candidate.pptx",
  "--theme",
  "professional_tech_dark",
];

describe("parseGeneratorArguments", () => {
  it("parses required arguments", () => {
    expect(parseGeneratorArguments(validArguments)).toEqual({
      input: "slide-plan.json",
      output: "candidate.pptx",
      theme: "professional_tech_dark",
    });
  });

  it("rejects missing arguments", () => {
    expect(() => parseGeneratorArguments(["--input", "slide-plan.json"])).toThrow(
      /Missing required arguments/,
    );
  });

  it("rejects unknown themes", () => {
    expect(() =>
      parseGeneratorArguments([
        "--input",
        "slide-plan.json",
        "--output",
        "candidate.pptx",
        "--theme",
        "unknown",
      ]),
    ).toThrow(/Unknown theme/);
  });
});

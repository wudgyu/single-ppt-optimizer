import Ajv2020Module from "ajv/dist/2020.js";
import { describe, expect, it } from "vitest";

import { commonSchema, contractsVersion } from "./index.js";

const Ajv2020 = Ajv2020Module.default;

describe("contract envelope schema", () => {
  it("accepts the supported schema version", () => {
    const validate = new Ajv2020({ allErrors: true }).compile(commonSchema);

    expect(validate({ schema_version: contractsVersion })).toBe(true);
  });

  it("rejects unsupported schema versions", () => {
    const validate = new Ajv2020({ allErrors: true }).compile(commonSchema);

    expect(validate({ schema_version: "0.9" })).toBe(false);
  });
});

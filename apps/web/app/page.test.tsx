import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("renders the primary heading", () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain("<h1>PPT Single-Slide Optimizer</h1>");
  });
});

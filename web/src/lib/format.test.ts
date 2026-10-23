import { describe, expect, it } from "vitest";

import {
  citationLabel,
  formatBytes,
  formatScore,
  formatWhen,
  isProbablyDocument,
  questionFromPoint,
  splitCitations,
} from "./format";

describe("formatBytes", () => {
  it("formats bytes, kilobytes, and megabytes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(1_500_000)).toBe("1.4 MB");
    expect(formatBytes(Number.NaN)).toBe("0 B");
  });
});

describe("formatWhen", () => {
  it("formats a UTC timestamp without shifting the day", () => {
    expect(formatWhen("2026-10-23T15:04:00Z", "UTC")).toBe("Oct 23, 2026");
  });

  it("returns the original string when the date is invalid", () => {
    expect(formatWhen("not-a-date")).toBe("not-a-date");
  });
});

describe("citations", () => {
  it("labels a passage and clamps the match percent", () => {
    expect(citationLabel(2)).toBe("Passage 2");
    expect(formatScore(0.823)).toBe("82% match");
    expect(formatScore(-0.2)).toBe("0% match");
    expect(formatScore(1.4)).toBe("100% match");
  });

  it("splits bracketed citation markers out of an answer", () => {
    expect(splitCitations("The code is Fjord-1842. [1]")).toEqual([
      { kind: "text", value: "The code is Fjord-1842. " },
      { kind: "cite", value: "[1]" },
    ]);
  });
});

describe("questionFromPoint", () => {
  it("turns a key point into a short grounded question", () => {
    expect(questionFromPoint("The on-call lead is Mina Solberg.")).toBe(
      "What does the document say about The on-call lead is Mina Solberg?",
    );
  });
});

describe("isProbablyDocument", () => {
  it("accepts a pdf or image and rejects a text file", () => {
    expect(isProbablyDocument({ name: "notes.pdf", type: "" })).toBe(true);
    expect(isProbablyDocument({ name: "image", type: "image/jpeg" })).toBe(true);
    expect(isProbablyDocument({ name: "notes.txt", type: "text/plain" })).toBe(false);
  });
});

import { afterEach, describe, expect, it } from "vitest";

import { apiBase, readError } from "./api";

describe("apiBase", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;

  afterEach(() => {
    if (original === undefined) delete process.env.NEXT_PUBLIC_API_URL;
    else process.env.NEXT_PUBLIC_API_URL = original;
  });

  it("drops a trailing slash", () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/";
    expect(apiBase()).toBe("http://localhost:8000");
  });

  it("defaults to the local API", () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(apiBase()).toBe("http://localhost:8000");
  });
});

describe("readError", () => {
  it("reads a string detail", async () => {
    const response = new Response(JSON.stringify({ detail: "Document not found." }), { status: 404 });
    await expect(readError(response)).resolves.toBe("Document not found.");
  });

  it("joins validation messages", async () => {
    const response = new Response(
      JSON.stringify({ detail: [{ msg: "Field required" }, { msg: "Too short" }] }),
      { status: 422 },
    );
    await expect(readError(response)).resolves.toBe("Field required Too short");
  });

  it("falls back when the body is not JSON", async () => {
    const response = new Response("nope", { status: 500 });
    await expect(readError(response)).resolves.toBe("Request failed (500).");
  });
});

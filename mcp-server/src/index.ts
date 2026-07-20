#!/usr/bin/env node
/**
 * ProM MCP Server
 * ─────────────────────────────────────────────────────────────────────────────
 * Exposes the five agentic tools as MCP tools that an agent client can
 * call during a conversation. The tools make HTTP calls to the FastAPI
 * backend running at PROM_API_URL (defaults to http://127.0.0.1:8000).
 *
 * Environment variables (set in mcp.json env block):
 *   PROM_API_URL        — Base URL of the FastAPI backend
 *   OPENAI_API_KEY      - Optional for tools that call OpenAI through the backend
 */

import { McpServer } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import { z } from "zod";

const API_BASE = process.env.PROM_API_URL ?? "http://127.0.0.1:8000";

// ── Shared fetch helper ───────────────────────────────────────────────────────
async function apiFetch(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Server setup ──────────────────────────────────────────────────────────────
const server = new McpServer({ name: "prom-mcp-server", version: "0.1.0" });

// ── Tool #1: stale_listing_check ──────────────────────────────────────────────
server.registerTool(
  "stale_listing_check",
  {
    description:
      "Checks whether an open seat has not been updated for a configurable number of days " +
      "and drafts a reconfirmation nudge message to send to the seat owner.",
    inputSchema: z.object({
      seat_id: z.string().describe("The unique ID of the open seat to inspect"),
      days_threshold: z
        .number()
        .int()
        .optional()
        .default(30)
        .describe("Number of days without update before a seat is considered stale"),
    }),
  },
  async ({ seat_id, days_threshold }) => {
    try {
      const result = await apiFetch("/api/agents/stale-check", {
        seat_id,
        days_threshold,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return {
        content: [{ type: "text", text: `stale_listing_check failed: ${String(err)}` }],
        isError: true,
      };
    }
  }
);

// ── Tool #2: mismatch_detector ────────────────────────────────────────────────
server.registerTool(
  "mismatch_detector",
  {
    description:
      "Detects whether an open seat listing is still posted but a candidate has already " +
      "been Selected or Confirmed internally, and returns an AI recommendation note.",
    inputSchema: z.object({
      seat_id: z.string().describe("The unique ID of the seat to cross-check"),
    }),
  },
  async ({ seat_id }) => {
    try {
      const result = await apiFetch("/api/agents/mismatch-check", { seat_id });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return {
        content: [{ type: "text", text: `mismatch_detector failed: ${String(err)}` }],
        isError: true,
      };
    }
  }
);

// ── Tool #3: draft_outreach_email ─────────────────────────────────────────────
server.registerTool(
  "draft_outreach_email",
  {
    description:
      "Drafts a personalised outreach email from a candidate to the project contact " +
      "based on the listing details and the candidate's background. " +
      "The draft is returned for the user to review and edit before sending via Outlook.",
    inputSchema: z.object({
      seat_id: z.string().describe("The seat the candidate is interested in"),
      candidate_professional_id: z
        .string()
        .describe("The professional ID of the candidate writing the email"),
    }),
  },
  async ({ seat_id, candidate_professional_id }) => {
    try {
      const result = await apiFetch("/api/agents/outreach-draft", {
        seat_id,
        candidate_professional_id,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return {
        content: [{ type: "text", text: `draft_outreach_email failed: ${String(err)}` }],
        isError: true,
      };
    }
  }
);

// ── Tool #4: get_recommendations ──────────────────────────────────────────────
server.registerTool(
  "get_recommendations",
  {
    description:
      "Returns AI-generated recommendations. " +
      "In candidate mode: recommends open seats for the professional based on their CV. " +
      "In owner mode: ranks applicants already in play for a specific seat_id by fit.",
    inputSchema: z.object({
      professional_id: z
        .string()
        .describe("The professional ID of the user requesting recommendations"),
      mode: z
        .enum(["candidate", "owner"])
        .optional()
        .default("candidate")
        .describe("'candidate' for seat recs, 'owner' for applicant ranking"),
      seat_id: z
        .string()
        .optional()
        .describe("Required for owner mode: the seat whose in-play applicants to rank"),
      cv_id: z
        .string()
        .optional()
        .describe("Optional CV id for candidate mode; defaults to the professional's default CV"),
      limit: z
        .number()
        .int()
        .optional()
        .default(5)
        .describe("Max recommendations to return"),
    }),
  },
  async ({ professional_id, mode, seat_id, cv_id, limit }) => {
    try {
      const body: Record<string, unknown> = {
        professional_id,
        mode,
        limit,
      };
      if (seat_id) body.seat_id = seat_id;
      if (cv_id) body.cv_id = cv_id;
      const result = await apiFetch("/api/agents/recommendations", body);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return {
        content: [{ type: "text", text: `get_recommendations failed: ${String(err)}` }],
        isError: true,
      };
    }
  }
);

// ── Tool #5: tailor_cv ────────────────────────────────────────────────────────
server.registerTool(
  "tailor_cv",
  {
    description:
      "Generates a tailored version of the candidate's CV specifically for the given open seat, " +
      "highlighting relevant experience and skills. Returns the tailored text and a summary of changes.",
    inputSchema: z.object({
      seat_id: z.string().describe("The seat to tailor the CV for"),
      professional_id: z
        .string()
        .describe("The professional ID whose CV should be tailored"),
    }),
  },
  async ({ seat_id, professional_id }) => {
    try {
      const result = await apiFetch("/api/agents/cv-tailor", {
        seat_id,
        professional_id,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return {
        content: [{ type: "text", text: `tailor_cv failed: ${String(err)}` }],
        isError: true,
      };
    }
  }
);

// ── Start ─────────────────────────────────────────────────────────────────────
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("prom-mcp-server running on stdio — API base:", API_BASE);
}

main().catch((err) => {
  console.error("Fatal error in prom-mcp-server:", err);
  process.exit(1);
});

import { describe, expect, it } from "vitest";
import { chmod, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import entry, { runRouter } from "./index.js";
import { getToolPluginMetadata } from "openclaw/plugin-sdk/tool-plugin";

describe("support-router", () => {
  it("declares the routing tool", () => {
    expect(getToolPluginMetadata(entry)?.tools.map((tool) => tool.name)).toEqual([
      "support_router_route_email",
    ]);
  });

  it("invokes a JSON stdin/stdout executable", async () => {
    const directory = await mkdtemp(join(tmpdir(), "support-router-plugin-"));
    const executable = join(directory, "router");
    await writeFile(
      executable,
      "#!/usr/bin/env node\nlet input='';process.stdin.on('data',c=>input+=c);process.stdin.on('end',()=>process.stdout.write(JSON.stringify({received:JSON.parse(input),routerEnv:Object.keys(process.env).filter(k=>k.startsWith('SUPPORT_ROUTER_')||k.startsWith('TYPESAFE_'))})));\n",
    );
    await chmod(executable, 0o700);
    try {
      const result = await runRouter(
        {
          message_id: "provider-1",
          sender: "customer@example.com",
          subject: "Duplicate charge",
          body_text: "Charged twice",
        },
        {
          executable,
          configFile: "/instance/teams.json",
          backend: "mock",
          apiToken: "12345",
        },
      );
      expect(result).toEqual({
        received: {
          message_id: "provider-1",
          sender: "customer@example.com",
          subject: "Duplicate charge",
          body_text: "Charged twice",
        },
        routerEnv: [],
      });
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("surfaces stderr when the router exits unsuccessfully", async () => {
    const directory = await mkdtemp(join(tmpdir(), "support-router-plugin-"));
    const executable = join(directory, "router");
    await writeFile(executable, "#!/bin/sh\necho 'invalid router config' >&2\nexit 2\n");
    await chmod(executable, 0o700);
    try {
      await expect(
        runRouter(
          {
            message_id: "provider-1",
            sender: "customer@example.com",
            subject: "Duplicate charge",
            body_text: "Charged twice",
          },
          { executable, configFile: "/instance/teams.json" },
        ),
      ).rejects.toThrow("invalid router config");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("rejects malformed router output", async () => {
    const directory = await mkdtemp(join(tmpdir(), "support-router-plugin-"));
    const executable = join(directory, "router");
    await writeFile(executable, "#!/bin/sh\nprintf 'not-json'\n");
    await chmod(executable, 0o700);
    try {
      await expect(
        runRouter(
          {
            message_id: "provider-1",
            sender: "customer@example.com",
            subject: "Duplicate charge",
            body_text: "Charged twice",
          },
          { executable, configFile: "/instance/teams.json" },
        ),
      ).rejects.toThrow();
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });
});

import { spawn } from "node:child_process";
import { Type } from "typebox";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";

const configSchema = Type.Object(
  {
    executable: Type.String({ description: "Absolute path to the support-router executable." }),
    configFile: Type.String({ description: "Absolute path to the instance team configuration." }),
    fixtureFile: Type.Optional(Type.String({ description: "Mock response fixture file." })),
    backend: Type.Optional(Type.Union([Type.Literal("mock"), Type.Literal("jev")])),
    apiToken: Type.Optional(Type.String()),
    timeoutMs: Type.Optional(Type.Integer({ minimum: 1, maximum: 120000 })),
  },
  { additionalProperties: false },
);

const emailSchema = Type.Object(
  {
    message_id: Type.String({ minLength: 1 }),
    sender: Type.String({ minLength: 1 }),
    subject: Type.String({ minLength: 1 }),
    body_text: Type.String({ minLength: 1 }),
    received_at: Type.Optional(Type.String({ minLength: 1 })),
  },
  { additionalProperties: false },
);

export default defineToolPlugin({
  id: "support-router",
  name: "Support Router",
  description: "Route an email through the installed provider-neutral Support Router core.",
  configSchema,
  tools: (tool) => [
    tool({
      name: "support_router_route_email",
      label: "Route Support Email",
      description: "Evaluate one already selected email and return its routing decision.",
      parameters: emailSchema,
      async execute(params, config, context) {
        context.signal?.throwIfAborted();
        return await runRouter(params, config, context.signal);
      },
    }),
  ],
});

type EmailInput = {
  message_id: string;
  sender: string;
  subject: string;
  body_text: string;
  received_at?: string;
};

type PluginConfig = {
  executable: string;
  configFile: string;
  fixtureFile?: string;
  backend?: "mock" | "jev";
  apiToken?: string;
  timeoutMs?: number;
};

export async function runRouter(
  input: EmailInput,
  config: PluginConfig,
  signal?: AbortSignal,
): Promise<unknown> {
  const env = {
    HOME: process.env.HOME,
    PATH: process.env.PATH,
  };
  const child = spawn(config.executable, [], {
    env,
    stdio: ["pipe", "pipe", "pipe"],
  });
  const stdout: Buffer[] = [];
  const stderr: Buffer[] = [];
  child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
  child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
  // A router that fails during startup may close stdin before Node flushes the
  // request. Its exit code and stderr below remain the authoritative error.
  child.stdin.on("error", () => undefined);
  child.stdin.end(JSON.stringify(input));

  const timeout = setTimeout(() => child.kill("SIGKILL"), config.timeoutMs ?? 30000);
  const abort = () => child.kill("SIGTERM");
  signal?.addEventListener("abort", abort, { once: true });
  try {
    const exitCode = await new Promise<number | null>((resolve, reject) => {
      child.once("error", reject);
      child.once("close", resolve);
    });
    const errorText = Buffer.concat(stderr).toString("utf8").trim();
    if (exitCode !== 0) {
      throw new Error(errorText || `support-router exited with code ${exitCode}`);
    }
    const output = Buffer.concat(stdout).toString("utf8");
    return JSON.parse(output);
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", abort);
  }
}

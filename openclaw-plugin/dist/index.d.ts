declare const _default: import("openclaw/plugin-sdk/tool-plugin").DefinedToolPluginEntry;
export default _default;
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
export declare function runRouter(input: EmailInput, config: PluginConfig, signal?: AbortSignal): Promise<unknown>;

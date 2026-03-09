import { MCPTool } from "mcp-framework";
import { BookstackClient, type HttpMethod, type BookstackRequestOptions } from "./BookstackClient.js";
import type { TagInput } from "./BookstackSchemas.js";
export type JsonValue = string | number | boolean | null | JsonObject | JsonArray;
export interface JsonObject {
    [key: string]: JsonValue;
}
export type JsonArray = JsonValue[];
export type ToolTextContent = {
    type: "text";
    text: string;
};
export type ToolErrorContent = {
    type: "error";
    text: string;
};
export type ToolContent = ToolTextContent | ToolErrorContent;
export interface BookstackToolExecuteOptions extends BookstackRequestOptions {
    method: HttpMethod;
    path: string;
}
export declare abstract class BookstackTool<TInput extends Record<string, unknown>> extends MCPTool<TInput> {
    protected readonly client: BookstackClient;
    constructor();
    protected callApi<T = unknown>({ method, path, ...options }: BookstackToolExecuteOptions): Promise<T>;
    protected getRequest<T = JsonValue>(path: string, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    protected postRequest<T = JsonValue>(path: string, body: unknown, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    protected putRequest<T = JsonValue>(path: string, body: unknown, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    protected deleteRequest<T = JsonValue>(path: string, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    protected runRequest(operation: () => Promise<JsonValue>): Promise<ToolContent[]>;
    protected formatTags(tags?: TagInput[]): TagInput[] | undefined;
    protected successContent(payload: JsonValue): ToolContent[];
    protected errorContent(message: string, details?: unknown): ToolContent[];
    protected mapError(error: unknown): ToolContent[];
    private stringify;
}

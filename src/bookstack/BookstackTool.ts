import { MCPTool } from "mcp-framework";
import {
  BookstackClient,
  BookstackApiError,
  type HttpMethod,
  type BookstackRequestOptions,
} from "./BookstackClient.js";
import type { TagInput } from "./BookstackSchemas.js";

export type JsonValue = string | number | boolean | null | JsonObject | JsonArray;
export interface JsonObject { [key: string]: JsonValue; }
export type JsonArray = JsonValue[];

export type ToolTextContent = { type: "text"; text: string };
export type ToolErrorContent = { type: "error"; text: string };
export type ToolContent = ToolTextContent | ToolErrorContent;

export interface BookstackToolExecuteOptions extends BookstackRequestOptions {
  method: HttpMethod;
  path: string;
}

export abstract class BookstackTool<TInput extends Record<string, unknown>> extends MCPTool<TInput> {
  protected readonly client: BookstackClient;

  constructor() {
    super();
    this.useStringify = false;
    this.client = BookstackClient.getInstance();
  }

  protected async callApi<T = unknown>({ method, path, ...options }: BookstackToolExecuteOptions): Promise<T> {
    const response = await this.client.request<T>(method, path, options);
    return response.data;
  }

  protected getRequest<T = JsonValue>(path: string, options: Omit<BookstackRequestOptions, "body"> = {}): Promise<T> {
    return this.client.get<T>(path, options);
  }

  protected postRequest<T = JsonValue>(
    path: string,
    body: unknown,
    options: Omit<BookstackRequestOptions, "body"> = {}
  ): Promise<T> {
    return this.client.post<T>(path, body, options);
  }

  protected putRequest<T = JsonValue>(
    path: string,
    body: unknown,
    options: Omit<BookstackRequestOptions, "body"> = {}
  ): Promise<T> {
    return this.client.put<T>(path, body, options);
  }

  protected deleteRequest<T = JsonValue>(
    path: string,
    options: Omit<BookstackRequestOptions, "body"> = {}
  ): Promise<T> {
    return this.client.delete<T>(path, options);
  }

  protected async runRequest(operation: () => Promise<JsonValue>): Promise<ToolContent[]> {
    try {
      const result = await operation();
      return this.successContent(result);
    } catch (error) {
      return this.mapError(error);
    }
  }

  protected formatTags(tags?: TagInput[]): TagInput[] | undefined {
    if (!tags) {
      return undefined;
    }

    return tags.map(tag => ({ name: tag.name, value: tag.value }));
  }

  protected successContent(payload: JsonValue): ToolContent[] {
    const text = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
    return [{ type: "text", text }];
  }

  protected errorContent(message: string, details?: unknown): ToolContent[] {
    const text = details ? `${message}\n${this.stringify(details)}` : message;
    return [{ type: "error", text }];
  }

  protected mapError(error: unknown): ToolContent[] {
    if (error instanceof BookstackApiError) {
      return this.errorContent(
        `Bookstack API error (status ${error.status})`,
        error.payload ?? error.message
      );
    }

    if (error instanceof Error) {
      return this.errorContent(`Bookstack tool failed: ${error.message}`);
    }

    return this.errorContent("Bookstack tool failed with unknown error", error);
  }

  private stringify(value: unknown): string {
    if (typeof value === "string") {
      return value;
    }

    try {
      return JSON.stringify(value, null, 2);
    } catch (error) {
      return String(value);
    }
  }
}


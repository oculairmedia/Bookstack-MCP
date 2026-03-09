import type { IncomingHttpHeaders } from "http";
export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
export interface BookstackRequestOptions {
    query?: Record<string, string | number | boolean | undefined>;
    body?: unknown;
    expectedStatuses?: number[];
    signal?: AbortSignal;
    timeoutMs?: number;
    headers?: Record<string, string | undefined>;
}
export interface BookstackResponse<T = unknown> {
    status: number;
    headers: IncomingHttpHeaders;
    data: T;
}
export declare class BookstackApiError<T = unknown> extends Error {
    readonly status: number;
    readonly payload: T;
    constructor(message: string, status: number, payload: T);
}
export declare class BookstackClient {
    private static instance;
    private readonly pool;
    private readonly basePath;
    private readonly defaultHeaders;
    private readonly origin;
    private constructor();
    static getInstance(): BookstackClient;
    request<T = unknown>(method: HttpMethod, path: string, options?: BookstackRequestOptions): Promise<BookstackResponse<T>>;
    get<T = unknown>(path: string, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    post<T = unknown>(path: string, body: unknown, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    put<T = unknown>(path: string, body: unknown, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    delete<T = unknown>(path: string, options?: Omit<BookstackRequestOptions, "body">): Promise<T>;
    private normalizePath;
    private createHeaders;
    private buildQueryString;
    private parseBody;
    private normalizeError;
    private isFormData;
    private requestWithFormData;
    private resolvePoolSize;
    private resolveBodyTimeout;
    private resolveHeadersTimeout;
    private consumeBody;
    private resolveTlsOptions;
    private parseBoolean;
    private readPemEntries;
}
export type BookstackClientType = BookstackClient;

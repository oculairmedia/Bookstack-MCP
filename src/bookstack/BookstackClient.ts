import { Pool, errors as undiciErrors } from "undici";
import type { IncomingHttpHeaders } from "http";

export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

export interface BookstackRequestOptions {
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  expectedStatuses?: number[];
  signal?: AbortSignal;
  timeoutMs?: number;
}

export interface BookstackResponse<T = unknown> {
  status: number;
  headers: IncomingHttpHeaders;
  data: T;
}

export class BookstackApiError<T = unknown> extends Error {
  public readonly status: number;
  public readonly payload: T;

  constructor(message: string, status: number, payload: T) {
    super(message);
    this.name = "BookstackApiError";
    this.status = status;
    this.payload = payload;
  }
}

const DEFAULT_TIMEOUT = 30_000;
const DEFAULT_POOL_CONNECTIONS = 10;

export class BookstackClient {
  private static instance: BookstackClient | null = null;

  private readonly pool: Pool;
  private readonly basePath: string;
  private readonly defaultHeaders: Record<string, string>;

  private constructor() {
    const baseUrl = (process.env.BS_URL || "https://knowledge.oculair.ca").trim();
    const tokenId = process.env.BS_TOKEN_ID;
    const tokenSecret = process.env.BS_TOKEN_SECRET;

    if (!tokenId || !tokenSecret) {
      throw new Error("BS_TOKEN_ID and BS_TOKEN_SECRET must be configured in the environment.");
    }

    let parsed: URL;
    try {
      parsed = new URL(baseUrl);
    } catch (error) {
      throw new Error(`Invalid BS_URL value: ${baseUrl}`);
    }

    const origin = `${parsed.protocol}//${parsed.host}`;
    this.basePath = parsed.pathname === "/" ? "" : parsed.pathname.replace(/\/$/, "");

    this.pool = new Pool(origin, {
      connections: this.resolvePoolSize(),
      pipelining: 1,
      keepAliveTimeout: 30_000,
      keepAliveMaxTimeout: 60_000,
      connectTimeout: DEFAULT_TIMEOUT,
    });

    this.defaultHeaders = {
      Authorization: `Token ${tokenId}:${tokenSecret}`,
      Accept: "application/json",
    };
  }

  public static getInstance(): BookstackClient {
    if (!this.instance) {
      this.instance = new BookstackClient();
    }
    return this.instance;
  }

  public async request<T = unknown>(method: HttpMethod, path: string, options: BookstackRequestOptions = {}): Promise<BookstackResponse<T>> {
    const cleanPath = this.normalizePath(path);
    const queryString = this.buildQueryString(options.query);
    const fullPath = `${cleanPath}${queryString}`;

    const headers: Record<string, string> = { ...this.defaultHeaders };
    let body: string | undefined;
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }

    const timeout = options.timeoutMs ?? DEFAULT_TIMEOUT;
    const signal = options.signal ?? AbortSignal.timeout(timeout);

    try {
      const { statusCode, headers: responseHeaders, body: responseBody } = await this.pool.request({
        method,
        path: fullPath,
        headers,
        body,
        signal,
      });

      const text = await responseBody.text();
      const data = this.parseBody(text) as T;
      const expected = options.expectedStatuses ?? [200];

      if (!expected.includes(statusCode)) {
        throw new BookstackApiError(`Unexpected status code ${statusCode}`, statusCode, data);
      }

      return {
        status: statusCode,
        headers: responseHeaders,
        data,
      };
    } catch (error) {
      throw this.normalizeError(error);
    }
  }

  public async get<T = unknown>(path: string, options: Omit<BookstackRequestOptions, "body"> = {}): Promise<T> {
    const response = await this.request<T>("GET", path, options);
    return response.data;
  }

  public async post<T = unknown>(
    path: string,
    body: unknown,
    options: Omit<BookstackRequestOptions, "body"> = {}
  ): Promise<T> {
    const response = await this.request<T>("POST", path, {
      ...options,
      body,
      expectedStatuses: options.expectedStatuses ?? [200, 201],
    });
    return response.data;
  }

  public async put<T = unknown>(
    path: string,
    body: unknown,
    options: Omit<BookstackRequestOptions, "body"> = {}
  ): Promise<T> {
    const response = await this.request<T>("PUT", path, {
      ...options,
      body,
      expectedStatuses: options.expectedStatuses ?? [200],
    });
    return response.data;
  }

  public async delete<T = unknown>(
    path: string,
    options: Omit<BookstackRequestOptions, "body"> = {}
  ): Promise<T> {
    const response = await this.request<T>("DELETE", path, {
      ...options,
      expectedStatuses: options.expectedStatuses ?? [204, 200],
    });
    return response.data;
  }

  private normalizePath(path: string): string {
    const trimmed = path.startsWith("/") ? path : `/${path}`;
    return `${this.basePath}${trimmed}` || "/";
  }

  private buildQueryString(query?: Record<string, string | number | boolean | undefined>): string {
    if (!query) {
      return "";
    }

    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null) {
        continue;
      }
      searchParams.append(key, String(value));
    }

    const serialized = searchParams.toString();
    return serialized ? `?${serialized}` : "";
  }

  private parseBody(payload: string): unknown {
    if (!payload) {
      return null;
    }

    try {
      return JSON.parse(payload);
    } catch (error) {
      return payload;
    }
  }

  private normalizeError(error: unknown): Error {
    if (error instanceof BookstackApiError) {
      return error;
    }

    if (error instanceof undiciErrors.UndiciError) {
      return new Error(`Bookstack request failed: ${error.message}`);
    }

    if (error instanceof Error) {
      return error;
    }

    return new Error(`Unknown error: ${String(error)}`);
  }

  private resolvePoolSize(): number {
    const raw = process.env.BS_POOL_SIZE;
    if (!raw) {
      return DEFAULT_POOL_CONNECTIONS;
    }

    const parsed = Number.parseInt(raw, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_POOL_CONNECTIONS;
  }
}

export type BookstackClientType = BookstackClient;


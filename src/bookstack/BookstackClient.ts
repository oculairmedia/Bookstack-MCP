import { Pool, errors as undiciErrors } from "undici";
import type { IncomingHttpHeaders } from "http";
import { readFileSync } from "node:fs";
import { resolve as resolvePath, delimiter as pathDelimiter } from "node:path";
import type { ConnectionOptions } from "node:tls";

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
  private readonly origin: string;

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
    this.origin = origin;
    this.basePath = parsed.pathname === "/" ? "" : parsed.pathname.replace(/\/$/, "");

    const poolOptions = {
      connections: this.resolvePoolSize(),
      pipelining: 1,
      keepAliveTimeout: 30_000,
      keepAliveMaxTimeout: 60_000,
      connectTimeout: DEFAULT_TIMEOUT,
      bodyTimeout: this.resolveBodyTimeout(),
      headersTimeout: this.resolveHeadersTimeout(),
    } as Pool.Options;

    const tlsOptions = this.resolveTlsOptions(parsed);
    if (tlsOptions) {
      poolOptions.connect = tlsOptions;
    }

    this.pool = new Pool(origin, poolOptions);

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

    const headers = this.createHeaders(options.headers);
    const expected = options.expectedStatuses ?? [200];
    const timeout = options.timeoutMs ?? DEFAULT_TIMEOUT;
    const signal = options.signal ?? AbortSignal.timeout(timeout);

    if (options.body !== undefined && options.body !== null) {
      if (this.isFormData(options.body)) {
        return this.requestWithFormData<T>({
          method,
          fullPath,
          headers,
          formData: options.body,
          signal,
          expected,
        });
      }
    }

    let body: string | undefined;
    if (options.body !== undefined && options.body !== null) {
      if (typeof options.body === "string") {
        body = options.body;
      } else {
        body = JSON.stringify(options.body);
      }

      if (!headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
      }
    }

    try {
      const { statusCode, headers: responseHeaders, body: responseBody } = await this.pool.request({
        method,
        path: fullPath,
        headers,
        body,
        signal,
      });

      const text = await this.consumeBody(responseBody, method, fullPath);
      const data = this.parseBody(text) as T;

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

  private createHeaders(additional?: Record<string, string | undefined>): Record<string, string> {
    const headers: Record<string, string> = { ...this.defaultHeaders };

    if (additional) {
      for (const [key, value] of Object.entries(additional)) {
        if (value !== undefined) {
          headers[key] = value;
        }
      }
    }

    return headers;
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
      const cause = (error as Error & { cause?: unknown }).cause;
      const undiciMessage = [error.message, cause ? `cause=${String(cause)}` : ""].filter(Boolean).join(" ");
      return new Error(`Bookstack request failed: ${undiciMessage}`);
    }

    if (error instanceof Error) {
      return error;
    }

    return new Error(`Unknown error: ${String(error)}`);
  }

  private isFormData(value: unknown): value is FormData {
    if (typeof FormData === "undefined") {
      return false;
    }

    return value instanceof FormData;
  }

  private async requestWithFormData<T>({
    method,
    fullPath,
    headers,
    formData,
    signal,
    expected,
  }: {
    method: HttpMethod;
    fullPath: string;
    headers: Record<string, string>;
    formData: FormData;
    signal: AbortSignal;
    expected: number[];
  }): Promise<BookstackResponse<T>> {
    const url = `${this.origin}${fullPath}`;

    const fetchHeaders = new Headers();
    for (const [key, value] of Object.entries(headers)) {
      if (key.toLowerCase() === "content-type") {
        continue;
      }

      fetchHeaders.set(key, value);
    }

    try {
      const response = await fetch(url, {
        method,
        headers: fetchHeaders,
        body: formData as unknown as BodyInit,
        signal,
      });

      const text = await response.text();
      const data = this.parseBody(text) as T;

      if (!expected.includes(response.status)) {
        throw new BookstackApiError(`Unexpected status code ${response.status}`, response.status, data);
      }

      const responseHeaders: IncomingHttpHeaders = {};
      response.headers.forEach((value, key) => {
        if (responseHeaders[key]) {
          const existing = responseHeaders[key];
          responseHeaders[key] = Array.isArray(existing)
            ? [...existing, value]
            : [existing as string, value];
        } else {
          responseHeaders[key] = value;
        }
      });

      return {
        status: response.status,
        headers: responseHeaders,
        data,
      };
    } catch (error) {
      throw this.normalizeError(error);
    }
  }

  private resolvePoolSize(): number {
    const raw = process.env.BS_POOL_SIZE;
    if (!raw) {
      return DEFAULT_POOL_CONNECTIONS;
    }

    const parsed = Number.parseInt(raw, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_POOL_CONNECTIONS;
  }

  private resolveBodyTimeout(): number {
    const raw = process.env.BS_BODY_TIMEOUT_MS;
    if (!raw) {
      return DEFAULT_TIMEOUT;
    }

    const parsed = Number.parseInt(raw, 10);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : DEFAULT_TIMEOUT;
  }

  private resolveHeadersTimeout(): number | undefined {
    const raw = process.env.BS_HEADERS_TIMEOUT_MS;
    if (!raw) {
      return undefined;
    }

    const parsed = Number.parseInt(raw, 10);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
  }

  private async consumeBody(
    responseBody: unknown,
    method: string,
    path: string,
  ): Promise<string> {
    if (!responseBody || typeof (responseBody as { text?: unknown }).text !== "function") {
      return "";
    }

    try {
      return await (responseBody as { text: () => Promise<string> }).text();
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      console.warn(
        `Failed to read response body for ${method.toUpperCase()} ${path}: ${reason}`,
        error instanceof Error && error.stack ? `\n${error.stack}` : ""
      );

      try {
        const maybeBody = responseBody as { cancel?: () => Promise<void>; resume?: () => void };
        if (typeof maybeBody.cancel === "function") {
          await maybeBody.cancel();
        } else if (typeof maybeBody.resume === "function") {
          maybeBody.resume();
        }
      } catch (cancelError) {
        console.warn(
          `Failed to discard response body for ${method.toUpperCase()} ${path}: ${cancelError instanceof Error ? cancelError.message : cancelError}`
        );
      }

      return "";
    }
  }

  private resolveTlsOptions(parsedUrl: URL): ConnectionOptions | undefined {
    if (parsedUrl.protocol !== "https:") {
      return undefined;
    }

    const options: ConnectionOptions = {};
    let hasOption = false;

    const rejectUnauthorizedEnv = process.env.BS_TLS_REJECT_UNAUTHORIZED;
    if (rejectUnauthorizedEnv !== undefined) {
      options.rejectUnauthorized = this.parseBoolean(rejectUnauthorizedEnv, true);
      hasOption = true;
    }

    const ca = this.readPemEntries(process.env.BS_TLS_CA_FILE ?? process.env.BS_TLS_CA_FILES);
    if (ca) {
      options.ca = ca;
      hasOption = true;
    }

    const cert = this.readPemEntries(process.env.BS_TLS_CERT_FILE);
    if (cert) {
      options.cert = cert;
      hasOption = true;
    }

    const key = this.readPemEntries(process.env.BS_TLS_KEY_FILE);
    if (key) {
      options.key = key;
      hasOption = true;
    }

    const passphrase = process.env.BS_TLS_PASSPHRASE;
    if (passphrase) {
      options.passphrase = passphrase;
      hasOption = true;
    }

    const minVersion = process.env.BS_TLS_MIN_VERSION;
    if (minVersion) {
      options.minVersion = minVersion as ConnectionOptions["minVersion"];
      hasOption = true;
    }

    const maxVersion = process.env.BS_TLS_MAX_VERSION;
    if (maxVersion) {
      options.maxVersion = maxVersion as ConnectionOptions["maxVersion"];
      hasOption = true;
    }

    const servername = process.env.BS_TLS_SERVERNAME;
    if (servername) {
      options.servername = servername;
      hasOption = true;
    }

    if (!hasOption) {
      return undefined;
    }

    return options;
  }

  private parseBoolean(value: string, fallback: boolean): boolean {
    const normalized = value.trim().toLowerCase();
    if (["1", "true", "yes", "on"].includes(normalized)) {
      return true;
    }
    if (["0", "false", "no", "off"].includes(normalized)) {
      return false;
    }
    return fallback;
  }

  private readPemEntries(source?: string): string | string[] | undefined {
    if (!source) {
      return undefined;
    }

    const paths = source
      .split(pathDelimiter)
      .map((entry) => entry.trim())
      .filter(Boolean);

    if (!paths.length) {
      return undefined;
    }

    const contents = paths.map((entry) => {
      const absolute = resolvePath(entry);
      try {
        return readFileSync(absolute, "utf8");
      } catch (error) {
        const cause = error instanceof Error ? error.message : String(error);
        throw new Error(`Failed to read TLS material from ${absolute}: ${cause}`);
      }
    });

    return contents.length === 1 ? contents[0] : contents;
  }
}

export type BookstackClientType = BookstackClient;

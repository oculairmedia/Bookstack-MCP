import { Pool, errors as undiciErrors } from "undici";
import { readFileSync } from "node:fs";
import { resolve as resolvePath, delimiter as pathDelimiter } from "node:path";
export class BookstackApiError extends Error {
    constructor(message, status, payload) {
        super(message);
        this.name = "BookstackApiError";
        this.status = status;
        this.payload = payload;
    }
}
const DEFAULT_TIMEOUT = 30000;
const DEFAULT_POOL_CONNECTIONS = 10;
export class BookstackClient {
    constructor() {
        const baseUrl = (process.env.BS_URL || "http://192.168.50.80:8087").trim();
        const tokenId = process.env.BS_TOKEN_ID;
        const tokenSecret = process.env.BS_TOKEN_SECRET;
        if (!tokenId || !tokenSecret) {
            throw new Error("BS_TOKEN_ID and BS_TOKEN_SECRET must be configured in the environment.");
        }
        let parsed;
        try {
            parsed = new URL(baseUrl);
        }
        catch (error) {
            throw new Error(`Invalid BS_URL value: ${baseUrl}`);
        }
        const origin = `${parsed.protocol}//${parsed.host}`;
        this.origin = origin;
        this.basePath = parsed.pathname === "/" ? "" : parsed.pathname.replace(/\/$/, "");
        const poolOptions = {
            connections: this.resolvePoolSize(),
            pipelining: 1,
            keepAliveTimeout: 30000,
            keepAliveMaxTimeout: 60000,
            connectTimeout: DEFAULT_TIMEOUT,
            bodyTimeout: this.resolveBodyTimeout(),
            headersTimeout: this.resolveHeadersTimeout(),
        };
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
    static getInstance() {
        if (!this.instance) {
            this.instance = new BookstackClient();
        }
        return this.instance;
    }
    async request(method, path, options = {}) {
        const cleanPath = this.normalizePath(path);
        const queryString = this.buildQueryString(options.query);
        const fullPath = `${cleanPath}${queryString}`;
        const headers = this.createHeaders(options.headers);
        const expected = options.expectedStatuses ?? [200];
        const timeout = options.timeoutMs ?? DEFAULT_TIMEOUT;
        const signal = options.signal ?? AbortSignal.timeout(timeout);
        if (options.body !== undefined && options.body !== null) {
            if (this.isFormData(options.body)) {
                return this.requestWithFormData({
                    method,
                    fullPath,
                    headers,
                    formData: options.body,
                    signal,
                    expected,
                });
            }
        }
        let body;
        if (options.body !== undefined && options.body !== null) {
            if (typeof options.body === "string") {
                body = options.body;
            }
            else {
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
            const data = this.parseBody(text);
            if (!expected.includes(statusCode)) {
                throw new BookstackApiError(`Unexpected status code ${statusCode}`, statusCode, data);
            }
            return {
                status: statusCode,
                headers: responseHeaders,
                data,
            };
        }
        catch (error) {
            throw this.normalizeError(error);
        }
    }
    async get(path, options = {}) {
        const response = await this.request("GET", path, options);
        return response.data;
    }
    async post(path, body, options = {}) {
        const response = await this.request("POST", path, {
            ...options,
            body,
            expectedStatuses: options.expectedStatuses ?? [200, 201],
        });
        return response.data;
    }
    async put(path, body, options = {}) {
        const response = await this.request("PUT", path, {
            ...options,
            body,
            expectedStatuses: options.expectedStatuses ?? [200],
        });
        return response.data;
    }
    async delete(path, options = {}) {
        const response = await this.request("DELETE", path, {
            ...options,
            expectedStatuses: options.expectedStatuses ?? [204, 200],
        });
        return response.data;
    }
    normalizePath(path) {
        const trimmed = path.startsWith("/") ? path : `/${path}`;
        return `${this.basePath}${trimmed}` || "/";
    }
    createHeaders(additional) {
        const headers = { ...this.defaultHeaders };
        if (additional) {
            for (const [key, value] of Object.entries(additional)) {
                if (value !== undefined) {
                    headers[key] = value;
                }
            }
        }
        return headers;
    }
    buildQueryString(query) {
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
    parseBody(payload) {
        if (!payload) {
            return null;
        }
        try {
            return JSON.parse(payload);
        }
        catch (error) {
            return payload;
        }
    }
    normalizeError(error) {
        if (error instanceof BookstackApiError) {
            return error;
        }
        if (error instanceof undiciErrors.UndiciError) {
            const cause = error.cause;
            const undiciMessage = [error.message, cause ? `cause=${String(cause)}` : ""].filter(Boolean).join(" ");
            return new Error(`Bookstack request failed: ${undiciMessage}`);
        }
        if (error instanceof Error) {
            return error;
        }
        return new Error(`Unknown error: ${String(error)}`);
    }
    isFormData(value) {
        if (typeof FormData === "undefined") {
            return false;
        }
        return value instanceof FormData;
    }
    async requestWithFormData({ method, fullPath, headers, formData, signal, expected, }) {
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
                body: formData,
                signal,
            });
            const text = await response.text();
            const data = this.parseBody(text);
            if (!expected.includes(response.status)) {
                throw new BookstackApiError(`Unexpected status code ${response.status}`, response.status, data);
            }
            const responseHeaders = {};
            response.headers.forEach((value, key) => {
                if (responseHeaders[key]) {
                    const existing = responseHeaders[key];
                    responseHeaders[key] = Array.isArray(existing)
                        ? [...existing, value]
                        : [existing, value];
                }
                else {
                    responseHeaders[key] = value;
                }
            });
            return {
                status: response.status,
                headers: responseHeaders,
                data,
            };
        }
        catch (error) {
            throw this.normalizeError(error);
        }
    }
    resolvePoolSize() {
        const raw = process.env.BS_POOL_SIZE;
        if (!raw) {
            return DEFAULT_POOL_CONNECTIONS;
        }
        const parsed = Number.parseInt(raw, 10);
        return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_POOL_CONNECTIONS;
    }
    resolveBodyTimeout() {
        const raw = process.env.BS_BODY_TIMEOUT_MS;
        if (!raw) {
            return DEFAULT_TIMEOUT;
        }
        const parsed = Number.parseInt(raw, 10);
        return Number.isFinite(parsed) && parsed >= 0 ? parsed : DEFAULT_TIMEOUT;
    }
    resolveHeadersTimeout() {
        const raw = process.env.BS_HEADERS_TIMEOUT_MS;
        if (!raw) {
            return undefined;
        }
        const parsed = Number.parseInt(raw, 10);
        return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
    }
    async consumeBody(responseBody, method, path) {
        if (!responseBody || typeof responseBody.text !== "function") {
            return "";
        }
        try {
            return await responseBody.text();
        }
        catch (error) {
            const reason = error instanceof Error ? error.message : String(error);
            console.warn(`Failed to read response body for ${method.toUpperCase()} ${path}: ${reason}`, error instanceof Error && error.stack ? `\n${error.stack}` : "");
            try {
                const maybeBody = responseBody;
                if (typeof maybeBody.cancel === "function") {
                    await maybeBody.cancel();
                }
                else if (typeof maybeBody.resume === "function") {
                    maybeBody.resume();
                }
            }
            catch (cancelError) {
                console.warn(`Failed to discard response body for ${method.toUpperCase()} ${path}: ${cancelError instanceof Error ? cancelError.message : cancelError}`);
            }
            return "";
        }
    }
    resolveTlsOptions(parsedUrl) {
        if (parsedUrl.protocol !== "https:") {
            return undefined;
        }
        const options = {};
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
            options.minVersion = minVersion;
            hasOption = true;
        }
        const maxVersion = process.env.BS_TLS_MAX_VERSION;
        if (maxVersion) {
            options.maxVersion = maxVersion;
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
    parseBoolean(value, fallback) {
        const normalized = value.trim().toLowerCase();
        if (["1", "true", "yes", "on"].includes(normalized)) {
            return true;
        }
        if (["0", "false", "no", "off"].includes(normalized)) {
            return false;
        }
        return fallback;
    }
    readPemEntries(source) {
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
            }
            catch (error) {
                const cause = error instanceof Error ? error.message : String(error);
                throw new Error(`Failed to read TLS material from ${absolute}: ${cause}`);
            }
        });
        return contents.length === 1 ? contents[0] : contents;
    }
}
BookstackClient.instance = null;

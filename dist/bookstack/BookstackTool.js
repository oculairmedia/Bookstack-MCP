import { MCPTool } from "mcp-framework";
import { BookstackClient, BookstackApiError, } from "./BookstackClient.js";
export class BookstackTool extends MCPTool {
    constructor() {
        super();
        this.useStringify = false;
        this.client = BookstackClient.getInstance();
    }
    async callApi({ method, path, ...options }) {
        const response = await this.client.request(method, path, options);
        return response.data;
    }
    getRequest(path, options = {}) {
        return this.client.get(path, options);
    }
    postRequest(path, body, options = {}) {
        return this.client.post(path, body, options);
    }
    putRequest(path, body, options = {}) {
        return this.client.put(path, body, options);
    }
    deleteRequest(path, options = {}) {
        return this.client.delete(path, options);
    }
    async runRequest(operation) {
        try {
            const result = await operation();
            return this.successContent(result);
        }
        catch (error) {
            return this.mapError(error);
        }
    }
    formatTags(tags) {
        if (!tags) {
            return undefined;
        }
        return tags.map(tag => ({ name: tag.name, value: tag.value }));
    }
    successContent(payload) {
        const text = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
        return [{ type: "text", text }];
    }
    errorContent(message, details) {
        const text = details ? `${message}\n${this.stringify(details)}` : message;
        return [{ type: "error", text }];
    }
    mapError(error) {
        if (error instanceof BookstackApiError) {
            return this.errorContent(`Bookstack API error (status ${error.status})`, error.payload ?? error.message);
        }
        if (error instanceof Error) {
            return this.errorContent(`Bookstack tool failed: ${error.message}`);
        }
        return this.errorContent("Bookstack tool failed with unknown error", error);
    }
    stringify(value) {
        if (typeof value === "string") {
            return value;
        }
        try {
            return JSON.stringify(value, null, 2);
        }
        catch (error) {
            return String(value);
        }
    }
}

import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
import { imageInputSchema, prepareImagePayload, } from "../bookstack/ImageUtils.js";
import { normalizeImageListResponse, } from "./utils/imageResponses.js";
const LIST_CACHE_TTL_MS = 30000;
const filtersSchema = z
    .array(z.object({
    key: z
        .string()
        .min(1)
        .describe("Filter key forwarded to BookStack as filter[<key>]"),
    value: z
        .string()
        .describe("Filter value forwarded to BookStack"),
}).describe("Filter entry"))
    .describe("Collection of filters forwarded to BookStack as filter[<key>] parameters")
    .optional();
const schema = z.object({
    operation: z
        .enum(["create", "read", "update", "delete", "list"])
        .describe("Image workflow operation to execute"),
    name: z
        .string()
        .min(1)
        .optional()
        .describe("Display name for the stored image (required for create)"),
    image: imageInputSchema
        .optional()
        .describe("Image payload as a base64 string or data URL for create/update operations"),
    id: createIdSchema("Image ID used by read/update/delete operations").optional(),
    new_name: z
        .string()
        .min(1)
        .optional()
        .describe("Replacement image name for update operations"),
    new_image: imageInputSchema
        .optional()
        .describe("Replacement image payload as base64 string or data URL"),
    offset: z
        .number()
        .int()
        .min(0)
        .optional()
        .describe("Number of records to skip when listing images"),
    count: z
        .number()
        .int()
        .min(1)
        .max(100)
        .optional()
        .describe("Number of records to return when listing images"),
    sort: z
        .string()
        .optional()
        .describe("Sort expression understood by BookStack (e.g. '-created_at')"),
    filters: filtersSchema,
});
class BookstackManageImagesTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_manage_images";
        this.description = "Unified CRUD interface for BookStack image gallery";
        this.schema = schema;
    }
    async execute(input) {
        if (input.operation === "create") {
            if (!input.name) {
                return this.errorContent("name is required when creating an image.");
            }
            if (!input.image) {
                return this.errorContent("Provide an image payload for create operations.");
            }
        }
        if ((input.operation === "read" || input.operation === "delete") && !input.id) {
            return this.errorContent("id is required for read and delete operations.");
        }
        switch (input.operation) {
            case "create":
                return this.handleCreate(input);
            case "read":
                return this.handleRead(input);
            case "update":
                if (!input.id) {
                    return this.errorContent("id is required for update operations.");
                }
                return this.handleUpdate(input);
            case "delete":
                return this.handleDelete(input);
            case "list":
                return this.handleList(input);
            default:
                return this.errorContent(`Unsupported image operation: ${input.operation ?? "unknown"}`);
        }
    }
    handleCreate(input) {
        return this.runRequest(async () => {
            const formData = new FormData();
            formData.append("name", input.name);
            const prepared = prepareImagePayload(input.image, input.name);
            formData.append("image", prepared.blob, prepared.fileName);
            const response = await this.postRequest("/api/image-gallery", formData);
            this.invalidateListCache();
            return this.buildResponse("create", response ?? null);
        });
    }
    handleRead(input) {
        return this.runRequest(async () => {
            const response = await this.getRequest(`/api/image-gallery/${input.id}`);
            return this.buildResponse("read", response ?? null);
        });
    }
    handleUpdate(input) {
        if (!input.new_name && !input.new_image) {
            return this.errorContent("Provide either new_name, new_image, or both for the update operation.");
        }
        return this.runRequest(async () => {
            const formData = new FormData();
            if (input.new_name) {
                formData.append("name", input.new_name);
            }
            if (input.new_image) {
                const prepared = prepareImagePayload(input.new_image, input.new_name ?? `image-${input.id}`);
                formData.append("image", prepared.blob, prepared.fileName);
            }
            const response = await this.putRequest(`/api/image-gallery/${input.id}`, formData);
            this.invalidateListCache();
            return this.buildResponse("update", response ?? null);
        });
    }
    handleDelete(input) {
        return this.runRequest(async () => {
            await this.deleteRequest(`/api/image-gallery/${input.id}`);
            this.invalidateListCache();
            return this.buildResponse("delete", null);
        });
    }
    handleList(input) {
        const offset = input.offset ?? 0;
        const count = input.count ?? 20;
        const cacheKey = this.buildListCacheKey({ offset, count, sort: input.sort, filters: input.filters });
        const cached = this.getCachedList(cacheKey);
        if (cached) {
            const metadata = { ...(cached.metadata ?? {}), cached: true };
            return this.successContent(this.buildResponse("list", cached.data, metadata));
        }
        return this.runRequest(async () => {
            const query = {
                offset,
                count,
            };
            if (input.sort) {
                query.sort = input.sort;
            }
            if (input.filters) {
                for (const { key, value } of input.filters) {
                    query[`filter[${key}]`] = value;
                }
            }
            const response = await this.getRequest("/api/image-gallery", { query });
            const { data, metadata } = normalizeImageListResponse(response, { offset, count });
            this.setCachedList(cacheKey, data, metadata);
            return this.buildResponse("list", data, metadata);
        });
    }
    buildResponse(operation, data, metadata) {
        const response = {
            operation,
            success: true,
            data,
        };
        if (metadata) {
            response.metadata = metadata;
        }
        return response;
    }
    buildListCacheKey(args) {
        const filterEntries = args.filters
            ? [...args.filters].sort((a, b) => a.key.localeCompare(b.key)).map(({ key, value }) => [key, value])
            : [];
        return JSON.stringify({
            offset: args.offset,
            count: args.count,
            sort: args.sort ?? null,
            filter: filterEntries,
        });
    }
    getCachedList(cacheKey) {
        const cached = BookstackManageImagesTool.listCache.get(cacheKey);
        if (!cached) {
            return undefined;
        }
        if (Date.now() - cached.timestamp > LIST_CACHE_TTL_MS) {
            BookstackManageImagesTool.listCache.delete(cacheKey);
            return undefined;
        }
        return cached;
    }
    setCachedList(cacheKey, data, metadata) {
        const entry = {
            timestamp: Date.now(),
            data,
            metadata,
        };
        BookstackManageImagesTool.listCache.set(cacheKey, entry);
    }
    invalidateListCache() {
        BookstackManageImagesTool.listCache.clear();
    }
}
BookstackManageImagesTool.listCache = new Map();
export default BookstackManageImagesTool;

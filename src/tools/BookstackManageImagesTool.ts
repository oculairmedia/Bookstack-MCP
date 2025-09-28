import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
import {
  imageInputSchema,
  prepareImagePayload,
  type ImageInput,
} from "../bookstack/ImageUtils.js";
import {
  normalizeImageListResponse,
  type ImageMetadata,
} from "./utils/imageResponses.js";

const LIST_CACHE_TTL_MS = 30_000;

const filtersSchema = z
  .array(
    z.object({
      key: z
        .string()
        .min(1)
        .describe("Filter key forwarded to BookStack as filter[<key>]") ,
      value: z
        .string()
        .describe("Filter value forwarded to BookStack"),
    }).describe("Filter entry"),
  )
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

type ImageManagementInput = z.infer<typeof schema>;
type CreateInput = ImageManagementInput & { operation: "create"; name: string; image: ImageInput };
type ReadInput = ImageManagementInput & { operation: "read"; id: number };
type UpdateInput = ImageManagementInput & { operation: "update"; id: number; new_name?: string; new_image?: ImageInput };
type DeleteInput = ImageManagementInput & { operation: "delete"; id: number };
type ListInput = ImageManagementInput & { operation: "list"; filters?: Array<{ key: string; value: string }> };

interface CacheEntry {
  timestamp: number;
  data: JsonValue;
  metadata?: ImageMetadata;
}

type StandardResponse = Record<string, JsonValue> & {
  operation: ImageManagementInput["operation"];
  success: boolean;
  data: JsonValue;
  metadata?: ImageMetadata;
};

class BookstackManageImagesTool extends BookstackTool<ImageManagementInput> {
  name = "bookstack_manage_images";
  description = "Unified CRUD interface for BookStack image gallery";
  schema = schema;

  private static readonly listCache = new Map<string, CacheEntry>();

  async execute(input: ImageManagementInput) {
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
        return this.handleCreate(input as CreateInput);
      case "read":
        return this.handleRead(input as ReadInput);
      case "update":
        if (!input.id) {
          return this.errorContent("id is required for update operations.");
        }
        return this.handleUpdate(input as UpdateInput);
      case "delete":
        return this.handleDelete(input as DeleteInput);
      case "list":
        return this.handleList(input as ListInput);
      default:
        return this.errorContent(`Unsupported image operation: ${(input as { operation?: string }).operation ?? "unknown"}`);
    }
  }

  private handleCreate(input: CreateInput) {
    return this.runRequest(async () => {
      const formData = new FormData();
      formData.append("name", input.name);

      const prepared = prepareImagePayload(input.image, input.name);
      formData.append("image", prepared.blob, prepared.fileName);

      const response = await this.postRequest<JsonValue>("/api/image-gallery", formData);
      this.invalidateListCache();
      return this.buildResponse("create", response ?? null);
    });
  }

  private handleRead(input: ReadInput) {
    return this.runRequest(async () => {
      const response = await this.getRequest<JsonValue>(`/api/image-gallery/${input.id}`);
      return this.buildResponse("read", response ?? null);
    });
  }

  private handleUpdate(input: UpdateInput) {
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

      const response = await this.putRequest<JsonValue>(`/api/image-gallery/${input.id}`, formData);
      this.invalidateListCache();
      return this.buildResponse("update", response ?? null);
    });
  }

  private handleDelete(input: DeleteInput) {
    return this.runRequest(async () => {
      await this.deleteRequest(`/api/image-gallery/${input.id}`);
      this.invalidateListCache();
      return this.buildResponse("delete", null);
    });
  }

  private handleList(input: ListInput) {
    const offset = input.offset ?? 0;
    const count = input.count ?? 20;
    const cacheKey = this.buildListCacheKey({ offset, count, sort: input.sort, filters: input.filters });

    const cached = this.getCachedList(cacheKey);
    if (cached) {
      const metadata = { ...(cached.metadata ?? {}), cached: true } as ImageMetadata;
      return this.successContent(this.buildResponse("list", cached.data, metadata));
    }

    return this.runRequest(async () => {
      const query: Record<string, string | number> = {
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

      const response = await this.getRequest<JsonValue>("/api/image-gallery", { query });
      const { data, metadata } = normalizeImageListResponse(response, { offset, count });

      this.setCachedList(cacheKey, data, metadata);
      return this.buildResponse("list", data, metadata);
    });
  }

  private buildResponse(
    operation: ImageManagementInput["operation"],
    data: JsonValue,
    metadata?: ImageMetadata,
  ): StandardResponse {
    const response: StandardResponse = {
      operation,
      success: true,
      data,
    };

    if (metadata) {
      response.metadata = metadata;
    }

    return response;
  }

  private buildListCacheKey(args: { offset: number; count: number; sort?: string; filters?: Array<{ key: string; value: string }> | undefined }): string {
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

  private getCachedList(cacheKey: string): CacheEntry | undefined {
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

  private setCachedList(cacheKey: string, data: JsonValue, metadata?: ImageMetadata) {
    const entry: CacheEntry = {
      timestamp: Date.now(),
      data,
      metadata,
    };

    BookstackManageImagesTool.listCache.set(cacheKey, entry);
  }

  private invalidateListCache() {
    BookstackManageImagesTool.listCache.clear();
  }
}

export default BookstackManageImagesTool;

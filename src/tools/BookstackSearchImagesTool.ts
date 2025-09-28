import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { normalizeImageListResponse, type ImageMetadata } from "./utils/imageResponses.js";

const isoDateString = z.string().refine(
  (value) => !Number.isNaN(Date.parse(value)),
  { message: "Expected an ISO-8601 date string" },
);

const schema = z.object({
  query: z.string().min(1).optional().describe("Text search across image names and descriptions"),
  extension: z
    .string()
    .min(1)
    .optional()
    .describe("File extension filter (e.g. .jpg, .png)"),
  size_min: z.number().int().min(0).optional().describe("Minimum size in bytes"),
  size_max: z.number().int().min(0).optional().describe("Maximum size in bytes"),
  created_after: isoDateString.optional().describe("Only return images created after this timestamp"),
  created_before: isoDateString.optional().describe("Only return images created before this timestamp"),
  used_in: z.enum(["books", "pages", "chapters"]).optional().describe("Filter by entity usage"),
  count: z.number().int().min(1).max(100).optional().describe("Results per page (default 20)"),
  offset: z.number().int().min(0).optional().describe("Pagination offset (default 0)"),
  sort: z.string().optional().describe("Sort expression supported by BookStack (e.g. '-created_at')"),
});

type SearchImagesInput = z.infer<typeof schema>;

type StandardResponse = Record<string, JsonValue> & {
  operation: "search";
  success: boolean;
  data: JsonValue;
  metadata?: ImageMetadata;
};

class BookstackSearchImagesTool extends BookstackTool<SearchImagesInput> {
  name = "bookstack_search_images";
  description = "Advanced discovery tool for BookStack image gallery";
  schema = schema;

  async execute(input: SearchImagesInput) {
    if (input.size_min !== undefined && input.size_max !== undefined && input.size_min > input.size_max) {
      return this.errorContent("size_min cannot be greater than size_max");
    }

    if (input.created_after && input.created_before) {
      const after = Date.parse(input.created_after);
      const before = Date.parse(input.created_before);
      if (after > before) {
        return this.errorContent("created_after must be earlier than created_before");
      }
    }

    return this.runRequest(async () => {
      const count = input.count ?? 20;
      const offset = input.offset ?? 0;
      const queryParams: Record<string, string | number> = {
        offset,
        count,
      };

      if (input.query) {
        queryParams.query = input.query;
      }

      if (input.extension) {
        queryParams.extension = input.extension.startsWith(".") ? input.extension : `.${input.extension}`;
      }

      if (input.size_min !== undefined) {
        queryParams.size_min = input.size_min;
      }

      if (input.size_max !== undefined) {
        queryParams.size_max = input.size_max;
      }

      if (input.created_after) {
        queryParams.created_after = input.created_after;
      }

      if (input.created_before) {
        queryParams.created_before = input.created_before;
      }

      if (input.used_in) {
        queryParams.used_in = input.used_in;
      }

      if (input.sort) {
        queryParams.sort = input.sort;
      }

      const response = await this.getRequest<JsonValue>("/api/image-gallery", { query: queryParams });
      const { data, metadata } = normalizeImageListResponse(response, { offset, count });

      return this.buildResponse(data, metadata);
    });
  }

  private buildResponse(data: JsonValue, metadata?: ImageMetadata): StandardResponse {
    const payload: StandardResponse = {
      operation: "search",
      success: true,
      data,
    };

    if (metadata) {
      payload.metadata = metadata;
    }

    return payload;
  }
}

export default BookstackSearchImagesTool;

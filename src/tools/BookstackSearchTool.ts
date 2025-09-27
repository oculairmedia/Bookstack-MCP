import { z } from "zod";
import { BookstackTool, type JsonValue, type JsonObject } from "../bookstack/BookstackTool.js";

const schema = z
  .object({
    query: z.string().min(1).describe("Search query text"),
    page: z
      .number()
      .int()
      .min(1)
      .describe("Page number for pagination")
      .optional(),
    count: z
      .number()
      .int()
      .min(1)
      .max(100)
      .describe("Number of results per page (max 100)")
      .optional(),
  })
  .describe("Bookstack search input");

type BookstackSearchInput = z.infer<typeof schema>;

class BookstackSearchTool extends BookstackTool<BookstackSearchInput> {
  name = "bookstack_search";
  description = "Searches content across Bookstack with advanced query support";
  schema = schema;

  async execute(input: BookstackSearchInput) {
    const queryParams: Record<string, string | number> = {
      query: input.query,
    };

    if (input.page !== undefined) {
      queryParams.page = input.page;
    }

    if (input.count !== undefined) {
      queryParams.count = input.count;
    }

    const limit = input.count ?? 20;

    return this.runRequest(async () => {
      const data = await this.getRequest<{ data?: unknown; total?: unknown }>(
        "/api/search",
        { query: queryParams }
      );

      const items = Array.isArray(data?.data) ? (data.data as JsonValue[]) : [];

      const results = items
        .map(item => this.createSearchResult(item))
        .filter((value): value is NonNullable<typeof value> => Boolean(value))
        .slice(0, limit);

      const payload: JsonValue = {
        query: input.query,
        total: typeof data?.total === "number" ? data.total : results.length,
        returned: results.length,
        results,
      };

      return payload;
    });
  }

  private createSearchResult(item: JsonValue): JsonValue | undefined {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      return undefined;
    }

    const typed = item as Record<string, JsonValue>;
    const title = this.asString(typed.name) ?? this.asString(typed.slug) ?? "Untitled";
    const summary = this.extractSummary(typed);

    const result: JsonObject = {
      id: typed.id ?? null,
      type: this.asString(typed.type) ?? "unknown",
      title,
      url: this.asString(typed.url) ?? null,
      summary,
    };

    if (typed.book && typeof typed.book === "object" && !Array.isArray(typed.book)) {
      const book = typed.book as Record<string, JsonValue>;
      result.book = {
        id: book.id ?? null,
        name: this.asString(book.name) ?? null,
      } as JsonValue;
    }

    if (typed.chapter && typeof typed.chapter === "object" && !Array.isArray(typed.chapter)) {
      const chapter = typed.chapter as Record<string, JsonValue>;
      result.chapter = {
        id: chapter.id ?? null,
        name: this.asString(chapter.name) ?? null,
      } as JsonValue;
    }

    return result;
  }

  private extractSummary(item: Record<string, JsonValue>): string {
    const preview = item.preview_html;
    if (preview && typeof preview === "object" && !Array.isArray(preview)) {
      const content = this.asString((preview as Record<string, JsonValue>).content);
      if (content) {
        return this.trimSummary(content);
      }
    }

    const description = this.asString(item.description);
    if (description) {
      return this.trimSummary(description);
    }

    return "No summary available";
  }

  private trimSummary(raw: string): string {
    const withoutTags = raw.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
    return withoutTags.length > 280 ? `${withoutTags.slice(0, 277)}...` : withoutTags;
  }

  private asString(value: JsonValue | undefined): string | undefined {
    if (typeof value === "string") {
      return value;
    }

    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }

    return undefined;
  }
}

export default BookstackSearchTool;

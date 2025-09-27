import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { tagArraySchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    name: z.string().min(1).describe("Page title"),
    book_id: z
      .number()
      .int()
      .positive()
      .describe("Book ID to attach the page to")
      .optional(),
    chapter_id: z
      .number()
      .int()
      .positive()
      .describe("Chapter ID to attach the page to")
      .optional(),
    markdown: z.string().describe("Page content in Markdown format").optional(),
    html: z.string().describe("Page content in HTML format").optional(),
    tags: tagArraySchema.describe("Tags to assign to the page").optional(),
    priority: z
      .number()
      .int()
      .min(0)
      .describe("Page priority")
      .optional(),
  })
  .describe("Create Page input");

type CreatePageInput = z.infer<typeof schema>;

class BookstackCreatePageTool extends BookstackTool<CreatePageInput> {
  name = "bookstack_create_page";
  description = "Creates a new page in Bookstack";
  schema = schema;

  async execute(input: CreatePageInput) {
    if (input.book_id === undefined && input.chapter_id === undefined) {
      return this.errorContent("Either book_id or chapter_id must be provided");
    }

    if (input.markdown && input.html) {
      return this.errorContent("Provide either markdown or html content, not both");
    }

    const payload: Record<string, unknown> = {
      name: input.name,
    };

    if (input.book_id !== undefined) {
      payload.book_id = input.book_id;
    }

    if (input.chapter_id !== undefined) {
      payload.chapter_id = input.chapter_id;
    }

    if (input.markdown) {
      payload.markdown = input.markdown;
    }

    if (input.html) {
      payload.html = input.html;
    }

    const formattedTags = this.formatTags(input.tags);
    if (formattedTags) {
      payload.tags = formattedTags;
    }

    if (input.priority !== undefined) {
      payload.priority = input.priority;
    }

    return this.runRequest(() =>
      this.postRequest<JsonValue>("/api/pages", payload)
    );
  }

}

export default BookstackCreatePageTool;

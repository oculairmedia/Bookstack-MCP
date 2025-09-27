import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { tagArraySchema, createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the page to update"),
    book_id: createIdSchema("Book ID to move the page to").optional(),
    chapter_id: createIdSchema("Chapter ID to move the page to").optional(),
    name: z.string().min(1).describe("New page name").optional(),
    markdown: z.string().describe("New Markdown content").optional(),
    html: z.string().describe("New HTML content").optional(),
    tags: tagArraySchema.describe("Updated tags").optional(),
    priority: z
      .number()
      .int()
      .min(0)
      .describe("Page priority")
      .optional(),
  })
  .describe("Update Page input");

type UpdatePageInput = z.infer<typeof schema>;

class BookstackUpdatePageTool extends BookstackTool<UpdatePageInput> {
  name = "bookstack_update_page";
  description = "Updates an existing Bookstack page";
  schema = schema;

  async execute(input: UpdatePageInput) {
    if (
      input.book_id === undefined &&
      input.chapter_id === undefined &&
      input.name === undefined &&
      input.markdown === undefined &&
      input.html === undefined &&
      input.tags === undefined &&
      input.priority === undefined
    ) {
      return this.errorContent("Provide at least one field to update");
    }

    if (input.markdown && input.html) {
      return this.errorContent("Provide either markdown or html content, not both");
    }

    const payload: Record<string, unknown> = {};

    if (input.book_id !== undefined) {
      payload.book_id = input.book_id;
    }

    if (input.chapter_id !== undefined) {
      payload.chapter_id = input.chapter_id;
    }

    if (input.name) {
      payload.name = input.name;
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
      this.putRequest<JsonValue>(`/api/pages/${input.id}`, payload)
    );
  }

}

export default BookstackUpdatePageTool;

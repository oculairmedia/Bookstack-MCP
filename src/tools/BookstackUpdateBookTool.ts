import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { tagArraySchema, createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the book to update"),
    name: z.string().min(1).describe("New book name").optional(),
    description: z.string().min(1).describe("New book description").optional(),
    tags: tagArraySchema.describe("Updated tags").optional(),
    imageId: z
      .number()
      .int()
      .positive()
      .describe("Image ID to use as cover")
      .optional(),
  })
  .describe("Update Book input");

type UpdateBookInput = z.infer<typeof schema>;

class BookstackUpdateBookTool extends BookstackTool<UpdateBookInput> {
  name = "bookstack_update_book";
  description = "Updates an existing Bookstack book";
  schema = schema;

  async execute(input: UpdateBookInput) {
    if (
      input.name === undefined &&
      input.description === undefined &&
      input.tags === undefined &&
      input.imageId === undefined
    ) {
      return this.errorContent("Provide at least one field to update");
    }

    const payload: Record<string, unknown> = {};

    if (input.name) {
      payload.name = input.name;
    }

    if (input.description) {
      payload.description = input.description;
    }

    const formattedTags = this.formatTags(input.tags);
    if (formattedTags) {
      payload.tags = formattedTags;
    }

    if (input.imageId !== undefined) {
      payload.image_id = input.imageId;
    }

    return this.runRequest(() =>
      this.putRequest<JsonValue>(`/api/books/${input.id}`, payload)
    );
  }

}

export default BookstackUpdateBookTool;

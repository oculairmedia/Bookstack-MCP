import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { tagArraySchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    name: z.string().min(1).describe("Book title"),
    description: z.string().min(1).describe("Book description"),
    tags: tagArraySchema.describe("Tags to assign to the book").optional(),
    imageId: z
      .number()
      .int()
      .positive()
      .describe("Image ID to use as cover")
      .optional(),
  })
  .describe("Create Book input");

type CreateBookInput = z.infer<typeof schema>;

class BookstackCreateBookTool extends BookstackTool<CreateBookInput> {
  name = "bookstack_create_book";
  description = "Creates a new book in Bookstack";
  schema = schema;

  async execute(input: CreateBookInput) {
    const payload: Record<string, unknown> = {
      name: input.name,
      description: input.description,
    };

    const formattedTags = this.formatTags(input.tags);
    if (formattedTags) {
      payload.tags = formattedTags;
    }

    if (input.imageId !== undefined) {
      payload.image_id = input.imageId;
    }

    return this.runRequest(() =>
      this.postRequest<JsonValue>("/api/books", payload)
    );
  }

}

export default BookstackCreateBookTool;

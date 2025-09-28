import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { tagArraySchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    name: z.string().min(1).describe("Bookshelf name"),
    description: z.string().min(1).describe("Bookshelf description").optional(),
    books: z
      .array(
        z
          .number()
          .int()
          .min(1)
          .describe("Book ID to include")
      )
      .describe("Book IDs to include in the shelf")
      .optional(),
    tags: tagArraySchema.describe("Tags to assign to the bookshelf").optional(),
  })
  .describe("Create Bookshelf input");

type CreateBookshelfInput = z.infer<typeof schema>;

class BookstackCreateBookshelfTool extends BookstackTool<CreateBookshelfInput> {
  name = "bookstack_create_bookshelf";
  description = "Creates a new bookshelf in Bookstack";
  schema = schema;

  async execute(input: CreateBookshelfInput) {
    const payload: Record<string, unknown> = {
      name: input.name,
    };

    if (input.description) {
      payload.description = input.description;
    }

    if (input.books) {
      payload.books = input.books;
    }

    const formattedTags = this.formatTags(input.tags);
    if (formattedTags) {
      payload.tags = formattedTags;
    }

    return this.runRequest(() =>
      this.postRequest<JsonValue>("/api/bookshelves", payload)
    );
  }

}

export default BookstackCreateBookshelfTool;

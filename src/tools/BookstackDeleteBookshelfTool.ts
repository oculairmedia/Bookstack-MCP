import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the bookshelf to delete"),
  })
  .describe("Delete Bookshelf input");

type DeleteBookshelfInput = z.infer<typeof schema>;

class BookstackDeleteBookshelfTool extends BookstackTool<DeleteBookshelfInput> {
  name = "bookstack_delete_bookshelf";
  description = "Deletes a bookshelf from Bookstack";
  schema = schema;

  async execute(input: DeleteBookshelfInput) {
    return this.runRequest(async () => {
      await this.deleteRequest(`/api/bookshelves/${input.id}`);
      return { success: true } as JsonValue;
    });
  }
}

export default BookstackDeleteBookshelfTool;


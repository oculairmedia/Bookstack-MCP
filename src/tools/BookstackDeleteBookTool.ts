import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the book to delete"),
  })
  .describe("Delete Book input");

type DeleteBookInput = z.infer<typeof schema>;

class BookstackDeleteBookTool extends BookstackTool<DeleteBookInput> {
  name = "bookstack_delete_book";
  description = "Deletes a book from Bookstack";
  schema = schema;

  async execute(input: DeleteBookInput) {
    return this.runRequest(async () => {
      await this.deleteRequest(`/api/books/${input.id}`);
      return { success: true } as JsonValue;
    });
  }
}

export default BookstackDeleteBookTool;


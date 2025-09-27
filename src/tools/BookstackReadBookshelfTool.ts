import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the bookshelf to retrieve"),
  })
  .describe("Read Bookshelf input");

type ReadBookshelfInput = z.infer<typeof schema>;

class BookstackReadBookshelfTool extends BookstackTool<ReadBookshelfInput> {
  name = "bookstack_read_bookshelf";
  description = "Retrieves details of a specific bookshelf in Bookstack";
  schema = schema;

  async execute(input: ReadBookshelfInput) {
    return this.runRequest(() =>
      this.getRequest<JsonValue>(`/api/bookshelves/${input.id}`)
    );
  }
}

export default BookstackReadBookshelfTool;


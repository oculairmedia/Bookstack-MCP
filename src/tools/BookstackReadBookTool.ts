import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the book to retrieve"),
  })
  .describe("Read Book input");

type ReadBookInput = z.infer<typeof schema>;

class BookstackReadBookTool extends BookstackTool<ReadBookInput> {
  name = "bookstack_read_book";
  description = "Retrieves details of a specific book in Bookstack";
  schema = schema;

  async execute(input: ReadBookInput) {
    return this.runRequest(() =>
      this.getRequest<JsonValue>(`/api/books/${input.id}`)
    );
  }
}

export default BookstackReadBookTool;


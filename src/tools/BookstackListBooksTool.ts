import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";

const schema = z
  .object({
    offset: z
      .number()
      .int()
      .min(0)
      .optional()
      .describe("Number of records to skip"),
    count: z
      .number()
      .int()
      .min(1)
      .max(100)
      .optional()
      .describe("Number of records to take"),
  })
  .describe("Parameters for listing books");

type ListBooksInput = z.infer<typeof schema>;

class BookstackListBooksTool extends BookstackTool<ListBooksInput> {
  name = "bookstack_list_books";
  description = "Lists books in Bookstack with pagination support";
  schema = schema;

  async execute(input: ListBooksInput) {
    const offset = input.offset ?? 0;
    const count = input.count ?? 100;

    return this.runRequest(() =>
      this.getRequest<JsonValue>("/api/books", { query: { offset, count } })
    );
  }
}

export default BookstackListBooksTool;

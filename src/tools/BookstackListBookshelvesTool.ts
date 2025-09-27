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
  .describe("Parameters for listing bookshelves");

type ListBookshelvesInput = z.infer<typeof schema>;

class BookstackListBookshelvesTool extends BookstackTool<ListBookshelvesInput> {
  name = "bookstack_list_bookshelves";
  description = "Lists bookshelves in Bookstack with pagination support";
  schema = schema;

  async execute(input: ListBookshelvesInput) {
    const offset = input.offset ?? 0;
    const count = input.count ?? 100;

    return this.runRequest(() =>
      this.getRequest<JsonValue>("/api/bookshelves", { query: { offset, count } })
    );
  }
}

export default BookstackListBookshelvesTool;

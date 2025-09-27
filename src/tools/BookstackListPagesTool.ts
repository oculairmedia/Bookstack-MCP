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
  .describe("Parameters for listing pages");

type ListPagesInput = z.infer<typeof schema>;

class BookstackListPagesTool extends BookstackTool<ListPagesInput> {
  name = "bookstack_list_pages";
  description = "Lists pages in Bookstack with pagination support";
  schema = schema;

  async execute(input: ListPagesInput) {
    const offset = input.offset ?? 0;
    const count = input.count ?? 100;

    return this.runRequest(() =>
      this.getRequest<JsonValue>("/api/pages", { query: { offset, count } })
    );
  }
}

export default BookstackListPagesTool;

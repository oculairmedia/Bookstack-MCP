import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the page to retrieve"),
  })
  .describe("Read Page input");

type ReadPageInput = z.infer<typeof schema>;

class BookstackReadPageTool extends BookstackTool<ReadPageInput> {
  name = "bookstack_read_page";
  description = "Retrieves details of a specific page in Bookstack";
  schema = schema;

  async execute(input: ReadPageInput) {
    return this.runRequest(() =>
      this.getRequest<JsonValue>(`/api/pages/${input.id}`)
    );
  }
}

export default BookstackReadPageTool;


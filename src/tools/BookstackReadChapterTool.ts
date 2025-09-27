import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the chapter to retrieve"),
  })
  .describe("Read Chapter input");

type ReadChapterInput = z.infer<typeof schema>;

class BookstackReadChapterTool extends BookstackTool<ReadChapterInput> {
  name = "bookstack_read_chapter";
  description = "Retrieves details of a specific chapter in Bookstack";
  schema = schema;

  async execute(input: ReadChapterInput) {
    return this.runRequest(() =>
      this.getRequest<JsonValue>(`/api/chapters/${input.id}`)
    );
  }
}

export default BookstackReadChapterTool;


import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the chapter to delete"),
  })
  .describe("Delete Chapter input");

type DeleteChapterInput = z.infer<typeof schema>;

class BookstackDeleteChapterTool extends BookstackTool<DeleteChapterInput> {
  name = "bookstack_delete_chapter";
  description = "Deletes a chapter from Bookstack";
  schema = schema;

  async execute(input: DeleteChapterInput) {
    return this.runRequest(async () => {
      await this.deleteRequest(`/api/chapters/${input.id}`);
      return { success: true } as JsonValue;
    });
  }
}

export default BookstackDeleteChapterTool;


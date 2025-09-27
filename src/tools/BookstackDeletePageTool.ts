import { z } from "zod";
import { BookstackTool, type JsonValue } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";

const schema = z
  .object({
    id: createIdSchema("ID of the page to delete"),
  })
  .describe("Delete Page input");

type DeletePageInput = z.infer<typeof schema>;

class BookstackDeletePageTool extends BookstackTool<DeletePageInput> {
  name = "bookstack_delete_page";
  description = "Deletes a page from Bookstack";
  schema = schema;

  async execute(input: DeletePageInput) {
    return this.runRequest(async () => {
      await this.deleteRequest(`/api/pages/${input.id}`);
      return { success: true } as JsonValue;
    });
  }
}

export default BookstackDeletePageTool;


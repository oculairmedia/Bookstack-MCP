import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the chapter to delete"),
})
    .describe("Delete Chapter input");
class BookstackDeleteChapterTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_delete_chapter";
        this.description = "Deletes a chapter from Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(async () => {
            await this.deleteRequest(`/api/chapters/${input.id}`);
            return { success: true };
        });
    }
}
export default BookstackDeleteChapterTool;

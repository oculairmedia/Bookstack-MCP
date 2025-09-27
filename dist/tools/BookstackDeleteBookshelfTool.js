import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the bookshelf to delete"),
})
    .describe("Delete Bookshelf input");
class BookstackDeleteBookshelfTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_delete_bookshelf";
        this.description = "Deletes a bookshelf from Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(async () => {
            await this.deleteRequest(`/api/bookshelves/${input.id}`);
            return { success: true };
        });
    }
}
export default BookstackDeleteBookshelfTool;

import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the book to delete"),
})
    .describe("Delete Book input");
class BookstackDeleteBookTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_delete_book";
        this.description = "Deletes a book from Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(async () => {
            await this.deleteRequest(`/api/books/${input.id}`);
            return { success: true };
        });
    }
}
export default BookstackDeleteBookTool;

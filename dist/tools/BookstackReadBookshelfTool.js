import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the bookshelf to retrieve"),
})
    .describe("Read Bookshelf input");
class BookstackReadBookshelfTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_read_bookshelf";
        this.description = "Retrieves details of a specific bookshelf in Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(() => this.getRequest(`/api/bookshelves/${input.id}`));
    }
}
export default BookstackReadBookshelfTool;

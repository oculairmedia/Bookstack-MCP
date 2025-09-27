import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the book to retrieve"),
})
    .describe("Read Book input");
class BookstackReadBookTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_read_book";
        this.description = "Retrieves details of a specific book in Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(() => this.getRequest(`/api/books/${input.id}`));
    }
}
export default BookstackReadBookTool;

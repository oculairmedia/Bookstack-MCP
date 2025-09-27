import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
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
    .describe("Parameters for listing books");
class BookstackListBooksTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_list_books";
        this.description = "Lists books in Bookstack with pagination support";
        this.schema = schema;
    }
    async execute(input) {
        const offset = input.offset ?? 0;
        const count = input.count ?? 100;
        return this.runRequest(() => this.getRequest("/api/books", { query: { offset, count } }));
    }
}
export default BookstackListBooksTool;

import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { tagArraySchema, createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the bookshelf to update"),
    name: z.string().min(1).describe("New bookshelf name").optional(),
    description: z.string().min(1).describe("New bookshelf description").optional(),
    books: z
        .array(z
        .number()
        .int()
        .positive()
        .describe("Book ID to include"))
        .describe("Updated list of book IDs")
        .optional(),
    tags: tagArraySchema.describe("Updated tags").optional(),
})
    .describe("Update Bookshelf input");
class BookstackUpdateBookshelfTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_update_bookshelf";
        this.description = "Updates an existing Bookstack bookshelf";
        this.schema = schema;
    }
    async execute(input) {
        if (input.name === undefined &&
            input.description === undefined &&
            input.books === undefined &&
            input.tags === undefined) {
            return this.errorContent("Provide at least one field to update");
        }
        const payload = {};
        if (input.name) {
            payload.name = input.name;
        }
        if (input.description) {
            payload.description = input.description;
        }
        if (input.books) {
            payload.books = input.books;
        }
        const formattedTags = this.formatTags(input.tags);
        if (formattedTags) {
            payload.tags = formattedTags;
        }
        return this.runRequest(() => this.putRequest(`/api/bookshelves/${input.id}`, payload));
    }
}
export default BookstackUpdateBookshelfTool;

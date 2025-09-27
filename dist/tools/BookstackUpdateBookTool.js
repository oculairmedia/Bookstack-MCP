import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { tagArraySchema, createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the book to update"),
    name: z.string().min(1).describe("New book name").optional(),
    description: z.string().min(1).describe("New book description").optional(),
    tags: tagArraySchema.describe("Updated tags").optional(),
    imageId: z
        .number()
        .int()
        .positive()
        .describe("Image ID to use as cover")
        .optional(),
})
    .describe("Update Book input");
class BookstackUpdateBookTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_update_book";
        this.description = "Updates an existing Bookstack book";
        this.schema = schema;
    }
    async execute(input) {
        if (input.name === undefined &&
            input.description === undefined &&
            input.tags === undefined &&
            input.imageId === undefined) {
            return this.errorContent("Provide at least one field to update");
        }
        const payload = {};
        if (input.name) {
            payload.name = input.name;
        }
        if (input.description) {
            payload.description = input.description;
        }
        const formattedTags = this.formatTags(input.tags);
        if (formattedTags) {
            payload.tags = formattedTags;
        }
        if (input.imageId !== undefined) {
            payload.image_id = input.imageId;
        }
        return this.runRequest(() => this.putRequest(`/api/books/${input.id}`, payload));
    }
}
export default BookstackUpdateBookTool;

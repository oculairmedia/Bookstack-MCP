import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { tagArraySchema, createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the chapter to update"),
    book_id: createIdSchema("Book ID to move the chapter to").optional(),
    name: z.string().min(1).describe("New chapter name").optional(),
    description: z.string().min(1).describe("New chapter description").optional(),
    tags: tagArraySchema.describe("Updated tags").optional(),
    priority: z
        .number()
        .int()
        .min(0)
        .describe("Chapter priority")
        .optional(),
})
    .describe("Update Chapter input");
class BookstackUpdateChapterTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_update_chapter";
        this.description = "Updates an existing Bookstack chapter";
        this.schema = schema;
    }
    async execute(input) {
        if (input.book_id === undefined &&
            input.name === undefined &&
            input.description === undefined &&
            input.tags === undefined &&
            input.priority === undefined) {
            return this.errorContent("Provide at least one field to update");
        }
        const payload = {};
        if (input.book_id !== undefined) {
            payload.book_id = input.book_id;
        }
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
        if (input.priority !== undefined) {
            payload.priority = input.priority;
        }
        return this.runRequest(() => this.putRequest(`/api/chapters/${input.id}`, payload));
    }
}
export default BookstackUpdateChapterTool;

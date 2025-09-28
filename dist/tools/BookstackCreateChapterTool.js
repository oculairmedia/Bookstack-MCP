import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { tagArraySchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    book_id: z
        .number()
        .int()
        .min(1)
        .describe("ID of the book to attach the chapter to"),
    name: z.string().min(1).describe("Chapter name"),
    description: z.string().min(1).describe("Chapter description").optional(),
    tags: tagArraySchema.describe("Tags for the chapter").optional(),
    priority: z
        .number()
        .int()
        .min(0)
        .describe("Chapter priority")
        .optional(),
})
    .describe("Create Chapter input");
class BookstackCreateChapterTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_create_chapter";
        this.description = "Creates a new chapter in Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        const payload = {
            book_id: input.book_id,
            name: input.name,
        };
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
        return this.runRequest(() => this.postRequest("/api/chapters", payload));
    }
}
export default BookstackCreateChapterTool;

import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { tagArraySchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    name: z.string().min(1).describe("Book title"),
    description: z.string().min(1).describe("Book description"),
    tags: tagArraySchema.describe("Tags to assign to the book").optional(),
    imageId: z
        .number()
        .int()
        .min(1)
        .describe("Image ID to use as cover")
        .optional(),
})
    .describe("Create Book input");
class BookstackCreateBookTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_create_book";
        this.description = "Creates a new book in Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        const payload = {
            name: input.name,
            description: input.description,
        };
        const formattedTags = this.formatTags(input.tags);
        if (formattedTags) {
            payload.tags = formattedTags;
        }
        if (input.imageId !== undefined) {
            payload.image_id = input.imageId;
        }
        return this.runRequest(() => this.postRequest("/api/books", payload));
    }
}
export default BookstackCreateBookTool;

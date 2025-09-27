import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the chapter to retrieve"),
})
    .describe("Read Chapter input");
class BookstackReadChapterTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_read_chapter";
        this.description = "Retrieves details of a specific chapter in Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(() => this.getRequest(`/api/chapters/${input.id}`));
    }
}
export default BookstackReadChapterTool;

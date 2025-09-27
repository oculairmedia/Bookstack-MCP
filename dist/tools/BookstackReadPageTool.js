import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the page to retrieve"),
})
    .describe("Read Page input");
class BookstackReadPageTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_read_page";
        this.description = "Retrieves details of a specific page in Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(() => this.getRequest(`/api/pages/${input.id}`));
    }
}
export default BookstackReadPageTool;

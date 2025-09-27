import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
import { createIdSchema } from "../bookstack/BookstackSchemas.js";
const schema = z
    .object({
    id: createIdSchema("ID of the page to delete"),
})
    .describe("Delete Page input");
class BookstackDeletePageTool extends BookstackTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_delete_page";
        this.description = "Deletes a page from Bookstack";
        this.schema = schema;
    }
    async execute(input) {
        return this.runRequest(async () => {
            await this.deleteRequest(`/api/pages/${input.id}`);
            return { success: true };
        });
    }
}
export default BookstackDeletePageTool;

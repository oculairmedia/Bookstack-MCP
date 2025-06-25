import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
class BookstackDeleteBookTool extends MCPTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_delete_book";
        this.description = "Deletes a book from Bookstack";
        this.toolBase = new BookstackToolBase();
        this.schema = {
            id: {
                type: z.string(),
                description: "The ID of the book to delete",
            },
        };
    }
    async execute(input) {
        try {
            console.log(`Executing bookstack_delete_book with input: ${JSON.stringify(input)}`);
            // Convert string input to number
            const id = parseInt(input.id, 10);
            // Validate converted number
            if (isNaN(id) || id <= 0) {
                return `Error: Invalid id value. Must be a positive number.`;
            }
            const result = await this.toolBase.executePythonScript("delete_book", {
                id: id
            });
            // Return the result as a string
            return result;
        }
        catch (error) {
            console.error("Error executing bookstack_delete_book:", error);
            return `Error: ${error.message || 'Unknown error'}`;
        }
    }
}
export default BookstackDeleteBookTool;

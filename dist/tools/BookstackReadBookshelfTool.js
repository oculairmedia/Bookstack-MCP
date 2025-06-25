import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
class BookstackReadBookshelfTool extends MCPTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_read_bookshelf";
        this.description = "Retrieves details of a specific bookshelf in Bookstack";
        this.toolBase = new BookstackToolBase();
        this.schema = {
            id: {
                type: z.string(),
                description: "The ID of the bookshelf to retrieve",
            },
        };
    }
    async execute(input) {
        try {
            console.log(`Executing bookstack_read_bookshelf with input: ${JSON.stringify(input)}`);
            // Convert string input to number
            const id = parseInt(input.id, 10);
            // Validate converted number
            if (isNaN(id) || id <= 0) {
                return `Error: Invalid id value. Must be a positive number.`;
            }
            const result = await this.toolBase.executePythonScript("read_bookshelf", {
                id: id
            });
            // Return the result as a string
            return result;
        }
        catch (error) {
            console.error("Error executing bookstack_read_bookshelf:", error);
            return `Error: ${error.message || 'Unknown error'}`;
        }
    }
}
export default BookstackReadBookshelfTool;

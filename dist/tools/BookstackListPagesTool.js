import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
class BookstackListPagesTool extends MCPTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_list_pages";
        this.description = "Lists all pages in Bookstack with pagination support";
        this.toolBase = new BookstackToolBase();
        this.schema = {
            offset: {
                type: z.string().optional(),
                description: "Number of records to skip",
            },
            count: {
                type: z.string().optional(),
                description: "Number of records to take",
            },
        };
    }
    async execute(input) {
        try {
            console.log(`Executing bookstack_list_pages with input: ${JSON.stringify(input)}`);
            // Convert string inputs to numbers
            const offset = input.offset ? parseInt(input.offset, 10) : 0;
            const count = input.count ? parseInt(input.count, 10) : 100;
            // Validate converted numbers
            if (isNaN(offset) || offset < 0) {
                return `Error: Invalid offset value. Must be a non-negative number.`;
            }
            if (isNaN(count) || count <= 0) {
                return `Error: Invalid count value. Must be a positive number.`;
            }
            const result = await this.toolBase.executePythonScript("list_pages", {
                offset: offset,
                count: count
            });
            // Return the result as a string
            return result;
        }
        catch (error) {
            console.error("Error executing bookstack_list_pages:", error);
            return `Error: ${error.message || 'Unknown error'}`;
        }
    }
}
export default BookstackListPagesTool;

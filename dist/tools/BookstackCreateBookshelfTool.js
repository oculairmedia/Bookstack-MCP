import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
class BookstackCreateBookshelfTool extends MCPTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_create_bookshelf";
        this.description = "Creates a new bookshelf in Bookstack";
        this.toolBase = new BookstackToolBase();
        this.schema = {
            name: {
                type: z.string(),
                description: "The name of the bookshelf",
            },
            description: {
                type: z.string().optional(),
                description: "A description of the bookshelf",
            },
            books: {
                type: z.array(z.string()).optional(),
                description: "A list of book IDs to include in the shelf",
            },
            tags: {
                type: z.array(z.object({
                    name: z.string(),
                    value: z.string(),
                })).optional(),
                description: "A list of tag objects (each with 'name' and 'value')",
            },
        };
    }
    async execute(input) {
        try {
            console.log(`Executing bookstack_create_bookshelf with input: ${JSON.stringify(input)}`);
            // Convert string book IDs to numbers if provided
            let bookIds;
            if (input.books && input.books.length > 0) {
                bookIds = input.books.map(id => {
                    const numId = parseInt(id, 10);
                    if (isNaN(numId)) {
                        throw new Error(`Invalid book ID: ${id}. Must be a number.`);
                    }
                    return numId;
                });
            }
            const result = await this.toolBase.executePythonScript("create_bookshelf", {
                name: input.name,
                description: input.description,
                books: bookIds,
                tags: input.tags
            });
            // Return the result as a string
            return result;
        }
        catch (error) {
            console.error("Error executing bookstack_create_bookshelf:", error);
            return `Error: ${error.message || 'Unknown error'}`;
        }
    }
}
export default BookstackCreateBookshelfTool;

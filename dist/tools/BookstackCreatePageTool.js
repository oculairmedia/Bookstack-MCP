import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
class BookstackCreatePageTool extends MCPTool {
    constructor() {
        super(...arguments);
        this.name = "bookstack_create_page";
        this.description = "Creates a new page in Bookstack";
        this.toolBase = new BookstackToolBase();
        this.schema = {
            name: {
                type: z.string(),
                description: "The name of the page",
            },
            book_id: {
                type: z.string().optional(),
                description: "The ID of the book to create the page in",
            },
            chapter_id: {
                type: z.string().optional(),
                description: "The ID of the chapter to create the page in",
            },
            markdown: {
                type: z.string().optional(),
                description: "The page content in Markdown format",
            },
            html: {
                type: z.string().optional(),
                description: "The page content in HTML format",
            },
            tags: {
                type: z.array(z.object({
                    name: z.string(),
                    value: z.string(),
                })).optional(),
                description: "A list of tag objects (each with 'name' and 'value')",
            },
            priority: {
                type: z.string().optional(),
                description: "Page priority",
            },
        };
    }
    async execute(input) {
        try {
            console.log(`Executing bookstack_create_page with input: ${JSON.stringify(input)}`);
            // Convert string inputs to numbers
            const book_id = input.book_id ? parseInt(input.book_id, 10) : undefined;
            const chapter_id = input.chapter_id ? parseInt(input.chapter_id, 10) : undefined;
            const priority = input.priority ? parseInt(input.priority, 10) : undefined;
            // Validate converted numbers
            if (input.book_id && isNaN(book_id)) {
                return `Error: Invalid book_id value. Must be a number.`;
            }
            if (input.chapter_id && isNaN(chapter_id)) {
                return `Error: Invalid chapter_id value. Must be a number.`;
            }
            if (input.priority && isNaN(priority)) {
                return `Error: Invalid priority value. Must be a number.`;
            }
            const result = await this.toolBase.executePythonScript("create_page", {
                name: input.name,
                book_id: book_id,
                chapter_id: chapter_id,
                markdown: input.markdown,
                html: input.html,
                tags: input.tags,
                priority: priority
            });
            // Return the result as a string
            return result;
        }
        catch (error) {
            console.error("Error executing bookstack_create_page:", error);
            return `Error: ${error.message || 'Unknown error'}`;
        }
    }
}
export default BookstackCreatePageTool;

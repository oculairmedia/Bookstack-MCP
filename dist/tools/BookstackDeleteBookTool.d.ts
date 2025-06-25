import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface DeleteBookInput {
    id: string;
}
declare class BookstackDeleteBookTool extends MCPTool<DeleteBookInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: DeleteBookInput): Promise<string>;
}
export default BookstackDeleteBookTool;

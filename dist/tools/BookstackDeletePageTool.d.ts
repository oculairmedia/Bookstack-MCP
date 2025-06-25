import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface DeletePageInput {
    id: string;
}
declare class BookstackDeletePageTool extends MCPTool<DeletePageInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: DeletePageInput): Promise<string>;
}
export default BookstackDeletePageTool;

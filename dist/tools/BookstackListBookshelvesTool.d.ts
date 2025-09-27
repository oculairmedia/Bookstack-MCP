import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ListBookshelvesInput {
    offset?: string;
    count?: string;
}
declare class BookstackListBookshelvesTool extends MCPTool<ListBookshelvesInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        offset: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        count: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
    };
    execute(input: ListBookshelvesInput): Promise<string>;
}
export default BookstackListBookshelvesTool;

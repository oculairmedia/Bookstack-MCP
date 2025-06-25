import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface Tag {
    name: string;
    value: string;
}
interface UpdateBookshelfInput {
    id: string;
    name?: string;
    description?: string;
    books?: string[];
    tags?: Tag[];
}
declare class BookstackUpdateBookshelfTool extends MCPTool<UpdateBookshelfInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
        name: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        description: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        books: {
            type: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
            description: string;
        };
        tags: {
            type: z.ZodOptional<z.ZodArray<z.ZodObject<{
                name: z.ZodString;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                name: string;
            }, {
                value: string;
                name: string;
            }>, "many">>;
            description: string;
        };
    };
    execute(input: UpdateBookshelfInput): Promise<string>;
}
export default BookstackUpdateBookshelfTool;

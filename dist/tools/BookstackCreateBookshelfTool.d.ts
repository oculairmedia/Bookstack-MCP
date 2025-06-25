import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface Tag {
    name: string;
    value: string;
}
interface CreateBookshelfInput {
    name: string;
    description?: string;
    books?: string[];
    tags?: Tag[];
}
declare class BookstackCreateBookshelfTool extends MCPTool<CreateBookshelfInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        name: {
            type: z.ZodString;
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
    execute(input: CreateBookshelfInput): Promise<string>;
}
export default BookstackCreateBookshelfTool;

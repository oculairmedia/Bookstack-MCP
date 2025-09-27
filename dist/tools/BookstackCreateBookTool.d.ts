import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface Tag {
    name: string;
    value: string;
}
interface CreateBookInput {
    name: string;
    description: string;
    tags?: Tag[];
    image_id?: string;
}
declare class BookstackCreateBookTool extends MCPTool<CreateBookInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        name: {
            type: z.ZodString;
            description: string;
        };
        description: {
            type: z.ZodString;
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
        image_id: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
    };
    execute(input: CreateBookInput): Promise<string>;
}
export default BookstackCreateBookTool;

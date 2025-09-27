import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    name: z.ZodString;
    description: z.ZodString;
    tags: z.ZodOptional<z.ZodArray<z.ZodObject<{
        name: z.ZodString;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        name: string;
    }, {
        value: string;
        name: string;
    }>, "many">>;
    imageId: z.ZodOptional<z.ZodNumber>;
}, "strip", z.ZodTypeAny, {
    name: string;
    description: string;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    imageId?: number | undefined;
}, {
    name: string;
    description: string;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    imageId?: number | undefined;
}>;
type CreateBookInput = z.infer<typeof schema>;
declare class BookstackCreateBookTool extends BookstackTool<CreateBookInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        name: z.ZodString;
        description: z.ZodString;
        tags: z.ZodOptional<z.ZodArray<z.ZodObject<{
            name: z.ZodString;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            name: string;
        }, {
            value: string;
            name: string;
        }>, "many">>;
        imageId: z.ZodOptional<z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        name: string;
        description: string;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        imageId?: number | undefined;
    }, {
        name: string;
        description: string;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        imageId?: number | undefined;
    }>;
    execute(input: CreateBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreateBookTool;

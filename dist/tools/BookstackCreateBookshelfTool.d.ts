import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    name: z.ZodString;
    description: z.ZodOptional<z.ZodString>;
    books: z.ZodOptional<z.ZodArray<z.ZodNumber, "many">>;
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
}, "strip", z.ZodTypeAny, {
    name: string;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    books?: number[] | undefined;
}, {
    name: string;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    books?: number[] | undefined;
}>;
type CreateBookshelfInput = z.infer<typeof schema>;
declare class BookstackCreateBookshelfTool extends BookstackTool<CreateBookshelfInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        name: z.ZodString;
        description: z.ZodOptional<z.ZodString>;
        books: z.ZodOptional<z.ZodArray<z.ZodNumber, "many">>;
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
    }, "strip", z.ZodTypeAny, {
        name: string;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        books?: number[] | undefined;
    }, {
        name: string;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        books?: number[] | undefined;
    }>;
    execute(input: CreateBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreateBookshelfTool;

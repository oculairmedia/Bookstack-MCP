import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
    name: z.ZodOptional<z.ZodString>;
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
    id: number;
    name?: string | undefined;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    books?: number[] | undefined;
}, {
    id: number;
    name?: string | undefined;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    books?: number[] | undefined;
}>;
type UpdateBookshelfInput = z.infer<typeof schema>;
declare class BookstackUpdateBookshelfTool extends BookstackTool<UpdateBookshelfInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
        name: z.ZodOptional<z.ZodString>;
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
        id: number;
        name?: string | undefined;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        books?: number[] | undefined;
    }, {
        id: number;
        name?: string | undefined;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        books?: number[] | undefined;
    }>;
    execute(input: UpdateBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdateBookshelfTool;

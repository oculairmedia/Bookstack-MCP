import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
    name: z.ZodOptional<z.ZodString>;
    description: z.ZodOptional<z.ZodString>;
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
    id: number;
    name?: string | undefined;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    imageId?: number | undefined;
}, {
    id: number;
    name?: string | undefined;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    imageId?: number | undefined;
}>;
type UpdateBookInput = z.infer<typeof schema>;
declare class BookstackUpdateBookTool extends BookstackTool<UpdateBookInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
        name: z.ZodOptional<z.ZodString>;
        description: z.ZodOptional<z.ZodString>;
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
        id: number;
        name?: string | undefined;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        imageId?: number | undefined;
    }, {
        id: number;
        name?: string | undefined;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        imageId?: number | undefined;
    }>;
    execute(input: UpdateBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdateBookTool;

import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    id: number;
}, {
    id: number;
}>;
type ReadBookshelfInput = z.infer<typeof schema>;
declare class BookstackReadBookshelfTool extends BookstackTool<ReadBookshelfInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        id: number;
    }, {
        id: number;
    }>;
    execute(input: ReadBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackReadBookshelfTool;

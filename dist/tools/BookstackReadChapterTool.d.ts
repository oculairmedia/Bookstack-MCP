import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    id: number;
}, {
    id: number;
}>;
type ReadChapterInput = z.infer<typeof schema>;
declare class BookstackReadChapterTool extends BookstackTool<ReadChapterInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        id: number;
    }, {
        id: number;
    }>;
    execute(input: ReadChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackReadChapterTool;

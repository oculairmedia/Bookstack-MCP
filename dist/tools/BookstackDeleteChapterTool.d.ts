import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    id: number;
}, {
    id: number;
}>;
type DeleteChapterInput = z.infer<typeof schema>;
declare class BookstackDeleteChapterTool extends BookstackTool<DeleteChapterInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        id: number;
    }, {
        id: number;
    }>;
    execute(input: DeleteChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeleteChapterTool;

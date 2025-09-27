import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    id: number;
}, {
    id: number;
}>;
type DeletePageInput = z.infer<typeof schema>;
declare class BookstackDeletePageTool extends BookstackTool<DeletePageInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        id: number;
    }, {
        id: number;
    }>;
    execute(input: DeletePageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeletePageTool;

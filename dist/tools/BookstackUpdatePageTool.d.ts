import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type UpdatePageInput = z.infer<typeof schema>;
declare class BookstackUpdatePageTool extends BookstackTool<UpdatePageInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: UpdatePageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdatePageTool;

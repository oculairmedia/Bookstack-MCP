import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ReadPageInput = z.infer<typeof schema>;
declare class BookstackReadPageTool extends BookstackTool<ReadPageInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ReadPageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackReadPageTool;

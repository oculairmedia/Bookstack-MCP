import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ReadChapterInput = z.infer<typeof schema>;
declare class BookstackReadChapterTool extends BookstackTool<ReadChapterInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ReadChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackReadChapterTool;

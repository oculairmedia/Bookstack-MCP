import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ReadBookInput = z.infer<typeof schema>;
declare class BookstackReadBookTool extends BookstackTool<ReadBookInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ReadBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackReadBookTool;

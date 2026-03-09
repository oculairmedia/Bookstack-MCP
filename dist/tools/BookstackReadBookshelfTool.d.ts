import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ReadBookshelfInput = z.infer<typeof schema>;
declare class BookstackReadBookshelfTool extends BookstackTool<ReadBookshelfInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ReadBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackReadBookshelfTool;

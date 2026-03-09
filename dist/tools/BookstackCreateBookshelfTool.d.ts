import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type CreateBookshelfInput = z.infer<typeof schema>;
declare class BookstackCreateBookshelfTool extends BookstackTool<CreateBookshelfInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: CreateBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreateBookshelfTool;
